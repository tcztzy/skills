#!/usr/bin/env bash
set -euo pipefail

section() {
  printf '\n== %s ==\n' "$1"
}

section system
uname -a || true
if command -v sw_vers >/dev/null 2>&1; then
  sw_vers || true
fi
if [[ -r /etc/os-release ]]; then
  sed -n '1,40p' /etc/os-release || true
fi

if ! command -v nix >/dev/null 2>&1; then
  section nix
  echo "nix: not found in PATH"
  exit 0
fi

section nix
nix --version || true
printf 'executable: %s\n' "$(command -v nix)"

section "nix config (filtered)"
config_output=""
if config_output=$(nix config show 2>/dev/null); then
  :
elif config_output=$(nix show-config 2>/dev/null); then
  echo "using legacy 'nix show-config' compatibility fallback"
else
  echo "configuration inspection unavailable"
fi

if [[ -n "$config_output" ]]; then
  printf '%s\n' "$config_output" |
    grep -E '^(experimental-features|extra-experimental-features|use-xdg-base-directories|substituters|trusted-public-keys|sandbox|trusted-users|trusted-substituters|system|require-sigs)[[:space:]]*=' ||
    true
fi

section "nix config check"
if nix config check --help >/dev/null 2>&1; then
  nix config check 2>&1 || true
else
  echo "nix config check: unavailable in this Nix version"
fi

section "nix registry"
nix registry list 2>/dev/null || true

section "nix store"
nix store info 2>/dev/null || true

section "project context"
printf 'cwd: %s\n' "$PWD"
if [[ -f flake.nix ]]; then
  echo "flake.nix: present"
  if [[ -f flake.lock ]]; then
    echo "flake.lock: present"
  else
    echo "flake.lock: absent"
  fi
else
  echo "flake.nix: absent"
fi

section done
