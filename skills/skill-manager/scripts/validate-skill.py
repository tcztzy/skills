#!/usr/bin/env python3
"""Compatibility CLI wrapper for validate_skill.py."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_skill import main  # type: ignore  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
