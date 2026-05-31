# Abgabe 2 – Automatisierte Bereitstellung einer VM-Info-Site auf Exoscale

> **Kurs:** VICA SS26 · Hochschule Burgenland · BITI
> **Autor:** Lucas Ehold
> **Stack:** Terraform · GitHub Actions · Exoscale (Compute + SOS Remote-State) · Cloud-Init · Caddy · FastAPI · DuckDNS

## 1. Zielzustand

Ein einziger Klick auf einen GitHub-Actions-Button erzeugt in Exoscale eine Ubuntu-VM, holt automatisch ein gültiges Let's-Encrypt-Zertifikat und liefert unter einer öffentlichen URL technische Informationen über sich selbst aus:

- **HTML-Dashboard:** <https://lucas-vica.duckdns.org/>  *(FQDN je nach DuckDNS-Subdomain)*
- **JSON-API:** <https://lucas-vica.duckdns.org/api/info>

Ein zweiter Workflow räumt die gesamte Infrastruktur sauber wieder ab.

## 2. Architektur

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  Entwickler-Rechner (lokaler Workspace)                                  │
│   ├── Terraform-Konfiguration                                            │
│   ├── Cloud-Init-Template                                                │
│   ├── FastAPI-App                                                        │
│   └── Caddyfile                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                │ git push / PR
                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  GitHub Repository  (sicksicksick666/Ehold_Lucas)                        │
│   ├── Ehold_Lucas/Abgabe_2_260518/...   <-- gesamter Code                │
│   └── .github/workflows/                                                 │
│         ├── infra-apply.yml   (workflow_dispatch -> terraform apply)     │
│         └── infra-destroy.yml (workflow_dispatch -> terraform destroy)   │
└──────────────────────────────────────────────────────────────────────────┘
                                │ Actions-Runner führt Terraform aus
                                ▼
