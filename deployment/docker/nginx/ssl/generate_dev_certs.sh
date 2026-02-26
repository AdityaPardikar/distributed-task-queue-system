#!/usr/bin/env bash
# ============================================================================
# Generate Self-Signed SSL Certificates for Development
# ============================================================================
# Creates a self-signed CA and server certificate for local HTTPS testing.
# NOT for production — use Let's Encrypt or a real CA in production.
#
# Usage:
#   chmod +x generate_dev_certs.sh
#   ./generate_dev_certs.sh
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="${SCRIPT_DIR}/certs"
DAYS_VALID=365
DOMAIN="localhost"
ORG="TaskFlow Development"

echo "========================================"
echo "  TaskFlow — Dev SSL Certificate Generator"
echo "========================================"

# Create output directory
mkdir -p "${CERT_DIR}"

# Generate CA private key
echo "[1/4] Generating CA private key..."
openssl genrsa -out "${CERT_DIR}/ca.key" 4096 2>/dev/null

# Generate CA certificate
echo "[2/4] Generating CA certificate..."
openssl req -x509 -new -nodes \
    -key "${CERT_DIR}/ca.key" \
    -sha256 \
    -days "${DAYS_VALID}" \
    -out "${CERT_DIR}/ca.crt" \
    -subj "/C=US/ST=Dev/L=Dev/O=${ORG}/CN=TaskFlow Dev CA"

# Generate server private key
echo "[3/4] Generating server private key..."
openssl genrsa -out "${CERT_DIR}/server.key" 2048 2>/dev/null

# Create config for SAN (Subject Alternative Names)
cat > "${CERT_DIR}/server.cnf" <<EOF
[req]
default_bits       = 2048
prompt             = no
default_md         = sha256
distinguished_name = dn
req_extensions     = v3_req

[dn]
C  = US
ST = Development
L  = Local
O  = ${ORG}
CN = ${DOMAIN}

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
DNS.3 = taskflow.local
DNS.4 = api.taskflow.local
IP.1  = 127.0.0.1
IP.2  = ::1
EOF

# Generate server CSR and sign with CA
echo "[4/4] Generating server certificate..."
openssl req -new \
    -key "${CERT_DIR}/server.key" \
    -out "${CERT_DIR}/server.csr" \
    -config "${CERT_DIR}/server.cnf"

openssl x509 -req \
    -in "${CERT_DIR}/server.csr" \
    -CA "${CERT_DIR}/ca.crt" \
    -CAkey "${CERT_DIR}/ca.key" \
    -CAcreateserial \
    -out "${CERT_DIR}/server.crt" \
    -days "${DAYS_VALID}" \
    -sha256 \
    -extensions v3_req \
    -extfile "${CERT_DIR}/server.cnf" 2>/dev/null

# Combine for Nginx
cat "${CERT_DIR}/server.crt" "${CERT_DIR}/ca.crt" > "${CERT_DIR}/fullchain.pem"
cp "${CERT_DIR}/server.key" "${CERT_DIR}/privkey.pem"

# Set permissions
chmod 600 "${CERT_DIR}"/*.key "${CERT_DIR}/privkey.pem"
chmod 644 "${CERT_DIR}"/*.crt "${CERT_DIR}/fullchain.pem"

# Clean up CSR and serial
rm -f "${CERT_DIR}/server.csr" "${CERT_DIR}/ca.srl" "${CERT_DIR}/server.cnf"

echo ""
echo "Certificates generated in: ${CERT_DIR}/"
echo "  ca.crt       — CA certificate (trust this in your browser)"
echo "  server.crt   — Server certificate"
echo "  server.key   — Server private key"
echo "  fullchain.pem — Full chain (server + CA) for Nginx"
echo "  privkey.pem   — Private key copy for Nginx"
echo ""
echo "Nginx config snippet:"
echo "  ssl_certificate     /etc/nginx/ssl/fullchain.pem;"
echo "  ssl_certificate_key /etc/nginx/ssl/privkey.pem;"
echo ""
echo "To trust the CA in your browser:"
echo "  macOS:   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ${CERT_DIR}/ca.crt"
echo "  Linux:   sudo cp ${CERT_DIR}/ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates"
echo "  Windows: certutil -addstore -f \"ROOT\" ${CERT_DIR}/ca.crt"
echo ""
echo "Done!"
