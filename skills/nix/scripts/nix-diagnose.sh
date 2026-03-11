#!/usr/bin/env bash
set -euo pipefail

echo "== system =="
uname -a || true
if command -v sw_vers >/dev/null 2>&1; then
  sw_vers || true
fi
if [ -f /etc/os-release ]; then
  cat /etc/os-release || true
fi

if ! command -v nix >/dev/null 2>&1; then
  echo "nix: not found in PATH"
  exit 0
fi

echo "== nix =="
nix --version || true

echo "== nix config (filtered) =="
if nix show-config >/dev/null 2>&1; then
  nix show-config 2>/dev/null | grep -E '^(experimental-features|extra-experimental-features|use-xdg-base-directories|substituters|trusted-public-keys|sandbox|trusted-users|trusted-substituters|system|require-sigs) ' || true
else
  echo "nix show-config: unavailable"
fi

echo "== nix registry =="
nix registry list 2>/dev/null || true

echo "== nix store =="
nix store info 2>/dev/null || true

echo "== done =="

