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
  fi
  if command -v fuser >/dev/null 2>&1; then
    fuser "$port/tcp" 2>/dev/null || true
  fi
  find_pids_with_ss "$port"
}

find_pids_with_ss() {
  local port="$1"
  local line
  if ! command -v ss >/dev/null 2>&1; then
    return
  fi
  while IFS= read -r line; do
    if [[ "$line" =~ pid=([0-9]+) ]]; then
      printf "%s\n" "${BASH_REMATCH[1]}"
    fi
  done < <(ss -ltnp "sport = :${port}" 2>/dev/null || true)
}

is_wsl_shell() {
  grep -qiE "(microsoft|wsl)" /proc/version 2>/dev/null
}

find_wsl_pids() {
  local port="$1"
  if is_wsl_shell || ! command -v wsl.exe >/dev/null 2>&1; then
    return
  fi
  wsl.exe sh -lc "port='${port}'; if command -v lsof >/dev/null 2>&1; then lsof -tiTCP:\$port -sTCP:LISTEN 2>/dev/null || true; fi; if command -v fuser >/dev/null 2>&1; then fuser \"\$port/tcp\" 2>/dev/null || true; fi; if command -v ss >/dev/null 2>&1; then ss -ltnp \"sport = :\$port\" 2>/dev/null | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p'; fi" \
    2>/dev/null || true
}

find_windows_pids() {
  local port="$1"
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
      "Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique" \
      2>/dev/null || true
  fi
  find_windows_pids_with_netstat "$port"
}

