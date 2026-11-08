#!/usr/bin/env python3
"""Read-only, bounded evidence checks. Python 3.11+, standard library and Git only."""

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit


MANIFEST_FIELDS = {
    "package.json": (
        "dependencies", "devDependencies", "peerDependencies", "optionalDependencies",
        "scripts", "bin", "exports", "files", "engines", "packageManager",
    ),
    "pyproject.toml": (
        "project.dependencies", "project.optional-dependencies", "project.requires-python",
        "project.scripts", "project.gui-scripts", "project.entry-points", "project.dynamic",
        "build-system", "tool.poetry",
    ),
    "Cargo.toml": (
        "dependencies", "dev-dependencies", "build-dependencies", "target", "features",
        "workspace.dependencies", "package", "bin", "lib",
    ),
}
UNPARSED_NAMES = {
    "requirements.txt", "setup.py", "setup.cfg", "Pipfile", "Pipfile.lock",
    "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock",
    "Dockerfile", "Containerfile", "Makefile", "flake.nix", "flake.lock",
    "environment.yml", "environment.yaml", "go.mod", "go.sum", "Gemfile",
    "composer.json", "pom.xml", "build.gradle", "build.gradle.kts",
}
TEMP_PARTS = {
    "tmp", "temp", "build", "dist", "target", "node_modules", "__pycache__",
    ".pytest_cache", ".cache",
}
MISSING = object()


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        # Git errors can contain configuration or content. Do not echo stderr.
        raise ValueError(f"git {args[0]} failed; inspect the repository directly")
    return result.stdout


def changed_paths(root: Path, layer: str, *revisions: str) -> list[dict[str, str]]:
    raw = git(root, "diff", "--no-ext-diff", "--no-textconv", "--no-renames",
              "--name-status", "-z", *revisions, "--")
    parts = raw.decode("utf-8", errors="surrogateescape").split("\0")[:-1]
    if len(parts) % 2:
        raise ValueError("unexpected Git path report; inspection incomplete")
    return [{"layer": layer, "change": parts[i], "path": parts[i + 1]}
            for i in range(0, len(parts), 2)]


def field_value(data: dict, field: str) -> object:
    value = data
    for part in field.split("."):
        if not isinstance(value, dict) or part not in value:
            return MISSING
        value = value[part]
    return value


def parse_manifest(data: bytes | None, name: str) -> dict:
    if data is None:
        return {}
    text = data.decode("utf-8")
    parsed = json.loads(text) if name == "package.json" else tomllib.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("manifest root is not a mapping")
    return parsed


