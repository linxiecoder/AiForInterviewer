#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "$ROOT_DIR"

MODE="${1:-}"
case "$MODE" in
  "" | "debug")
    ;;
  *)
    echo "[dev] unsupported api mode: ${MODE}"
    echo "[dev] usage: bash scripts/dev/start-api.sh [debug]"
    exit 2
    ;;
esac

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

if [ "$MODE" = "debug" ]; then
  export API_DEBUG=true
fi

UVICORN_ARGS=(
  app.main:app
  --app-dir apps/api
  --host 127.0.0.1
  --port 8001
  --reload
  --reload-dir apps/api
)

if [ "$MODE" = "debug" ]; then
  UVICORN_ARGS+=(--log-level debug)
fi

if [ "$MODE" = "debug" ]; then
  echo "[dev] starting api on http://127.0.0.1:8001 (debug)"
else
  echo "[dev] starting api on http://127.0.0.1:8001"
fi
exec .venv/bin/python -m uvicorn "${UVICORN_ARGS[@]}"
