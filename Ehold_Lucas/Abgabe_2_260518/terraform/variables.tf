# --------------------------------------------------------------------------- #
#  Variablen-Definitionen                                                     #
#                                                                             #
#  Alle Konfigurationsoptionen werden hier deklariert.                        #
#  Werte kommen entweder aus den Default-Definitionen oder werden vom         #
#  GitHub-Workflow per `TF_VAR_<name>` Umgebungsvariable überschrieben.       #
# --------------------------------------------------------------------------- #

variable "project_name" {
  description = "Kurzer Bezeichner für Ressourcen-Namen (Security-Group, SSH-Key, Instanz)."
  type        = string
  default     = "vica-abgabe2"
}

variable "zone" {
  description = <<EOT
Exoscale-Zone, in der die Ressourcen erstellt werden. Auswahl z.B.:
  - at-vie-1 (Wien)
  - at-vie-2 (Wien 2)
  - ch-gva-2 (Genf)
  - ch-dk-2  (Zürich)
  - de-fra-1 (Frankfurt)
EOT
  type        = string
  default     = "at-vie-1"
}

variable "instance_type" {
  description = "Exoscale Instanz-Typ. 'standard.micro' reicht für unseren kleinen Webservice."
  type        = string
  default     = "standard.micro"
}

variable "disk_size" {
  description = "Disk-Größe der VM in GB. Minimum bei Exoscale ist 10 GB."
  type        = number
  default     = 10
}

variable "template_name" {
  description = "Name des Exoscale-Templates für Ubuntu. Wird per data-source gesucht."
  type        = string
  default     = "Linux Ubuntu 24.04 LTS 64-bit"
}

variable "ssh_public_key" {
  description = <<EOT
Public-Key der zur Instanz hinzugefügt wird. Erlaubt SSH-Login für Debugging.
Wird im GitHub-Workflow aus dem Secret SSH_PUBLIC_KEY befüllt.
EOT
  type        = string
  sensitive   = false
}

# --------------------------------------------------------------------------- #
#  DuckDNS Konfiguration                                                      #
#                                                                             #
#  Wir verwenden DuckDNS als kostenlosen DNS-Provider, damit Caddy ein        #
#  Let's-Encrypt-Zertifikat über DNS/HTTP-Challenge holen kann.               #
# --------------------------------------------------------------------------- #
variable "duckdns_subdomain" {
  description = "DuckDNS-Subdomain (NUR der vordere Teil, ohne '.duckdns.org')."
  type        = string
}

variable "duckdns_token" {
  description = "DuckDNS-Account-Token. Sensitiv -> nicht ins State-Log loggen."
  type        = string
  sensitive   = true
}
