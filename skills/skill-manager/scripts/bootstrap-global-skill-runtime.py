#!/usr/bin/env python3
"""Bootstrap the shared WSL2 runtime registry for all installed Codex skills."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from runtime_registry import build_registry, refresh_helper_path, registry_path, resolve_runtime_root, shell_init_path  # type: ignore  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap shared WSL2 runtimes for installed Codex skills")
    parser.add_argument("--runtime-root", default=None)
    parser.add_argument("--domain", action="append", dest="domains", default=None)
    parser.add_argument("--no-install", action="store_true")
    args = parser.parse_args(argv)

    registry = build_registry(
        runtime_root=args.runtime_root,
        install_missing=not args.no_install,
        domains=set(args.domains) if args.domains else None,
    )
    root = resolve_runtime_root(args.runtime_root)
    print(json.dumps({
        "runtime_root": str(root),
        "registry_path": str(registry_path(root)),
        "shell_init_path": str(shell_init_path(root)),
        "refresh_helper_path": str(refresh_helper_path()),
        "domains": {name: info.get("status") for name, info in registry.get("domains", {}).items()},
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
