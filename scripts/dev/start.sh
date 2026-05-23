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
    echo "[dev] unsupported mode: ${MODE}"
    echo "[dev] usage: npm run dev [debug]"
    exit 2
    ;;
esac

bash scripts/dev/kill-ports.sh 8001 5173

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
}

trap cleanup INT TERM EXIT

bash scripts/dev/start-api.sh "$MODE" &
API_PID="$!"
echo "[dev] api PID ${API_PID}"

npm --workspace apps/web run dev &
WEB_PID="$!"
echo "[dev] web PID ${WEB_PID}"

wait -n "$API_PID" "$WEB_PID"
exit_code="$?"
cleanup
exit "$exit_code"
