#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "$ROOT_DIR"

source "${ROOT_DIR}/scripts/lib/python.sh"
PYTHON_BIN="$(resolve_python "$ROOT_DIR")"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

export PYTHONPATH="apps/api${PYTHONPATH:+:${PYTHONPATH}}"
exec "$PYTHON_BIN" scripts/db/upgrade.py
