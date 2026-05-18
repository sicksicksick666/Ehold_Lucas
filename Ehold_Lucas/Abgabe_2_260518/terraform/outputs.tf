# --------------------------------------------------------------------------- #
#  Outputs                                                                    #
#                                                                             #
#  Werte, die nach dem `terraform apply` für den User sichtbar sein sollen,   #
#  und im GitHub-Workflow-Log angezeigt werden.                               #
# --------------------------------------------------------------------------- #

output "instance_public_ip" {
  description = "Public IPv4 der erstellten Exoscale-VM."
  value       = exoscale_compute_instance.vm.public_ip_address
}

output "fqdn" {
  description = "Voll qualifizierter Domainname (über DuckDNS)."
  value       = "${var.duckdns_subdomain}.duckdns.org"
}

output "html_url" {
  description = "URL zur HTML-Übersichtsseite (per HTTPS)."
  value       = "https://${var.duckdns_subdomain}.duckdns.org/"
}

output "api_url" {
  description = "URL zum JSON-API-Endpunkt."
  value       = "https://${var.duckdns_subdomain}.duckdns.org/api/info"
}

output "ssh_command" {
  description = "Befehl, um sich zu Debug-Zwecken per SSH zur VM zu verbinden."
  value       = "ssh ubuntu@${exoscale_compute_instance.vm.public_ip_address}"
}
