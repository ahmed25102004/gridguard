
#!/usr/bin/env bash

set -Eeuo pipefail

IMAGES=(
  "python:3.12-slim"
  "node:18-alpine"
)

if ! command -v trivy >/dev/null 2>&1; then
  echo "[ERROR] Trivy is not installed or not available in PATH."
  echo "Install Trivy before running this script."
  exit 1
fi

echo "======================================"
echo " GridGuard Container Security Scanner"
echo "======================================"

for image in "${IMAGES[@]}"; do
  echo ""
  echo "[INFO] Scanning image: ${image}"

  trivy image \
    --severity HIGH,CRITICAL \
    --exit-code 1 \
    "${image}"

  echo "[INFO] Scan completed: ${image}"
done

echo ""
echo "[SUCCESS] All image scans completed without blocking findings."
