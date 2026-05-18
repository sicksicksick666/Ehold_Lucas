"""
VM-Info-Service
===============

Kleine FastAPI-Anwendung, die zwei Endpunkte ausliefert:

  GET /            -> menschenlesbare HTML-Übersichtsseite
  GET /api/info    -> JSON-Repräsentation derselben Daten

Die Daten werden bei jedem Request frisch ausgelesen, damit Memory- und
Disk-Auslastung tatsächlich aktuell sind.

Quellen für die System-Infos:
  - psutil               -> CPU, Memory, Disk, Network, Partitionen
  - platform / os.uname  -> Kernel, Architektur
  - /etc/os-release      -> Distribution
  - systemd-detect-virt  -> Hypervisor-Erkennung
  - /proc/mounts         -> Filesystems (Fallback)
"""
from __future__ import annotations

import os
import socket
import platform
import subprocess
import time
from datetime import datetime, timezone
from html import escape
from typing import Any

import psutil
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(
    title="VM Info Service",
    description="Zeigt technische Details der laufenden Exoscale-VM (Abgabe 2, VICA SS26).",
    version="1.0.0",
)


# --------------------------------------------------------------------------- #
#  Hilfsfunktionen                                                            #
# --------------------------------------------------------------------------- #
def _read_os_release() -> dict[str, str]:
    """Parsed /etc/os-release in ein dict. Format: KEY=VALUE pro Zeile."""
    info: dict[str, str] = {}
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as fh:
            for line in fh:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    info[key] = val.strip().strip('"')
    except FileNotFoundError:
        pass
    return info


def _detect_hypervisor() -> str:
    """systemd-detect-virt liefert z.B. 'kvm', 'xen', 'vmware', 'none'."""
    try:
        return subprocess.check_output(
            ["systemd-detect-virt"], text=True, timeout=2
        ).strip()
    except Exception:
        return "unknown"


def _public_ip() -> str | None:
    """Holt die Public-IP über api.ipify.org (Timeout 3 s, optional)."""
    try:
        return subprocess.check_output(
            ["curl", "-s", "-4", "--max-time", "3", "https://api.ipify.org"],
            text=True,
        ).strip() or None
    except Exception:
        return None


def _bytes_human(n: int) -> str:
    """Wandelt Bytes in lesbares Format um (1024-Basis)."""
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if abs(n) < 1024.0:
            return f"{n:3.1f} {unit}"
        n /= 1024.0
    return f"{n:3.1f} EiB"


# --------------------------------------------------------------------------- #
#  Kern-Datenmodell                                                           #
# --------------------------------------------------------------------------- #
def gather_vm_info() -> dict[str, Any]:
    """Sammelt einen kompletten Snapshot der VM-Eigenschaften."""
    uname = platform.uname()
    osr = _read_os_release()
    mem = psutil.virtual_memory()
    disk_root = psutil.disk_usage("/")
    cpu_freq = psutil.cpu_freq()

    # Filesystems / Mounts (nur "echte" - keine tmpfs/proc/sys ohne device)
    filesystems = []
    for p in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(p.mountpoint)
            filesystems.append({
                "device": p.device,
                "mountpoint": p.mountpoint,
                "fstype": p.fstype,
                "opts": p.opts,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent_used": usage.percent,
            })
        except PermissionError:
            # Manche Mountpoints sind für unprivilegierte Prozesse gesperrt.
            continue

    # Netzwerk-Interfaces (ohne loopback-Ballast)
    net_ifaces = {}
    for iface, addrs in psutil.net_if_addrs().items():
        net_ifaces[iface] = [
            {"family": a.family.name, "address": a.address, "netmask": a.netmask}
            for a in addrs
        ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hostname": socket.gethostname(),
        "fqdn": socket.getfqdn(),
        "public_ip": _public_ip(),
        "uptime_seconds": int(time.time() - psutil.boot_time()),
        "platform": {
            "system": uname.system,
            "node": uname.node,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
            "kernel": uname.release,
        },
        "distribution": {
            "id": osr.get("ID"),
            "name": osr.get("NAME"),
            "version": osr.get("VERSION"),
            "pretty_name": osr.get("PRETTY_NAME"),
        },
        "hypervisor": _detect_hypervisor(),
        "cpu": {
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "current_freq_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
            "load_avg_1_5_15": list(os.getloadavg()),
            "percent": psutil.cpu_percent(interval=0.2),
        },
        "memory": {
            "total_bytes": mem.total,
            "available_bytes": mem.available,
            "used_bytes": mem.used,
            "percent": mem.percent,
        },
        "disk_root": {
            "total_bytes": disk_root.total,
            "used_bytes": disk_root.used,
            "free_bytes": disk_root.free,
            "percent": disk_root.percent,
        },
        "filesystems": filesystems,
        "network_interfaces": net_ifaces,
    }


