#!/usr/bin/env bash

resolve_python() {
  local root_dir="${1:-.}"

  if [ -n "${PYTHON:-}" ]; then
    printf '%s\n' "$PYTHON"
    return 0
  fi

  if [ -n "${VIRTUAL_ENV:-}" ]; then
    if [ -x "${VIRTUAL_ENV}/bin/python" ]; then
      printf '%s\n' "${VIRTUAL_ENV}/bin/python"
      return 0
    fi
    if [ -x "${VIRTUAL_ENV}/Scripts/python.exe" ]; then
      printf '%s\n' "${VIRTUAL_ENV}/Scripts/python.exe"
      return 0
    fi
  fi

  if [ -x "${root_dir}/.venv/bin/python" ]; then
    printf '%s\n' "${root_dir}/.venv/bin/python"
    return 0
  fi
  if [ -x "${root_dir}/.venv/Scripts/python.exe" ]; then
    printf '%s\n' "${root_dir}/.venv/Scripts/python.exe"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  echo "[dev] python not found; set PYTHON or create .venv" >&2
  return 1
}
