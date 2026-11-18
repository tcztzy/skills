#!/usr/bin/env python3
"""Run repository and bundled-skill unittest suites in separate interpreters.

Use the release inventory so private or retired skills do not enter the suite.
The core selection covers repository tooling, including Codex skill metrics.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from generate_claude_marketplace import distribution_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", action="store_true", help="run only repository tooling tests")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    files = distribution_files(root)
    suites = set()
    for path in files:
        if not path.match("test_*.py"):
            continue
        if path.is_relative_to("scripts/tests") or path.is_relative_to(".codex/skill-metrics"):
            suites.add(path.parent)
        elif not args.core and len(path.parts) == 4 and path.parts[0] == "skills" and path.parts[2] == "tests":
            if path.parents[1] / "SKILL.md" in files:
                suites.add(path.parent)
    if not suites:
        parser.exit(1, "No test suites discovered.\n")
    failed = []
    for suite in sorted(suites):
        print(f"Running {suite.as_posix()}", flush=True)
        command = [sys.executable, "-m", "unittest", "discover", "-s", str(suite), "-v"]
        if subprocess.run(command, cwd=root).returncode:
            failed.append(suite.as_posix())
    if failed:
        print("Failed suites: " + ", ".join(failed), file=sys.stderr)
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
