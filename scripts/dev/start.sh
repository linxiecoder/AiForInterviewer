#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "$ROOT_DIR"

source "${ROOT_DIR}/scripts/lib/node.sh"
source "${ROOT_DIR}/scripts/lib/env.sh"

API_PORT_WAS_EXPLICIT=0
if [ "${API_PORT+x}" = "x" ]; then
  API_PORT_WAS_EXPLICIT=1
fi
VITE_API_PROXY_TARGET_WAS_EXPLICIT=0
if [ "${VITE_API_PROXY_TARGET+x}" = "x" ]; then
  VITE_API_PROXY_TARGET_WAS_EXPLICIT=1
fi

load_dotenv_preserving_explicit_env .env API_HOST API_PORT WEB_PORT VITE_API_PROXY_TARGET API_LOG_FILE API_LOG_FILE_ENABLED

API_PORT="${API_PORT:-8001}"
WEB_PORT="${WEB_PORT:-5173}"
export API_PORT
export WEB_PORT

MODE="${1:-}"
case "$MODE" in
  "" | "debug")
    ;;
  *)
    echo "[dev] unsupported mode: ${MODE}"
    echo "[dev] usage: npm run dev [debug]"
    exit 2
    ;;
esac

select_web_runtime

resolve_api_port() {
  local port="$API_PORT"
  local candidate
  local max_port

  if bash scripts/dev/kill-ports.sh "$port"; then
    return 0
  fi

  if [ "$API_PORT_WAS_EXPLICIT" = "1" ]; then
    echo "[dev] API_PORT ${port} is unavailable; explicit API_PORT will not be auto-reassigned." >&2
    return 1
  fi

  if ! [[ "$port" =~ ^[0-9]+$ ]]; then
    echo "[dev] API_PORT ${port} is unavailable and cannot be used as a numeric fallback base." >&2
    return 1
  fi

  candidate=$((port + 1))
  max_port=$((port + 20))
  while [ "$candidate" -le "$max_port" ]; do
    if bash scripts/dev/kill-ports.sh "$candidate"; then
      echo "[dev] API_PORT ${port} is unavailable; using ${candidate}"
      API_PORT="$candidate"
      export API_PORT
      if [ "$VITE_API_PROXY_TARGET_WAS_EXPLICIT" != "1" ]; then
        VITE_API_PROXY_TARGET="http://127.0.0.1:${API_PORT}"
        export VITE_API_PROXY_TARGET
      fi
      return 0
    fi
    candidate=$((candidate + 1))
  done

  echo "[dev] no free API_PORT found from ${port} to ${max_port}" >&2
  return 1
}

resolve_api_port
if [ -z "${VITE_API_PROXY_TARGET:-}" ]; then
  VITE_API_PROXY_TARGET="http://127.0.0.1:${API_PORT}"
  export VITE_API_PROXY_TARGET
fi
echo "[dev] API_PORT=${API_PORT}"
echo "[dev] VITE_API_PROXY_TARGET=${VITE_API_PROXY_TARGET}"
bash scripts/dev/kill-ports.sh "$WEB_PORT"

cleanup() {
  trap - INT TERM EXIT
  if [ -n "${API_PID:-}" ] && kill -0 "$API_PID" 2>/dev/null; then
    echo "[dev] stopping api PID ${API_PID}"
    kill "$API_PID" 2>/dev/null || true
  fi
  if [ -n "${WEB_PID:-}" ] && kill -0 "$WEB_PID" 2>/dev/null; then
    echo "[dev] stopping web PID ${WEB_PID}"
    kill "$WEB_PID" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
  bash scripts/dev/kill-ports.sh "$API_PORT" "$WEB_PORT"
}

trap cleanup INT TERM EXIT

bash scripts/dev/start-api.sh "$MODE" &
API_PID="$!"
echo "[dev] api PID ${API_PID}"

start_web_dev "$ROOT_DIR" &
WEB_PID="$!"
echo "[dev] web PID ${WEB_PID}"

wait -n "$API_PID" "$WEB_PID"
exit_code="$?"
cleanup
exit "$exit_code"