def inspect_repo(repo: Path, base: str) -> tuple[dict, int]:
    if not base.strip():
        raise ValueError("a nonempty explicit baseline is required")
    root = Path(git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    head = git(root, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    baseline = git(root, "rev-parse", "--verify", "--end-of-options",
                   f"{base}^{{commit}}").decode().strip()
    try:
        git(root, "merge-base", "--is-ancestor", baseline, head)
    except ValueError:
        raise ValueError("the baseline is not a verified ancestor of HEAD") from None

    changes = changed_paths(root, "committed", baseline, head)
    changes += changed_paths(root, "staged", "--cached", head)
    changes += changed_paths(root, "unstaged")
    changes += [{"layer": "untracked", "change": "?", "path": p}
                for p in git(root, "ls-files", "--others", "--exclude-standard", "-z")
                .decode("utf-8", errors="surrogateescape").split("\0") if p]
    errors, warnings, unknowns, manifests = [], [], [], []
    for entry in changes:
        path, layer, change = entry["path"], entry["layer"], entry["change"]
        local = Path(path)
        if change == "U":
            errors.append({**entry, "category": "unresolved_merge"})
            continue
        if change != "D":
            if (set(local.parts) & TEMP_PARTS or local.suffix in {".log", ".tmp", ".bak", ".pyc"}
                    or local.name == ".DS_Store"):
                warnings.append({**entry, "category": "possible_temporary_or_build_artifact"})
            if (local.name == ".env" or local.name.startswith(".env.")
                    or local.name in {"id_rsa", "id_ed25519"}
                    or local.suffix in {".pem", ".key"}):
                warnings.append({**entry, "category": "possibly_sensitive_filename"})

        if local.name in MANIFEST_FIELDS:
            warnings.append({**entry, "category": "dependency_or_distribution_manifest_changed"})
            # Symlink contents are link targets, not manifest bytes; do not follow them.
            refs = {"committed": (baseline, head), "staged": (head, ""),
                    "unstaged": ("", None), "untracked": (None, None)}[layer]
            snapshots = []
            unsupported = False
            for index, ref in enumerate(refs):
                absent = (index == 0 and change in {"A", "?"}) or (index == 1 and change == "D")
                if absent:
                    snapshots.append(None)
                elif ref is None:
                    if (root / path).is_symlink():
                        unsupported = True
                        break
                    snapshots.append((root / path).read_bytes())
                else:
                    mode = (git(root, "ls-files", "--stage", "-z", "--", path)
                            if ref == "" else git(root, "ls-tree", "-z", ref, "--", path))
                    if mode.startswith(b"120000 "):
                        unsupported = True
                        break
                    snapshots.append(git(root, "cat-file", "blob", f"{ref}:{path}"))
            if unsupported:
                unknowns.append({**entry, "category": "symlink_manifest_not_interpreted"})
                continue
            try:
                before, after = [parse_manifest(raw, local.name) for raw in snapshots]
            except (ValueError, UnicodeError):
                errors.append({**entry, "category": "invalid_manifest_syntax"})
                continue
            fields = [field for field in MANIFEST_FIELDS[local.name]
                      if field_value(before, field) != field_value(after, field)]
            manifests.append({**entry, "changed_supported_fields": fields})
        elif (local.name in UNPARSED_NAMES or local.suffix == ".lock"
              or local.match("requirements*.txt") or local.match("environment*.yml")
              or local.match("environment*.yaml") or local.match("Dockerfile.*")
              or local.match("install*.sh") or path.startswith(".github/workflows/")):
            warnings.append({**entry, "category": "possible_installation_configuration_changed"})
            unknowns.append({**entry, "category": "manifest_or_configuration_not_interpreted"})

    report = {
        "check": "repo", "status": "findings" if errors else "inspection_complete",
        "facts": {"repository": str(root), "baseline": baseline, "head": head,
                  "changes": changes, "manifest_comparisons": manifests},
        "warnings": warnings, "unknowns": unknowns, "errors": errors,
        "limits": ["local non-atomic snapshot; no remote state or ignored files",
                   "only listed manifest fields and recognized configuration filenames",
                   "no file contents or dependency values printed; no secret-content scan",
                   "no installation, user acceptance, architecture, or authorization validation"],
    }
    return report, 1 if errors else 0


def inspect_skill(folder: Path) -> tuple[dict, int]:
    root = folder.resolve()
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    errors, unknowns = [], []
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    fields = {}
    if not match:
        errors.append({"path": "SKILL.md", "category": "missing_or_unterminated_frontmatter"})
    else:
        for line in match[1].splitlines():
            item = re.fullmatch(r"(name|description): ([^\n]+)", line)
            if not item:
                unknowns.append({"path": "SKILL.md", "category": "unsupported_frontmatter_syntax"})
                continue
            key, value = item.groups()
            if (value[0] in "[]{}|>&*!%@\"'`" or ": " in value or " #" in value):
                unknowns.append({"path": "SKILL.md", "category": "unsupported_frontmatter_scalar"})
                continue
            if key in fields:
                errors.append({"path": "SKILL.md", "category": "duplicate_frontmatter_key"})
            fields[key] = value.strip()
        if not unknowns:
            name = fields.get("name", "")
            if (not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64
                    or name != root.name):
                errors.append({"path": "SKILL.md", "category": "invalid_name_or_directory_mismatch"})
            description = fields.get("description", "")
            if not description or len(description) > 1024 or re.search(r"[<>]", description):
                errors.append({"path": "SKILL.md", "category": "invalid_description"})

    checked_links = []
    for document in sorted(root.rglob("*.md")):
        relative = str(document.relative_to(root))
        if document.is_symlink():
            unknowns.append({"path": relative, "category": "symlink_document_not_interpreted"})
            continue
        body = re.sub(r"(?ms)^```[^\n]*\n.*?^```\s*$", "", document.read_text(encoding="utf-8"))
        for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", body):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc:
                continue
            destination = (document.parent / unquote(parsed.path)).resolve() if parsed.path else document
            if not destination.is_relative_to(root):
                errors.append({"path": relative, "category": "reference_outside_skill"})
            elif not destination.exists():
                errors.append({"path": relative, "target": parsed.path, "category": "missing_local_reference"})
            else:
                checked_links.append({"path": relative, "target": parsed.path})
            if parsed.fragment:
                unknowns.append({"path": relative, "category": "link_fragment_not_checked"})

    code = 1 if errors else 2 if unknowns else 0
    return {
        "check": "skill", "status": "findings" if errors else "incomplete" if unknowns else "inspection_complete",
        "facts": {"directory": str(root), "checked_local_file_links": checked_links},
        "errors": errors, "warnings": [], "unknowns": unknowns,
        "limits": ["single-line plain name/description frontmatter; inline relative file links",
                   "no behavioral quality, design, or authorization validation"],
    }, code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    repo = commands.add_parser("repo", help="inspect local Git changes from an explicit baseline")
    repo.add_argument("--repo", type=Path, required=True)
    repo.add_argument("--base", required=True)
    skill = commands.add_parser("skill", help="validate this skill's supported metadata and links")
    skill.add_argument("folder", type=Path)
    args = parser.parse_args()
    try:
        report, code = (inspect_repo(args.repo, args.base) if args.command == "repo"
                        else inspect_skill(args.folder))
    except (OSError, ValueError) as error:
        # Report categories without echoing file contents or potentially sensitive diagnostics.
        report, code = {"check": args.command, "status": "incomplete",
                        "errors": [{"category": type(error).__name__,
                                    "detail": "unable to inspect requested files or Git baseline"}]}, 2
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
