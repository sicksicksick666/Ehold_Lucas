# --------------------------------------------------------------------------- #
#  Caddy-Konfiguration                                                        #
#                                                                             #
#  Caddy holt automatisch ein Let's-Encrypt-Zertifikat für ${fqdn},          #
#  sobald die A-Record auf die VM zeigt. Anschließend wird der Traffic        #
#  als Reverse-Proxy an FastAPI (localhost:8000) weitergereicht.              #
#                                                                             #
#  Diese Datei ist ein Terraform-Template: $${fqdn} wird vor Cloud-Init       #
#  ersetzt durch den realen DuckDNS-FQDN.                                     #
# --------------------------------------------------------------------------- #

${fqdn} {
    # GZIP/Zstd Komprimierung für die HTML-Seite
    encode gzip zstd

    # Sicherheits-relevante Header
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "no-referrer"
        # Caddy verrät sich nicht groß
        -Server
    }

    # Reverse-Proxy auf die lokale FastAPI-Instanz
    reverse_proxy 127.0.0.1:8000

    # Strukturierte Logs nach journald
    log {
        output stdout
        format console
    }
}
