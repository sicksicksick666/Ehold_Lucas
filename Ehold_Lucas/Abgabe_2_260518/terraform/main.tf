# --------------------------------------------------------------------------- #
#  Haupt-Ressourcen für die Exoscale-Infrastruktur                            #
#                                                                             #
#  Ressourcen-Übersicht:                                                      #
#    1. data "exoscale_template"  -> findet die aktuelle Ubuntu-AMI/Template  #
#    2. exoscale_ssh_key          -> lädt unseren Public-Key hoch             #
#    3. exoscale_security_group   -> Firewall-Regelwerk                       #
#    4. exoscale_security_group_rule (3x) -> SSH, HTTP, HTTPS                 #
#    5. exoscale_compute_instance -> die eigentliche Ubuntu-VM                #
# --------------------------------------------------------------------------- #

# ---------- 1. Ubuntu-Template suchen ------------------------------------- #
# Wir fragen Exoscale nach dem aktuellsten, von Exoscale gepflegten
# Public-Template. Damit bleibt die Konfiguration zukunftssicher, ohne dass
# wir die Template-ID manuell pflegen müssen.
data "exoscale_template" "ubuntu" {
  zone = var.zone
  name = var.template_name
}

# ---------- 2. SSH-Public-Key hochladen ----------------------------------- #
resource "exoscale_ssh_key" "deploy" {
  name       = "${var.project_name}-key"
  public_key = var.ssh_public_key
}

# ---------- 3. Security Group anlegen ------------------------------------- #
resource "exoscale_security_group" "web" {
  name        = "${var.project_name}-sg"
  description = "Erlaubt SSH (22), HTTP (80) und HTTPS (443) aus dem Internet."
}

# ---------- 4a. Regel: SSH (Port 22) -------------------------------------- #
# Im echten Betrieb würde man hier auf eine Whitelist (Office-IP, Bastion)
# einschränken. Für die Übung lassen wir 0.0.0.0/0 zu.
resource "exoscale_security_group_rule" "ssh" {
  security_group_id = exoscale_security_group.web.id
  type              = "INGRESS"
  protocol          = "TCP"
  cidr              = "0.0.0.0/0"
  start_port        = 22
  end_port          = 22
  description       = "SSH-Zugang für Debugging"
}

# ---------- 4b. Regel: HTTP (Port 80) ------------------------------------- #
# Port 80 wird auch von Caddy für die ACME http-01 Challenge benötigt, sonst
# bekommen wir kein Let's-Encrypt-Zertifikat.
resource "exoscale_security_group_rule" "http" {
  security_group_id = exoscale_security_group.web.id
  type              = "INGRESS"
  protocol          = "TCP"
  cidr              = "0.0.0.0/0"
  start_port        = 80
  end_port          = 80
  description       = "HTTP für Caddy & ACME challenge"
}

# ---------- 4c. Regel: HTTPS (Port 443) ----------------------------------- #
resource "exoscale_security_group_rule" "https" {
  security_group_id = exoscale_security_group.web.id
  type              = "INGRESS"
  protocol          = "TCP"
  cidr              = "0.0.0.0/0"
  start_port        = 443
  end_port          = 443
  description       = "HTTPS für die VM-Info-Webseite/API"
}

# ---------- 5. Compute Instance ------------------------------------------- #
# Hier kommt die eigentliche Ubuntu-VM. Wir reichen den Cloud-Init-User-Data
# als base64 NICHT durch (Exoscale akzeptiert auch plain), und nutzen
# templatefile() um Variablen (DuckDNS-Token, Domain) sicher zur Boot-Zeit
# einzusetzen.
resource "exoscale_compute_instance" "vm" {
  zone               = var.zone
  name               = "${var.project_name}-vm"
  type               = var.instance_type
  template_id        = data.exoscale_template.ubuntu.id
  disk_size          = var.disk_size
  ssh_keys           = [exoscale_ssh_key.deploy.name] # 'ssh_keys' (Set) ist der aktuelle Provider-Arg; 'ssh_key' ist deprecated
  security_group_ids = [exoscale_security_group.web.id]

  # Labels helfen später bei Abrechnung & Auswertung in der Exoscale-Console.
  labels = {
    project = var.project_name
    course  = "fh-burgenland-vica-ss26"
    owner   = "ehold-lucas"
  }

  # Cloud-Init: Die komplette Konfiguration des Betriebssystems passiert
  # ausschließlich über das Cloud-Init-Skript (Anforderung der Aufgabe).
  #
  # app.py, requirements.txt und Caddyfile werden hier base64-codiert
  # eingebettet, damit Sonderzeichen (insb. im Python-Code) das YAML nicht
  # zerlegen können. Das Caddyfile wird zusätzlich per templatefile() mit
  # dem FQDN gerendert, bevor es codiert wird.
  # base64gzip(): Exoscale begrenzt user_data auf 32768 Bytes (auf die
  # base64-codierte Form). Unser Cloud-Init ist roh ~27 KB -> base64 ~37 KB
  # und damit zu groß. gzip+base64 schrumpft es auf ~14 KB. Der Provider
  # reicht bereits base64-codierte Daten unveraendert durch, und cloud-init
  # erkennt/entpackt das gzip auf der VM automatisch.
  user_data = base64gzip(templatefile("${path.module}/cloud-init.yaml.tftpl", {
    duckdns_subdomain = var.duckdns_subdomain
    duckdns_token     = var.duckdns_token
    fqdn              = "${var.duckdns_subdomain}.duckdns.org"
    app_py_b64        = base64encode(file("${path.module}/../app/app.py"))
    requirements_b64  = base64encode(file("${path.module}/../app/requirements.txt"))
    caddyfile_b64 = base64encode(templatefile("${path.module}/../app/Caddyfile.tpl", {
      fqdn = "${var.duckdns_subdomain}.duckdns.org"
    }))
  }))
}
