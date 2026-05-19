#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "[dev] no ports provided"
  exit 0
fi

find_pids() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
    return
  fi
  if command -v fuser >/dev/null 2>&1; then
    fuser "$port/tcp" 2>/dev/null || true
    return
  fi
}

for port in "$@"; do
  echo "[dev] checking port ${port}..."
  pids="$(find_pids "$port" | xargs echo || true)"
  if [ -z "$pids" ]; then
    echo "[dev] port ${port} is free"
    continue
  fi
  echo "[dev] port ${port} occupied by PID(s): ${pids}; killing"
  kill -9 $pids 2>/dev/null || true
done
