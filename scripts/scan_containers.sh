
#!/usr/bin/env bash

set -Eeuo pipefail

IMAGE="python:3.12-slim"

if ! command -v trivy >/dev/null 2>&1; then
  echo "[ERROR] Trivy is not installed or not available in PATH."
  echo "Install Trivy before running this script."
  exit 1
fi

echo "======================================"
echo " GridGuard Container Security Scanner"
echo "======================================"

echo ""
echo "[INFO] Scanning backend image: ${IMAGE}"

trivy image \
  --severity HIGH,CRITICAL \
  --exit-code 1 \
  "${IMAGE}"

echo ""
echo "[SUCCESS] Backend image scan completed without blocking findings."
