#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "$ROOT_DIR"

source "${ROOT_DIR}/scripts/lib/python.sh"
source "${ROOT_DIR}/scripts/lib/env.sh"
PYTHON_BIN="$(resolve_python "$ROOT_DIR")"

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

load_dotenv_preserving_explicit_env .env API_HOST API_PORT PYCHARM_DEBUG_HOST PYCHARM_DEBUG_PORT PYCHARM_DEBUG_SUSPEND PYCHARM_DEBUG_STDOUT PYCHARM_DEBUG_STDERR

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8001}"
export API_HOST
export API_PORT

if [ "$MODE" = "debug" ]; then
  export API_DEBUG=true
fi

"$PYTHON_BIN" scripts/dev/check_auth_dev_user.py

if [ "${API_DB_AUTO_MIGRATE:-true}" != "false" ]; then
  bash scripts/db/migrate.sh
fi

if [ "$MODE" = "debug" ]; then
  echo "[dev] starting api on http://${API_HOST}:${API_PORT} (debug, PyCharm attach)"
  echo "[dev] PyCharm debug server: ${PYCHARM_DEBUG_HOST:-127.0.0.1}:${PYCHARM_DEBUG_PORT:-5678}"
  exec "$PYTHON_BIN" scripts/dev/pycharm_debug_uvicorn.py --host "$API_HOST" --port "$API_PORT"
fi

echo "[dev] starting api on http://${API_HOST}:${API_PORT}"
exec "$PYTHON_BIN" scripts/dev/run_api.py --host "$API_HOST" --port "$API_PORT"
