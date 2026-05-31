# --------------------------------------------------------------------------- #
#  Terraform Versions & Provider Konfiguration                                #
#                                                                             #
#  Hier wird festgelegt, welche Terraform- und Provider-Versionen verwendet   #
#  werden. Durch das Pinning vermeiden wir, dass ein Provider-Update unsere   #
#  Pipeline unerwartet "kaputt patcht".                                       #
# --------------------------------------------------------------------------- #

terraform {
  # Mindestens Terraform 1.6 (auch kompatibel mit OpenTofu >= 1.6).
  required_version = ">= 1.6.0"

  required_providers {
    # Offizieller Exoscale-Provider für Compute, Networking, IAM, ...
    exoscale = {
      source  = "exoscale/exoscale"
      version = "~> 0.62"
    }
  }
}

# --------------------------------------------------------------------------- #
#  Exoscale Provider                                                          #
#                                                                             #
#  Authentifizierung erfolgt über Umgebungsvariablen, die der GitHub-Workflow #
#  aus Secrets befüllt:                                                       #
#    - EXOSCALE_API_KEY                                                       #
#    - EXOSCALE_API_SECRET                                                    #
#  Damit landen die Keys NICHT in der State-Datei und nicht in Git.           #
# --------------------------------------------------------------------------- #
provider "exoscale" {
  # key/secret werden bewusst NICHT hier gesetzt -> kommen aus ENV vars.
}
