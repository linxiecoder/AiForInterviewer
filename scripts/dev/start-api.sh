#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "$ROOT_DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

echo "[dev] starting api on http://127.0.0.1:8001"
exec .venv/bin/python -m uvicorn app.main:app \
  --app-dir apps/api \
  --host 127.0.0.1 \
  --port 8001 \
  --reload \
  --reload-dir apps/api
