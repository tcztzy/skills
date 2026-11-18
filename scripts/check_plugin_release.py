"""Check a candidate Codex plugin against its previous Git revision.

CI and release maintainers supply a base commit. Check the published skill files
and manifest for changes, enforce an increasing release version, and look for
callers of retired names. All operations read the checkout and Git history.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from generate_claude_marketplace import collect_plugins, read_external_plugins
from validate_plugin_metadata import validate_retired_skills


MANIFEST = ".codex-plugin/plugin.json"
COMPANIONS = ".claude-plugin/external-plugins.json"
VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")


def release_errors(root: Path, base: str) -> list[str]:
    """Compare bundled content and check that retired names have no active callers."""
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=root)

    commit = git("rev-parse", "--verify", "--end-of-options", base + "^{commit}").decode().strip()
    old_manifest = json.loads(git("show", f"{commit}:{MANIFEST}"))
    new_version = json.loads((root / MANIFEST).read_text(encoding="utf-8")).get("version")
    if not isinstance(new_version, str) or not VERSION.fullmatch(new_version):
        return [f"{MANIFEST} must declare a release version in MAJOR.MINOR.PATCH form."]
    # The first release used a timestamp as SemVer build metadata.
    old_version = old_manifest["version"].partition("+")[0]
    if not VERSION.fullmatch(old_version):
        return [f"Cannot compare the base version {old_manifest['version']!r}."]

    previous = set()
    for path in git("ls-tree", "-r", "--name-only", "-z", commit, "--", "skills").decode().split("\0"):
        if path.count("/") == 2 and path.endswith("/SKILL.md"):
            previous.add(Path(path).parent.name)
    current = {plugin["name"] for plugin in collect_plugins(root / "skills")}
    old_external = set()
    if git("ls-tree", "--name-only", commit, "--", COMPANIONS):
        old_external = {plugin["name"] for plugin in json.loads(git("show", f"{commit}:{COMPANIONS}"))}
    new_external = {plugin["name"] for plugin in read_external_plugins(root / COMPANIONS)}
    errors = validate_retired_skills(root, (previous | old_external) - (current | new_external))
    paths = [MANIFEST, COMPANIONS, *(f"skills/{name}" for name in sorted(previous | current))]
    changed = git("diff", "--name-only", "-z", commit, "--", *paths)
    added = git("ls-files", "--others", "--exclude-standard", "-z", "--", *paths)
    if (changed or added) and tuple(map(int, new_version.split("."))) <= tuple(map(int, old_version.split("."))):
        errors.append(
            f"Bundled plugin content changed since {commit[:12]} ({old_manifest['version']}). "
            f"Increase the Codex plugin version in {MANIFEST} (currently {new_version})."
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Previous release or base commit in this checkout")
    args = parser.parse_args()
    try:
        errors = release_errors(Path(__file__).resolve().parents[1], args.base)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Could not compare plugin releases: {exc}\n")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Plugin release version and retirement checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
