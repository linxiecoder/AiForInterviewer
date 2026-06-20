#!/usr/bin/env bash

remember_explicit_env() {
  local name
  local set_var
  local value_var

  for name in "$@"; do
    set_var="__AIFI_EXPLICIT_${name}_SET"
    value_var="__AIFI_EXPLICIT_${name}"
    if [ "${!name+x}" = "x" ]; then
      printf -v "$set_var" '%s' "1"
      printf -v "$value_var" '%s' "${!name}"
    else
      printf -v "$set_var" '%s' ""
      printf -v "$value_var" '%s' ""
    fi
  done
}

restore_explicit_env() {
  local name
  local set_var
  local value_var

  for name in "$@"; do
    set_var="__AIFI_EXPLICIT_${name}_SET"
    value_var="__AIFI_EXPLICIT_${name}"
    if [ "${!set_var:-}" = "1" ]; then
      printf -v "$name" '%s' "${!value_var}"
      export "$name"
    fi
    unset "$set_var" "$value_var"
  done
}

load_dotenv_preserving_explicit_env() {
  local env_file="$1"
  shift

  remember_explicit_env "$@"
  if [ -f "$env_file" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$env_file"
    set +a
  fi
  restore_explicit_env "$@"
}
