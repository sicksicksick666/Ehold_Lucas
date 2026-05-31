# --------------------------------------------------------------------------- #
#  Remote-State-Backend  –  Exoscale SOS (S3-kompatibel)                       #
#                                                                             #
#  WARUM überhaupt ein Remote-State?                                          #
#  ------------------------------------------------------------------------- #
#  Terraform speichert in der State-Datei, WELCHE Ressourcen es verwaltet.    #
#  GitHub-Actions-Runner sind aber bei JEDEM Lauf frisch und leer. Läge der   #
#  State nur lokal im Runner, hätte der Destroy-Workflow einen leeren State   #
#  und würde NICHTS löschen. Deshalb legen wir den State in einen Exoscale-   #
#  SOS-Bucket (S3-kompatibel). So teilen sich Apply- und Destroy-Workflow     #
#  exakt denselben State – Erstellen und Löschen funktionieren zuverlässig.   #
#                                                                             #
#  Authentifizierung:                                                         #
#    Die Zugangsdaten (= derselbe Exoscale-API-Key/-Secret) werden NICHT      #
#    hier eingetragen, sondern vom Workflow über die Standard-Umgebungs-      #
#    variablen AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY gesetzt. Damit       #
#    landen keine Secrets in Git.                                             #
#                                                                             #
#  Der Bucket selbst wird vom Workflow vor `terraform init` idempotent        #
#  angelegt (siehe infra-apply.yml / infra-destroy.yml).                      #
# --------------------------------------------------------------------------- #
terraform {
  backend "s3" {
    # Name des SOS-Buckets, in dem die State-Datei liegt.
    bucket = "ehold-vica-abgabe2-tfstate"
    # Pfad/Objekt-Key der State-Datei innerhalb des Buckets.
    key = "abgabe2/terraform.tfstate"
    # Exoscale-Zone des Buckets (entspricht der AWS-"Region").
    region = "at-vie-1"

    # SOS-Endpunkt – das ist der entscheidende Unterschied zu echtem AWS S3.
    endpoints = {
      s3 = "https://sos-at-vie-1.exo.io"
    }

    # Exoscale ist NICHT AWS -> alle AWS-spezifischen Prüfungen abschalten,
    # sonst scheitert `terraform init`/`apply` an Account-/Region-Checks.
    skip_credentials_validation = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    # SOS unterstützt die neuen AWS-SHA256-Objekt-Checksums nicht ->
    # zwingend abschalten (sonst Upload-Fehler beim State-Speichern).
    skip_s3_checksum = true
    # Path-Style-URLs (https://endpoint/bucket) statt Virtual-Hosted-Style.
    use_path_style = true
  }
}
