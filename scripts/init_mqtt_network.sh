#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

COMPOSE_FILE="${COMPOSE_FILE:-${REPO_ROOT}/deployments/docker-compose.iot.yml}"
EMQX_CONF_FILE="${EMQX_CONF_FILE:-${REPO_ROOT}/deployments/emqx/emqx_base.conf}"
IOT_NETWORK_NAME="${IOT_DOCKER_NETWORK:-gridguard_iot_baseline_net}"
MQTT_PORT="${EMQX_MQTT_TCP_PORT:-1883}"

echo "[INFO] Checking required tools..."
command -v docker >/dev/null 2>&1 || { echo "[ERROR] docker is not installed or not in PATH."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "[ERROR] docker compose is not available."; exit 1; }
docker info >/dev/null 2>&1 || { echo "[ERROR] Docker daemon is not running."; exit 1; }

echo "[INFO] Checking required configuration files..."
[[ -f "${COMPOSE_FILE}" ]] || { echo "[ERROR] Missing compose file: ${COMPOSE_FILE}"; exit 1; }
[[ -f "${EMQX_CONF_FILE}" ]] || { echo "[ERROR] Missing EMQX config file: ${EMQX_CONF_FILE}"; exit 1; }

# Ensure unencrypted MQTT port is not published to host interfaces in compose file
if grep -Eq '^\s*-\s*["'\'']?[0-9.]+:'"${MQTT_PORT}"'(:|/)' "${COMPOSE_FILE}" || grep -Eq '^\s*-\s*["'\'']?'"${MQTT_PORT}"'(:|/)' "${COMPOSE_FILE}"; then
  echo "[ERROR] Unencrypted MQTT port ${MQTT_PORT} must not be published externally in ${COMPOSE_FILE}."
  exit 1
fi

echo "[INFO] Validating docker compose configuration..."
docker compose -f "${COMPOSE_FILE}" config >/dev/null

echo "[INFO] Ensuring isolated bridge network '${IOT_NETWORK_NAME}' exists..."
if ! docker network inspect "${IOT_NETWORK_NAME}" >/dev/null 2>&1; then
  docker network create --driver bridge "${IOT_NETWORK_NAME}" >/dev/null
  echo "[INFO] Created network '${IOT_NETWORK_NAME}'."
else
  echo "[INFO] Network '${IOT_NETWORK_NAME}' already exists."
fi

echo "[INFO] MQTT baseline network initialization checks completed successfully."