┌─────────────────────────┐        ┌──────────────────────────────────────┐
│  DuckDNS                │◄───────┤  Exoscale-VM (Ubuntu 24.04 LTS)      │
│  lucas-vica.duckdns.org │        │   ├── duckdns-update.timer (alle 5m) │
│  -> wird auf VM-IP      │        │   ├── Caddy   (Ports 80/443,         │
│  aktualisiert           │        │   │   Auto-HTTPS via Let's Encrypt)  │
└─────────────────────────┘        │   └── FastAPI (127.0.0.1:8000)       │
                                   │       /        -> HTML-Dashboard     │
                                   │       /api/info-> JSON-API           │
                                   └──────────────────────────────────────┘
                                                ▲
                                                │ HTTPS
                                                │
                                          Internet-User
```

## 3. Verzeichnisstruktur

```text
Ehold_Lucas/Abgabe_2_260518/
├── README.md                       (diese Datei)
├── terraform/
│   ├── versions.tf                 Provider-Pinning
│   ├── variables.tf                Inputs
│   ├── main.tf                     SSH-Key, Security-Group, Instanz
│   ├── outputs.tf                  IPs, URLs, SSH-Command
│   └── cloud-init.yaml.tftpl       OS-Konfiguration (kommt als user_data auf die VM)
├── app/
│   ├── app.py                      FastAPI-App (HTML + JSON)
│   ├── requirements.txt            Python-Dependencies
│   └── Caddyfile.tpl               Reverse-Proxy + TLS-Konfig
└── github-workflows/               -> nach `.github/workflows/` im Repo-Root kopieren
    ├── infra-apply.yml
    └── infra-destroy.yml
```

## 4. Voraussetzungen

| Tool / Account | Wofür |
|---|---|
| GitHub-Fork von `DrackThor/fhb-biti-vica-ss26` | Code & Workflows hosten |
| Exoscale-Account + IAM-API-Key/-Secret | VM-Provisionierung |
| DuckDNS-Account + Token + freie Subdomain | DNS + Let's-Encrypt |
| SSH-Keypair (`ed25519` empfohlen) | Optionales Debugging der VM |

### 4.1 DuckDNS einrichten (einmalig, ~ 2 min)

1. <https://www.duckdns.org> öffnen und mit GitHub-Account einloggen.
2. Subdomain anlegen, z. B. `lucas-vica`. → ergibt FQDN `lucas-vica.duckdns.org`.
3. Token oben auf der Seite kopieren (UUID-Format).
4. IP-Adresse kann leer bleiben – wir aktualisieren sie automatisch.

### 4.2 Exoscale-API-Key

Im Exoscale-Portal unter **IAM → API Keys → Add** einen Key mit den Berechtigungen *Compute*, *Networking*, *IAM* (nur SSH-Keys) und *Storage* anlegen. Key & Secret notieren – beides wird nur einmal angezeigt.

### 4.3 GitHub-Repository-Secrets

Im eigenen Fork unter **Settings → Secrets and variables → Actions → New repository secret** folgende Secrets anlegen:

| Secret-Name | Inhalt |
|---|---|
| `EXOSCALE_API_KEY` | API-Key aus Exoscale |
| `EXOSCALE_API_SECRET` | API-Secret aus Exoscale |
| `SSH_PUBLIC_KEY` | Inhalt von z. B. `~/.ssh/id_ed25519.pub` |
| `DUCKDNS_SUBDOMAIN` | nur der vordere Teil, z. B. `lucas-vica` |
| `DUCKDNS_TOKEN` | DuckDNS-Token |

> **Hinweis:** Für das Terraform-Remote-State-Backend (Exoscale SOS) ist **kein
> zusätzliches Secret** nötig. Die Workflows setzen die AWS-Standard-Variablen
> `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` automatisch aus demselben
> Exoscale-Key. Siehe Abschnitt 4.5.

### 4.4 Workflows aktivieren

Die beiden Dateien aus `github-workflows/` müssen am **Wurzelverzeichnis des Forks** in `.github/workflows/` liegen, damit GitHub sie ausführt:

```bash
# Im eigenen Fork-Clone:
mkdir -p .github/workflows
cp Ehold_Lucas/Abgabe_2_260518/github-workflows/*.yml .github/workflows/
git add .github && git commit -m "Activate Abgabe 2 workflows" && git push
```

### 4.5 Terraform Remote-State (Exoscale SOS) – vollautomatisch

Der Terraform-State wird **nicht** lokal gehalten, sondern in einem
S3-kompatiblen **Exoscale-SOS-Bucket** (`ehold-vica-abgabe2-tfstate`,
Zone `at-vie-1`). Das ist entscheidend, weil GitHub-Actions-Runner bei jedem
Lauf frisch sind: Nur über den geteilten Remote-State "weiß" der
**Destroy**-Workflow, welche Ressourcen der **Apply**-Workflow angelegt hat.

Der Bucket wird vom Workflow **vor** `terraform init` idempotent angelegt
(`aws s3 mb ... || true`) – es ist also kein manueller Schritt nötig.
Konfiguriert ist das Backend in `terraform/backend.tf`; die nötigen
`skip_*`-Flags (`skip_s3_checksum`, `use_path_style`, …) stellen die
Kompatibilität mit dem Nicht-AWS-Endpunkt sicher.

> **Versions-Hinweis:** Terraform ist bewusst auf **1.9.8** gepinnt. Neuere
> Versionen (1.11+) haben bekannte Regressionen mit S3-kompatiblen
> Nicht-AWS-Backends (Checksum-Handling) – 1.9.8 ist hier stabil.

## 5. Bedienung – Step by Step

### 5.1 Infrastruktur erstellen

1. Im Fork unter **Actions → "Infra Apply (Exoscale)" → Run workflow** klicken.
2. Im Input-Feld `yes` eintragen → **Run workflow**.
3. Der Job läuft ca. 3–5 Minuten:
   - Terraform legt SSH-Key, Security-Group und VM an.
   - Cloud-Init installiert Caddy, FastAPI, DuckDNS-Updater.
   - Caddy holt automatisch ein Let's-Encrypt-Zertifikat.
   - Der eingebaute Smoke-Test wartet bis zu 5 Minuten auf einen HTTP-200 vom `/api/info`-Endpoint.
4. Am Ende des Logs zeigen die **Terraform-Outputs** die URLs an, z. B.:
   ```
   api_url           = "https://lucas-vica.duckdns.org/api/info"
   html_url          = "https://lucas-vica.duckdns.org/"
   instance_public_ip= "194.182.xxx.xxx"
   ssh_command       = "ssh ubuntu@194.182.xxx.xxx"
   ```

### 5.2 Infrastruktur zerstören

1. **Actions → "Infra Destroy (Exoscale)" → Run workflow**.
2. Im Input-Feld `destroy` eintragen → **Run workflow**.
3. Terraform entfernt die VM, die Security-Group und den SSH-Key wieder.

### 5.3 Lokal ausführen (optional, ohne GitHub Actions)

Falls man die Pipeline lokal debuggen will:

```bash
cd Ehold_Lucas/Abgabe_2_260518/terraform

export EXOSCALE_API_KEY=...      # aus Exoscale-Portal
export EXOSCALE_API_SECRET=...
export TF_VAR_ssh_public_key="$(cat ~/.ssh/id_ed25519.pub)"
export TF_VAR_duckdns_subdomain="lucas-vica"
export TF_VAR_duckdns_token="..."

terraform init
terraform plan
terraform apply
```

## 6. Was passiert auf der VM? (Reihenfolge)

| # | Schritt | Wo definiert |
|---|---|---|
| 1 | Pakete aktualisieren + Basistools installieren | `cloud-init.yaml.tftpl` (`packages`) |
| 2 | DuckDNS-Updater-Script + systemd-Service + Timer schreiben | `write_files` |
| 3 | FastAPI-App + requirements.txt schreiben | `write_files` (base64) |
| 4 | systemd-Unit für FastAPI schreiben | `write_files` |
| 5 | Caddyfile mit FQDN schreiben | `write_files` (base64) |
| 6 | Service-User `vminfo` anlegen | `runcmd` |
| 7 | Caddy aus offiziellem Cloudsmith-APT-Repo installieren | `runcmd` |
| 8 | DuckDNS triggern → A-Record zeigt jetzt auf die VM | `runcmd` |
| 9 | 30 s warten (DNS-Propagation) | `runcmd` |
| 10 | Python-venv + Dependencies installieren | `runcmd` |
| 11 | `vminfo.service` starten (FastAPI auf 127.0.0.1:8000) | `runcmd` |
| 12 | Caddy restart → ACME challenge → HTTPS aktiv | `runcmd` |

## 7. Endpoints im Detail

### `/` – HTML-Dashboard

Selbst gerenderte Übersichtskarten (Dark-Theme, ohne externe JS-Libraries) mit:

- System (Distribution, Kernel, Architektur, Hypervisor, Uptime, FQDN)
- CPU (Kerne, Takt, Load-Avg, aktuelle Auslastung mit Balken)
- Memory (Total / Used / Available + Balken)
- Disk Root (Total / Used / Free + Balken)
- Netzwerk (Hostname, Public-IP, alle Interfaces inkl. IPv6)
- Filesystems (Device, Mountpoint, Typ, Auslastung pro Mount)

Bei jedem Reload aktualisieren sich alle Werte (kein Caching).

### `/api/info` – JSON-API

Liefert exakt dieselben Daten in maschinenlesbarer Form, z. B.:

```json
{
  "generated_at": "2026-05-18T19:23:11+00:00",
  "hostname": "lucas-vica",
  "public_ip": "194.182.x.x",
  "platform": { "kernel": "6.8.0-45-generic", "machine": "x86_64", "...": "..." },
  "distribution": { "pretty_name": "Ubuntu 24.04.1 LTS", "...": "..." },
  "hypervisor": "kvm",
  "cpu": { "logical_cores": 2, "physical_cores": 1, "percent": 3.4, "...": "..." },
  "memory": { "total_bytes": 2034712576, "percent": 21.4, "...": "..." },
  "disk_root": { "total_bytes": 10500000000, "percent": 18.0, "...": "..." },
  "filesystems": [ { "device": "/dev/vda1", "fstype": "ext4", "...": "..." } ],
  "network_interfaces": { "eth0": [{ "family": "AF_INET", "address": "..." }] }
}
```

## 8. Bewertungsrelevante Bonuspunkte

| Kriterium | Umsetzung |
|---|---|
| HTTPS mit echtem Zertifikat | Caddy + Let's Encrypt (ACME http-01 challenge) |
| DNS | DuckDNS-A-Record per Cloud-Init initial + alle 5 min automatisch aktualisiert |
| HTML- und JSON-Endpoint auf getrennten Pfaden | `/` (HTML) vs. `/api/info` (JSON) |
| Security-Header | HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy |
| Service-Hardening | FastAPI läuft als unprivilegierter User mit `NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome` |

## 9. Trouble-Shooting

| Symptom | Diagnose-Befehl auf der VM |
|---|---|
| Seite antwortet nicht | `sudo systemctl status caddy` / `journalctl -u caddy -e` |
| FastAPI down | `sudo systemctl status vminfo` / `journalctl -u vminfo -e` |
| Kein HTTPS / 525-Fehler | `journalctl -u caddy` nach `obtain_cert` – meist DNS-Propagation, einfach abwarten oder DuckDNS-Update manuell triggern: `sudo /etc/duckdns/update.sh` |
| Cloud-Init Status | `cloud-init status --long` und `/var/log/cloud-init-output.log` |

## 10. Bekannte Limitationen / nicht im Scope

- **Kein State-Locking** – der State liegt in Exoscale SOS (siehe 4.5), aber ohne verteiltes Lock (z. B. DynamoDB). Bei nur einer Person, die die Workflows seriell startet, ist das unkritisch; bei parallelen Läufen könnte es zu State-Konflikten kommen (das `concurrency`-Gate im Workflow verhindert dies zusätzlich).
- **Single-AZ, keine HA** – die VM ist eine einzelne Instanz; Ausfall = Downtime.
- **Keine Backups** – Disk wird beim Destroy mit gelöscht.
- **Public SSH (Port 22) offen für 0.0.0.0/0** – für eine Übung praktikabel, in Produktion via Bastion oder Tailscale einschränken.

## 11. Quellen

- Exoscale Terraform Provider Doku: <https://registry.terraform.io/providers/exoscale/exoscale/latest/docs>
- Cloud-Init Reference: <https://cloudinit.readthedocs.io/en/latest/reference/modules.html>
- Caddy Documentation: <https://caddyserver.com/docs/>
- DuckDNS API: <https://www.duckdns.org/spec.jsp>
- FastAPI: <https://fastapi.tiangolo.com>
- psutil API: <https://psutil.readthedocs.io/en/latest/>
