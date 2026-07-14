#!/usr/bin/env bash
# Generate a self-signed TLS certificate for the dev MinIO used by the isolated-agent stack
# (docker-compose.pod.yml). MinIO serves https so the pod can pull workspaces over TLS; the cert is
# self-signed, so the pod runs with AGENT_POD_WORKSPACE_TLS_VERIFY=0 and the backend's MinIO client
# with MINIO_CERT_CHECK=false. NOT for production — a real deployment uses a real object store with
# a valid certificate.
#
#   ./scripts/gen_minio_cert.sh
set -euo pipefail

CERT_DIR="$(cd "$(dirname "$0")/.." && pwd)/docker/minio/certs"
mkdir -p "$CERT_DIR"

if [[ -f "$CERT_DIR/public.crt" && -f "$CERT_DIR/private.key" ]]; then
  echo "cert already present at $CERT_DIR (delete to regenerate)"
  exit 0
fi

# SAN must include the compose service name 'minio' — that is the host in the pre-signed URL.
openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
  -keyout "$CERT_DIR/private.key" \
  -out "$CERT_DIR/public.crt" \
  -subj "/CN=minio" \
  -addext "subjectAltName=DNS:minio,DNS:localhost,IP:127.0.0.1"

echo "wrote self-signed MinIO cert to $CERT_DIR"
