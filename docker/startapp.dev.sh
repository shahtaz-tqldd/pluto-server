#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# docker kill $(docker ps -q)

docker compose -f "${SCRIPT_DIR}/compose.dev.yml" down --remove-orphans
docker compose -f "${SCRIPT_DIR}/compose.dev.yml" up --build "$@"