# --------------------------------------------------------------------------- #
#  /api/info - JSON                                                           #
# --------------------------------------------------------------------------- #
@app.get(
    "/api/info",
    summary="Technische Details der VM als JSON",
    response_class=JSONResponse,
)
def api_info() -> dict[str, Any]:
    return gather_vm_info()


# --------------------------------------------------------------------------- #
#  / - HTML Dashboard                                                         #
# --------------------------------------------------------------------------- #
HTML_TEMPLATE = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>VM Info - {hostname}</title>
  <style>
    :root {{
      --bg: #0d1117; --card: #161b22; --border: #30363d;
      --fg: #c9d1d9; --muted: #8b949e; --accent: #58a6ff;
      --good: #3fb950; --warn: #d29922; --bad: #f85149;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
      background: var(--bg); color: var(--fg); margin: 0; padding: 2rem;
      line-height: 1.5;
    }}
    h1 {{ margin: 0 0 0.5rem 0; font-size: 1.6rem; }}
    .sub {{ color: var(--muted); margin-bottom: 2rem; }}
    .grid {{
      display: grid; gap: 1rem;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    }}
    .card {{
      background: var(--card); border: 1px solid var(--border);
      border-radius: 8px; padding: 1.2rem;
    }}
    .card h2 {{
      margin: 0 0 0.7rem 0; font-size: 1.05rem;
      color: var(--accent); border-bottom: 1px solid var(--border);
      padding-bottom: 0.4rem;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th, td {{ padding: 0.25rem 0.3rem; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 500; width: 42%; }}
    td {{ font-family: ui-monospace, SFMono-Regular, monospace; word-break: break-all; }}
    .bar {{
      background: #21262d; height: 8px; border-radius: 4px; overflow: hidden;
      margin-top: 4px;
    }}
    .bar > div {{ height: 100%; background: var(--good); }}
    .bar.warn > div {{ background: var(--warn); }}
    .bar.bad  > div {{ background: var(--bad); }}
    footer {{
      margin-top: 2rem; color: var(--muted); font-size: 0.85rem;
      border-top: 1px solid var(--border); padding-top: 0.8rem;
    }}
    a {{ color: var(--accent); }}
    .pill {{
      display: inline-block; padding: 1px 8px; border-radius: 999px;
      background: #21262d; border: 1px solid var(--border); font-size: 0.8rem;
    }}
  </style>
</head>
<body>
  <h1>VM Info — <span class="pill">{hostname}</span></h1>
  <div class="sub">
    Generiert: {generated_at} &middot;
    <a href="/api/info">JSON-API</a>
  </div>

  <div class="grid">
    <div class="card">
      <h2>System</h2>
      <table>
        <tr><th>Distribution</th><td>{distro}</td></tr>
        <tr><th>Kernel</th><td>{kernel}</td></tr>
        <tr><th>Architektur</th><td>{arch}</td></tr>
        <tr><th>Hypervisor</th><td>{hypervisor}</td></tr>
        <tr><th>Uptime</th><td>{uptime}</td></tr>
        <tr><th>FQDN</th><td>{fqdn}</td></tr>
      </table>
    </div>

    <div class="card">
      <h2>CPU</h2>
      <table>
        <tr><th>Logische Kerne</th><td>{cpu_logical}</td></tr>
        <tr><th>Physische Kerne</th><td>{cpu_physical}</td></tr>
        <tr><th>Takt</th><td>{cpu_freq} MHz</td></tr>
        <tr><th>Auslastung</th>
            <td>{cpu_percent} %
              <div class="bar {cpu_class}"><div style="width:{cpu_percent}%"></div></div>
            </td></tr>
        <tr><th>Load (1/5/15 min)</th><td>{loadavg}</td></tr>
      </table>
    </div>

    <div class="card">
      <h2>Memory</h2>
      <table>
        <tr><th>Total</th><td>{mem_total}</td></tr>
        <tr><th>Used</th><td>{mem_used}</td></tr>
        <tr><th>Available</th><td>{mem_avail}</td></tr>
        <tr><th>Auslastung</th>
            <td>{mem_percent} %
              <div class="bar {mem_class}"><div style="width:{mem_percent}%"></div></div>
            </td></tr>
      </table>
    </div>

    <div class="card">
      <h2>Disk (/)</h2>
      <table>
        <tr><th>Total</th><td>{disk_total}</td></tr>
        <tr><th>Used</th><td>{disk_used}</td></tr>
        <tr><th>Free</th><td>{disk_free}</td></tr>
        <tr><th>Auslastung</th>
            <td>{disk_percent} %
              <div class="bar {disk_class}"><div style="width:{disk_percent}%"></div></div>
            </td></tr>
      </table>
    </div>

    <div class="card">
      <h2>Netzwerk</h2>
      <table>
        <tr><th>Hostname</th><td>{hostname}</td></tr>
        <tr><th>Public IP</th><td>{public_ip}</td></tr>
      </table>
      <p style="color:var(--muted);font-size:.85rem;margin:.6rem 0 .3rem 0;">Interfaces:</p>
      {iface_rows}
    </div>

    <div class="card">
      <h2>Filesystems</h2>
      <table>
        <tr><th>Device</th><th>Mount</th><th>Type</th><th>Used</th></tr>
        {fs_rows}
      </table>
    </div>
  </div>

  <footer>
    Lucas Ehold &middot; Abgabe 2 &middot; VICA SS26 &middot;
    Hochschule Burgenland &middot;
    Bereitgestellt von Caddy &amp; FastAPI auf Exoscale.
  </footer>
</body>
</html>
"""


def _percent_class(p: float) -> str:
    if p >= 90:
        return "bad"
    if p >= 70:
        return "warn"
    return ""


def _format_uptime(s: int) -> str:
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, _ = divmod(s, 60)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    parts.append(f"{m}m")
    return " ".join(parts)


@app.get("/", response_class=HTMLResponse, summary="HTML-Dashboard")
def index() -> HTMLResponse:
    info = gather_vm_info()

    # Interface-Tabelle
    iface_html_parts = []
    for iface, addrs in info["network_interfaces"].items():
        if iface == "lo":
            continue
        rows = "".join(
            f"<tr><th>{escape(iface)} ({escape(a['family'])})</th>"
            f"<td>{escape(a['address'] or '')}</td></tr>"
            for a in addrs
        )
        iface_html_parts.append(f"<table>{rows}</table>")
    iface_rows = "".join(iface_html_parts) or "<p>Keine Interfaces gefunden.</p>"

    # Filesystem-Tabelle
    fs_rows = "".join(
        "<tr>"
        f"<td>{escape(fs['device'])}</td>"
        f"<td>{escape(fs['mountpoint'])}</td>"
        f"<td>{escape(fs['fstype'])}</td>"
        f"<td>{_bytes_human(fs['used_bytes'])} / {_bytes_human(fs['total_bytes'])} "
        f"({fs['percent_used']:.1f} %)</td>"
        "</tr>"
        for fs in info["filesystems"]
    )

    html = HTML_TEMPLATE.format(
        hostname=escape(info["hostname"]),
        generated_at=escape(info["generated_at"]),
        distro=escape(info["distribution"].get("pretty_name") or "n/a"),
        kernel=escape(info["platform"]["kernel"]),
        arch=escape(info["platform"]["machine"]),
        hypervisor=escape(info["hypervisor"]),
        uptime=_format_uptime(info["uptime_seconds"]),
        fqdn=escape(info["fqdn"]),
        cpu_logical=info["cpu"]["logical_cores"],
        cpu_physical=info["cpu"]["physical_cores"] or "n/a",
        cpu_freq=info["cpu"]["current_freq_mhz"] or "n/a",
        cpu_percent=info["cpu"]["percent"],
        cpu_class=_percent_class(info["cpu"]["percent"]),
        loadavg=" / ".join(f"{x:.2f}" for x in info["cpu"]["load_avg_1_5_15"]),
        mem_total=_bytes_human(info["memory"]["total_bytes"]),
        mem_used=_bytes_human(info["memory"]["used_bytes"]),
        mem_avail=_bytes_human(info["memory"]["available_bytes"]),
        mem_percent=info["memory"]["percent"],
        mem_class=_percent_class(info["memory"]["percent"]),
        disk_total=_bytes_human(info["disk_root"]["total_bytes"]),
        disk_used=_bytes_human(info["disk_root"]["used_bytes"]),
        disk_free=_bytes_human(info["disk_root"]["free_bytes"]),
        disk_percent=info["disk_root"]["percent"],
        disk_class=_percent_class(info["disk_root"]["percent"]),
        public_ip=escape(info["public_ip"] or "n/a"),
        iface_rows=iface_rows,
        fs_rows=fs_rows,
    )
    return HTMLResponse(content=html)