find_windows_pids_with_netstat() {
  local port="$1"
  local line
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
      "netstat -ano | ForEach-Object { if (\$_ -match '127\.0\.0\.1:${port}\s+.*LISTENING\s+(\d+)$') { \$Matches[1] } }" \
      2>/dev/null || true
    return
  fi
  if ! command -v cmd.exe >/dev/null 2>&1; then
    return
  fi
  while IFS= read -r line; do
    line="${line//$'\r'/}"
    if [[ "$line" =~ 127\.0\.0\.1:${port}[[:space:]]+.*LISTENING[[:space:]]+([0-9]+)$ ]]; then
      printf "%s\n" "${BASH_REMATCH[1]}"
    fi
  done < <(cmd.exe //D //S //C "netstat -ano -p tcp" 2>/dev/null || true)
}

kill_windows_port() {
  local port="$1"
  if ! command -v powershell.exe >/dev/null 2>&1; then
    return
  fi
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
    "\$processIds = @(Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique); foreach (\$processId in \$processIds) { try { Stop-Process -Id \$processId -Force -ErrorAction Stop } catch { Write-Output \"[dev] Stop-Process failed for Windows PID \$processId: \$(\$_.Exception.Message)\" } }" \
    2>/dev/null | strip_cr_nonempty || true
}

strip_cr_nonempty() {
  local line
  while IFS= read -r line; do
    line="${line//$'\r'/}"
    if [ -n "$line" ]; then
      echo "$line"
    fi
  done
}

describe_windows_pids() {
  local pid_list="$1"
  if [ -z "$pid_list" ] || ! command -v powershell.exe >/dev/null 2>&1; then
    return
  fi
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
    "\$processIds = '${pid_list}'.Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries); foreach (\$processId in \$processIds) { try { \$process = Get-CimInstance Win32_Process -Filter \"ProcessId = \$processId\" -ErrorAction Stop; \$name = if (\$process.Name) { \$process.Name } else { '<unknown>' }; \$path = if (\$process.ExecutablePath) { \$process.ExecutablePath } else { '<path unavailable>' }; \$parent = if (\$process.ParentProcessId) { \$process.ParentProcessId } else { '<unknown>' }; Write-Output \"[dev] Windows PID \$processId: name=\$name; parent=\$parent; path=\$path\" } catch { try { \$process = Get-Process -Id ([int]\$processId) -ErrorAction Stop; Write-Output \"[dev] Windows PID \$processId: name=\$(\$process.ProcessName); parent=<unknown>; path=<unavailable>\" } catch { Write-Output \"[dev] Windows PID \$processId: unable to inspect process details: \$(\$_.Exception.Message)\" } } }" \
    2>/dev/null | strip_cr_nonempty || true
}

kill_windows_pids() {
  local pid_list="$1"
  local process_id
  local taskkill_output
  local fallback_pid_list=""
  if [ -z "$pid_list" ]; then
    return
  fi
  if command -v taskkill.exe >/dev/null 2>&1; then
    for process_id in $pid_list; do
      if ! taskkill_output="$(MSYS2_ARG_CONV_EXCL="*" taskkill.exe /F /PID "$process_id" 2>&1)"; then
        fallback_pid_list="${fallback_pid_list}${process_id} "
        taskkill_output="${taskkill_output//$'\r'/}"
        if [ -n "$taskkill_output" ]; then
          while IFS= read -r line; do
            if [ -n "$line" ]; then
              echo "[dev] taskkill failed for Windows PID ${process_id}: ${line}"
            fi
          done <<<"$taskkill_output"
        else
          echo "[dev] taskkill failed for Windows PID ${process_id}"
        fi
      fi
    done
  else
    fallback_pid_list="$pid_list"
  fi
  if [ -z "$fallback_pid_list" ]; then
    return
  fi
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
      "\$processIds = '${fallback_pid_list}'.Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries); foreach (\$processId in \$processIds) { try { Stop-Process -Id ([int]\$processId) -Force -ErrorAction Stop } catch { Write-Output \"[dev] Stop-Process failed for Windows PID \$processId: \$(\$_.Exception.Message)\" } }" \
      2>/dev/null | strip_cr_nonempty || true
  fi
}

kill_wsl_pids() {
  local pid_list="$1"
  if [ -z "$pid_list" ] || is_wsl_shell || ! command -v wsl.exe >/dev/null 2>&1; then
    return
  fi
  wsl.exe sh -lc "for process_id in ${pid_list}; do kill -9 \"\$process_id\" 2>/dev/null || true; done" \
    >/dev/null 2>&1 || true
}

normalize_pids() {
  local pid
  local seen=" "
  while IFS= read -r pid; do
    pid="${pid//$'\r'/}"
    pid="${pid//[[:space:]]/}"
    if [[ "$pid" =~ ^[0-9]+$ ]] && [[ "$seen" != *" $pid "* ]]; then
      printf "%s " "$pid"
      seen="${seen}${pid} "
    fi
  done
}

pause_after_kill() {
  if command -v sleep >/dev/null 2>&1; then
    sleep 1
    return
  fi
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 1" >/dev/null 2>&1 || true
  fi
}

for port in "$@"; do
  echo "[dev] checking port ${port}..."
  pids="$(find_pids "$port" | normalize_pids || true)"
  wsl_pids="$(find_wsl_pids "$port" | normalize_pids || true)"
  windows_pids="$(find_windows_pids "$port" | normalize_pids || true)"
  if [ -n "$pids" ]; then
    echo "[dev] port ${port} occupied by PID(s): ${pids}; killing"
    kill -9 $pids 2>/dev/null || true
  fi
  if [ -n "$wsl_pids" ]; then
    echo "[dev] WSL port ${port} occupied by PID(s): ${wsl_pids}; killing"
    kill_wsl_pids "$wsl_pids"
  fi
  if [ -n "$windows_pids" ]; then
    echo "[dev] Windows port ${port} occupied by PID(s): ${windows_pids}; killing"
    describe_windows_pids "$windows_pids"
    kill_windows_pids "$windows_pids"
  fi
  if [ -n "$pids" ] || [ -n "$wsl_pids" ] || [ -n "$windows_pids" ]; then
    pause_after_kill
  fi
  remaining_pids="$(find_pids "$port" | normalize_pids || true)"
  remaining_wsl_pids="$(find_wsl_pids "$port" | normalize_pids || true)"
  remaining_windows_pids="$(find_windows_pids "$port" | normalize_pids || true)"
  if [ -z "$remaining_pids" ] && [ -z "$remaining_wsl_pids" ] && [ -z "$remaining_windows_pids" ]; then
    echo "[dev] port ${port} is free"
  else
    echo "[dev] failed to free port ${port}; remaining PID(s): ${remaining_pids}${remaining_wsl_pids}${remaining_windows_pids}"
    if [ -n "$remaining_windows_pids" ]; then
      echo "[dev] Windows still reports port ${port} in the TCP table. If taskkill says the PID does not exist, the listener is likely owned by System or the virtualization network layer."
      echo '[dev] bypass example (PowerShell): $env:API_PORT="8002"; npm run dev'
    fi
    exit 1
  fi
done
