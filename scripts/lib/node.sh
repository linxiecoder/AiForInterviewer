#!/usr/bin/env bash

WEB_NODE_MIN_VERSION="20.19.0"
WEB_RUNTIME_KIND=""
WEB_RUNTIME_NODE_VERSION=""

node_version_supports_web_dev() {
  local version="${1#v}"
  local major minor patch

  IFS=. read -r major minor patch _ <<<"$version"
  patch="${patch%%[^0-9]*}"

  if [ -z "$major" ] || [ -z "$minor" ]; then
    return 1
  fi

  if [ "$major" -eq 20 ]; then
    [ "$minor" -ge 19 ]
    return $?
  fi

  if [ "$major" -eq 22 ]; then
    [ "$minor" -ge 12 ]
    return $?
  fi

  [ "$major" -gt 22 ]
}

read_command_version() {
  "$@" -v 2>/dev/null | tr -d '\r' | sed -n '1p'
}

is_wsl_shell() {
  [ -r /proc/version ] && grep -qiE "microsoft|wsl" /proc/version
}

windows_path_for_shell_path() {
  local path="$1"

  if command -v wslpath >/dev/null 2>&1; then
    wslpath -w "$path"
    return 0
  fi

  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$path"
    return 0
  fi

  printf '%s\n' "$path"
}

powershell_single_quoted_literal() {
  local value="$1"
  local escaped

  escaped="$(printf '%s' "$value" | sed "s/'/''/g")"
  printf "'%s'\n" "$escaped"
}

select_web_runtime() {
  local version

  if [ -n "$WEB_RUNTIME_KIND" ]; then
    return 0
  fi

  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    version="$(read_command_version node)"
    if node_version_supports_web_dev "$version"; then
      WEB_RUNTIME_KIND="native"
      WEB_RUNTIME_NODE_VERSION="$version"
      return 0
    fi
    echo "[dev] shell node ${version:-unknown} is below required ${WEB_NODE_MIN_VERSION}"
  fi

  if command -v powershell.exe >/dev/null 2>&1; then
    version="$(
      powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "node -v" 2>/dev/null \
        | tr -d '\r' \
        | sed -n '1p'
    )"
    if node_version_supports_web_dev "$version"; then
      WEB_RUNTIME_KIND="windows"
      WEB_RUNTIME_NODE_VERSION="$version"
      return 0
    fi
  fi

  echo "[dev] Node.js ${WEB_NODE_MIN_VERSION}+ is required for Vite dev server" >&2
  echo "[dev] Upgrade Node inside the shell that runs bash, or make Windows node/npm available from WSL." >&2
  return 1
}

start_web_dev() {
  local root_dir="$1"
  local windows_root
  local powershell_root
  local powershell_api_proxy_target

  select_web_runtime
  export VITE_API_PROXY_TARGET="${VITE_API_PROXY_TARGET:-http://127.0.0.1:${API_PORT:-8001}}"

  case "$WEB_RUNTIME_KIND" in
    native)
      echo "[dev] starting web with shell node ${WEB_RUNTIME_NODE_VERSION}"
      exec npm --workspace apps/web run dev
      ;;
    windows)
      windows_root="$(windows_path_for_shell_path "$root_dir")"
      powershell_root="$(powershell_single_quoted_literal "$windows_root")"
      powershell_api_proxy_target="$(powershell_single_quoted_literal "$VITE_API_PROXY_TARGET")"
      echo "[dev] starting web with Windows node ${WEB_RUNTIME_NODE_VERSION}"
      exec powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "\$env:VITE_API_PROXY_TARGET=${powershell_api_proxy_target}; Set-Location -LiteralPath ${powershell_root}; npm.cmd --workspace apps/web run dev"
      ;;
    *)
      echo "[dev] unsupported web runtime: ${WEB_RUNTIME_KIND:-unknown}" >&2
      return 1
      ;;
  esac
}
