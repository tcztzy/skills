#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["tiktoken==0.12.0"]
# ///
"""Measure source size and observed internal dependency structure without execution.

CLI main selects nonignored files (or an explicit walk), counts exact per-file
cl100k_base tokens, extracts Python imports with AST or consumes a provenance-bearing
graph, and emits a summary plus optional JSON/baseline deltas. Graph edges point
from dependent to dependency. Module ownership collapses imported item graphs.
Only the requested report is written; target modules are never imported. Invalid
inputs fail with exit 2; unreadable files/unsupported graph coverage remain explicit
missing data. Structural metrics describe the observed static graph, not behavior,
overengineering, fault detection, or collaboration effort.
"""

import argparse
import ast
from collections import deque
from fnmatch import fnmatchcase
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ENCODING = "cl100k_base"
SOURCE = {".py", ".rs", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
DOCS = {".md", ".rst", ".txt", ".adoc"}
CONFIG = {".toml", ".json", ".yaml", ".yml", ".ini", ".cfg", ".sh"}
ROLES = ("production", "tests", "documentation", "configuration")
EXCLUDED = {
    ".git", ".venv", "venv", "node_modules", "target", "dist", "build",
    "vendor", "third_party", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".next",
}


def graph_metrics(adjacency: dict[str, set[str]]) -> dict[str, Any]:
    """Compute exact reflexive reachability and SCCs via an iterative condensation DAG.

    SCC bitsets use O(N²) worst-case bits, avoiding recursive DFS and dense Python
    object matrices. Empty-graph ratios are undefined (None). An explicit self edge
    is a cycle; the reflexive diagonal alone is not.
    """
    names = sorted(adjacency)
    if any(target not in adjacency for edges in adjacency.values() for target in edges):
        raise ValueError("Graph edge endpoint is not in nodes")
    reverse: dict[str, set[str]] = {node: set() for node in names}
    for node, targets in adjacency.items():
        for target in targets:
            reverse[target].add(node)
    visited: set[str] = set()
    order: list[str] = []
    for start in names:
        stack = [(start, False)]
        while stack:
            node, finish = stack.pop()
            if finish:
                order.append(node)
            elif node not in visited:
                visited.add(node)
                stack.append((node, True))
                stack.extend((target, False) for target in sorted(adjacency[node], reverse=True))
    groups: list[list[str]] = []
    component: dict[str, int] = {}
    for start in reversed(order):
        if start in component:
            continue
        group: list[str] = []
        stack2 = [start]
        component[start] = len(groups)
        while stack2:
            node = stack2.pop()
            group.append(node)
            for target in sorted(reverse[node]):
                if target not in component:
                    component[target] = len(groups)
                    stack2.append(target)
        groups.append(sorted(group))
    dag: list[set[int]] = [set() for _ in groups]
    incoming = [0] * len(groups)
    for node, targets in adjacency.items():
        source = component[node]
        for target in targets:
            dest = component[target]
            if dest != source and dest not in dag[source]:
                dag[source].add(dest)
                incoming[dest] += 1
    queue = deque(i for i, count in enumerate(incoming) if not count)
    topo: list[int] = []
    while queue:
        source = queue.popleft()
        topo.append(source)
        for dest in sorted(dag[source]):
            incoming[dest] -= 1
            if not incoming[dest]:
                queue.append(dest)
    indexes = {node: i for i, node in enumerate(names)}
    bits = [sum(1 << indexes[node] for node in group) for group in groups]
    outward = bits.copy()
    inward = bits.copy()
    for source in reversed(topo):
        for dest in dag[source]:
            outward[source] |= outward[dest]
    for source in topo:
        for dest in dag[source]:
            inward[dest] |= inward[source]
    cycles = [group for group in groups if len(group) > 1 or group[0] in adjacency[group[0]]]
    cycles.sort(key=lambda group: (-len(group), group))
    n = len(names)
    pairs = sum(len(group) * outward[i].bit_count() for i, group in enumerate(groups))
    hotspots = [{
        "node": node,
        "direct_fan_in": len(reverse[node] - {node}),
        "direct_fan_out": len(adjacency[node] - {node}),
        "visible_fan_in": inward[component[node]].bit_count(),
        "visible_fan_out": outward[component[node]].bit_count(),
    } for node in names]
    hotspots.sort(key=lambda row: (-row["visible_fan_in"], -row["visible_fan_out"], row["node"]))
    outgoing_hotspots = sorted(hotspots, key=lambda row: (-row["visible_fan_out"], -row["visible_fan_in"], row["node"]))
    return {
        "nodes": n, "edges": sum(map(len, adjacency.values())),
        "reachable_pairs": pairs, "pc": pairs / (n * n) if n else None,
        "cyclic_nodes": sum(map(len, cycles)),
        "cyclic_ratio": sum(map(len, cycles)) / n if n else None,
        "largest_cycle_size": len(cycles[0]) if cycles else 0,
        "largest_cycle": cycles[0] if cycles else [], "cycles": cycles,
        "hotspots": hotspots[:10], "outgoing_hotspots": outgoing_hotspots[:10],
    }


def select_files(root: Path, selection: str, excludes: list[str], automatic: set[Path]) -> tuple[list[str], dict[str, Any]]:
    """Inventory selected files and exclusions; never follow directory symlinks."""
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "."],
        capture_output=True, check=False,
    ) if selection == "git" else None
    if result is not None and result.returncode:
        raise ValueError("Git selection requires a checkout; use --selection walk for a plain directory")
    omitted: list[dict[str, str]] = []
    if result is not None:
        candidates = sorted(set(os.fsdecode(result.stdout).split("\0")) - {""})
    else:
        candidates = []
        for current, dirs, files in os.walk(root, followlinks=False):
            for directory in dirs.copy():
                path = Path(current) / directory
                relative = path.relative_to(root).as_posix()
                if directory in EXCLUDED or path.is_symlink() or any(fnmatchcase(relative, p) for p in excludes):
                    dirs.remove(directory)
                    omitted.append({"path": relative + "/", "reason": "excluded directory or symlink"})
            candidates.extend((Path(current) / name).relative_to(root).as_posix() for name in files)
    selected: list[str] = []
    for relative in sorted(candidates):
        path = root / relative
        parts = Path(relative).parts
        reason = None
        if path.resolve() in automatic:
            reason = "report/baseline/graph input"
        elif any(part in EXCLUDED for part in parts) or any(fnmatchcase(relative, p) for p in excludes):
            reason = "default or explicit exclusion"
        elif any((root / Path(*parts[:i])).is_symlink() for i in range(1, len(parts) + 1)):
            reason = "symlink"
        elif path.name.startswith(".env") or path.suffix.lower() not in SOURCE | DOCS | CONFIG:
            reason = "unselected type or environment secrets"
        if reason:
            omitted.append({"path": relative, "reason": reason})
        else:
            selected.append(relative)
    return selected, {
        "method": selection,
        "default_excluded_directories": sorted(EXCLUDED),
        "excluded": sorted(omitted, key=lambda row: row["path"]),
        "git_ignored": "omitted by git --exclude-standard; not individually enumerated" if result else "not consulted",
    }


def file_role(relative: str, overrides: list[tuple[str, str]]) -> str:
    """Assign one whole-file role; the last explicit glob override wins."""
    for pattern, role in reversed(overrides):
        if fnmatchcase(relative, pattern):
            return role
    path = Path(relative)
    if path.suffix.lower() in DOCS:
        return "documentation"
    if path.suffix.lower() in CONFIG:
        return "configuration"
    if any(part.lower() in {"test", "tests", "__tests__"} for part in path.parts[:-1]) or path.name.startswith("test_") or path.stem.endswith(("_test", ".test", ".spec")) or path.name == "conftest.py":
        return "tests"
    return "production"


def python_graph(root: Path, texts: dict[str, str], roots: list[str]) -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, Any]]:
    """Resolve static local imports against explicit source roots, without imports.

    Include package initialization and imports inside functions/TYPE_CHECKING.
    Dynamic imports and runtime sys.path changes are not resolved.
    """
    locations: dict[str, set[str]] = {}
    module_paths: dict[str, str] = {}
    for relative in texts:
        if Path(relative).suffix != ".py":
            continue
        path = root / relative
        candidates = [base for base in roots if path.is_relative_to(root / base)]
        if not candidates:
            continue
        base = max(candidates, key=lambda value: len(Path(value).parts))
        parts = list(path.relative_to(root / base).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        name = ".".join(parts) or root.name
        if name in locations:
            raise ValueError(f"Python module collision: {name}; choose non-overlapping import identities")
        locations[name] = {relative}
        module_paths[relative] = name
    adjacency: dict[str, set[str]] = {name: set() for name in locations}
    missing: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    dynamic: list[dict[str, Any]] = []
    for relative, source in module_paths.items():
        try:
            tree = ast.parse(texts[relative], filename=relative)
        except SyntaxError as exc:
            missing.append({"path": relative, "reason": f"syntax error at line {exc.lineno}: {exc.msg}"})
            continue
        package = source if Path(relative).name == "__init__.py" else source.rpartition(".")[0]
        for node in ast.walk(tree):
            imports: list[str] = []
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    parent = package.split(".") if package else []
                    if node.level > len(parent):
                        unresolved.append({"path": relative, "line": node.lineno, "import": "relative import beyond source root"})
                        continue
                    prefix = ".".join(parent[:len(parent) - node.level + 1])
                    base = ".".join(part for part in (prefix, node.module) if part)
                else:
                    base = node.module or ""
                imports.append(base)
                imports.extend(f"{base}.{alias.name}" for alias in node.names if alias.name != "*" and f"{base}.{alias.name}" in locations)
            elif isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Name) and node.func.id == "__import__"
                or isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"
            ):
                dynamic.append({"path": relative, "line": node.lineno})
            for imported in imports:
                pieces = imported.split(".")
                found = False
                for size in range(1, len(pieces) + 1):
                    target = ".".join(pieces[:size])
                    if target in locations:
                        found = True
                        if source != target:
                            adjacency[source].add(target)
                if not found:
                    unresolved.append({"path": relative, "line": node.lineno, "import": imported})
    return adjacency, locations, {
        "extractor": {"name": "python-ast", "version": "1", "python": sys.version.split()[0]},
        "scope": "selected readable Python files under python_roots; internal static imports",
        "granularity": "module", "python_roots": roots,
        "parse_failures": missing, "external_or_unresolved_imports": unresolved,
        "dynamic_import_sites": dynamic,
        "limitations": ["Import-level graph, not call/data flow; optional and type-only imports included.",
                        "Dynamic imports, runtime sys.path changes, star re-export targets and namespace initialization are not modeled.",
                        "Whole-file roles: inline Rust/Python tests cannot be token-separated."],
    }


def load_graph(path: Path) -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, Any]]:
    """Load schema v1, collapse raw item owners, and deduplicate dependency edges."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1 or raw.get("granularity") not in {"module", "file"}:
        raise ValueError("Graph requires schema_version=1 and granularity=module or file")
    extractor = raw.get("extractor", {})
    if not isinstance(extractor, dict) or not all(isinstance(extractor.get(key), str) and extractor[key] for key in ("name", "version", "command")) or not isinstance(raw.get("scope"), str) or not raw["scope"]:
        raise ValueError("Graph requires scope and extractor name/version/command provenance")
    if not isinstance(raw.get("limitations"), list) or not isinstance(raw.get("unresolved"), list):
        raise ValueError("Graph requires explicit limitations and unresolved lists (empty if known empty)")
    if not isinstance(raw.get("nodes"), list) or not isinstance(raw.get("edges"), list):
        raise ValueError("Graph nodes and edges must be lists")
    if any(not isinstance(node, dict) for node in raw["nodes"]):
        raise ValueError("Graph nodes must be objects")
    locations: dict[str, set[str]] = {}
    owners: dict[str, str] = {}
    for node in raw["nodes"]:
        name = node["id"]
        owner = node.get("owner", name)
        if not isinstance(name, str) or not name or name in owners or not isinstance(owner, str) or not owner:
            raise ValueError("Graph node IDs/owners must be nonempty strings and raw IDs unique")
        if node.get("kind") not in {"item", raw["granularity"]}:
            raise ValueError("Node kind must match granularity, or be an item with a module owner")
        if node.get("kind") == "item" and ("owner" not in node or raw["granularity"] != "module"):
            raise ValueError("Item nodes require explicit module owners and module granularity")
        files = node["files"]
        if not isinstance(files, list) or any(not isinstance(file, str) or Path(file).is_absolute() or ".." in Path(file).parts for file in files):
            raise ValueError("Graph files must be root-relative paths without '..'")
        owners[name] = owner
        locations.setdefault(owner, set()).update(files)
    module_ids = {node["id"] for node in raw["nodes"] if node["kind"] == raw["granularity"]}
    if any(owner not in module_ids or owners[owner] != owner for owner in owners.values()):
        raise ValueError("Every owner must have an explicit node of the declared granularity")
    adjacency: dict[str, set[str]] = {owner: set() for owner in locations}
    intra = 0
    for source, target in raw["edges"]:
        if source not in owners or target not in owners:
            raise ValueError(f"Graph edge has unknown endpoint: {source} -> {target}")
        a, b = owners[source], owners[target]
        if a == b and (source != target or source != a):
            intra += 1
        else:
            adjacency[a].add(b)
    return adjacency, locations, {
        "extractor": extractor, "scope": raw["scope"], "granularity": raw["granularity"],
        "limitations": raw["limitations"], "unresolved": raw["unresolved"],
        "raw_nodes": len(owners), "collapsed_intra_module_edges": intra,
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def entry_closure(entries: list[str], adjacency: dict[str, set[str]], locations: dict[str, set[str]], files: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Measure the union of reachable files once, including the entry modules."""
    if not entries:
        return None
    unknown = set(entries) - adjacency.keys()
    if unknown:
        raise ValueError(f"Unknown entry nodes: {', '.join(sorted(unknown))}")
    seen: set[str] = set()
    stack = entries.copy()
    while stack:
        node = stack.pop()
        if node not in seen:
            seen.add(node)
            stack.extend(adjacency[node] - seen)
    paths = set().union(*(locations[node] for node in seen))
    unmapped = sorted(node for node in seen if not locations[node])
    missing = sorted(path for path in paths if path not in files or files[path]["tokens"] is None)
    known = sum(files[path]["tokens"] for path in paths if path in files and files[path]["tokens"] is not None)
    return {"entries": sorted(set(entries)), "nodes": len(seen), "files": sorted(paths),
            "tokens": None if unmapped or missing else known, "known_tokens": known,
            "missing_files": missing, "unmapped_nodes": unmapped,
            "interpretation": "whole reachable file text, deduplicated; not a minimal LLM context"}


def compare_reports(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compare compatible measurement policies; unknown inputs produce null deltas."""
    mismatches = [key for key in after["policy"] if before.get("policy", {}).get(key) != after["policy"][key]]
    if before.get("schema_version") != after["schema_version"]:
        mismatches.append("schema_version")
    delta: dict[str, Any] = {}
    for role in ROLES:
        old = before.get("size", {}).get(role, {}).get("tokens")
        new = after["size"][role]["tokens"]
        delta[f"tokens.{role}"] = new - old if not mismatches and old is not None and new is not None else None
    graph_known = not mismatches and not before.get("graph", {}).get("missing") and not after["graph"]["missing"]
    for key in ("nodes", "edges", "reachable_pairs", "pc", "cyclic_nodes", "cyclic_ratio", "largest_cycle_size"):
        old = before.get("graph", {}).get("metrics", {}).get(key)
        new = after["graph"]["metrics"][key]
        delta[f"graph.{key}"] = new - old if graph_known and old is not None and new is not None else None
    old_entry = before.get("entry_closure") or {}
    new_entry = after.get("entry_closure") or {}
    old, new = old_entry.get("tokens"), new_entry.get("tokens")
    delta["entry_closure.tokens"] = new - old if graph_known and old is not None and new is not None else None
    return {"compatible_policy": not mismatches, "mismatches": mismatches, "delta_after_minus_before": delta,
            "requirements_equivalence": "not verified by measurement; requires the same acceptance evidence",
            "file_changes": {"added": sorted(after["files"].keys() - before.get("files", {}).keys()),
                             "removed": sorted(before.get("files", {}).keys() - after["files"].keys())}}


def measure(args: argparse.Namespace) -> dict[str, Any]:
    """Build a deterministic report, retaining scope, exact counts and missing data."""
    import tiktoken

    root = args.root.resolve()
    if not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")
    roots = sorted(set(args.python_root or ["."]))
    if any(Path(base).is_absolute() or ".." in Path(base).parts or not (root / base).is_dir() for base in roots):
        raise ValueError("--python-root must name existing root-relative directories")
    overrides: list[tuple[str, str]] = []
    for value in args.role:
        pattern, separator, role = value.rpartition("=")
        if not separator or not pattern or role not in ROLES:
            raise ValueError(f"--role requires GLOB={'|'.join(ROLES)}")
        overrides.append((pattern, role))
    automatic = {path.resolve() for path in (args.json, args.baseline, args.graph) if path}
    selected, selection = select_files(root, args.selection, args.exclude, automatic)
    encoder = tiktoken.get_encoding(ENCODING)
    files: dict[str, dict[str, Any]] = {}
    texts: dict[str, str] = {}
    for relative in selected:
        row: dict[str, Any] = {"role": file_role(relative, overrides), "tokens": None, "bytes": None, "lines": None}
        try:
            data = (root / relative).read_bytes()
            # Decode strictly: no replacement characters and no newline normalization.
            text = data.decode("utf-8")
            texts[relative] = text
            row.update(tokens=len(encoder.encode_ordinary(text)), bytes=len(data),
                       lines=len(text.splitlines()), sha256=hashlib.sha256(data).hexdigest())
        except (OSError, UnicodeError) as exc:
            row["missing"] = str(exc)
        files[relative] = row
    size: dict[str, Any] = {}
    for role in ROLES:
        rows = [row for row in files.values() if row["role"] == role]
        missing = [name for name, row in files.items() if row["role"] == role and row["tokens"] is None]
        known = sum(row["tokens"] for row in rows if row["tokens"] is not None)
        size[role] = {"files": len(rows), "tokens": None if missing else known,
                      "known_tokens": known, "missing_files": missing,
                      "bytes": None if missing else sum(row["bytes"] for row in rows),
                      "lines": None if missing else sum(row["lines"] for row in rows)}
    if args.graph:
        adjacency, locations, metadata = load_graph(args.graph)
    else:
        unsupported = [path for path in selected if Path(path).suffix in SOURCE - {".py"}]
        if unsupported:
            raise ValueError("Rust/TypeScript/JavaScript source requires --graph; see references/measurement.md")
        adjacency, locations, metadata = python_graph(root, texts, roots)
    mapped = set().union(*locations.values()) if locations else set()
    source_files = {path for path in selected if Path(path).suffix in SOURCE}
    missing_graph = {
        "selected_source_files_unmapped": sorted(source_files - mapped),
        "mapped_files_unavailable": sorted(path for path in mapped if path not in texts),
        "nodes_without_files": sorted(node for node, paths in locations.items() if not paths),
        "parse_failures": metadata.get("parse_failures", []),
        "unresolved": metadata.get("unresolved", []) + metadata.get("dynamic_import_sites", []),
    }
    missing_graph = {key: value for key, value in missing_graph.items() if value}
    graph = {"metadata": metadata, "missing": missing_graph,
             "coverage": "partial" if missing_graph else "observed static scope (see limitations)",
             "node_files": {node: sorted(paths) for node, paths in sorted(locations.items())},
             "edges": [[node, target] for node in sorted(adjacency) for target in sorted(adjacency[node])],
             "metrics": graph_metrics(adjacency)}
    policy = {
        "encoding": ENCODING, "tiktoken": version("tiktoken"), "selection": args.selection,
        "exclude": sorted(set(args.exclude)), "default_exclusions": sorted(EXCLUDED),
        "extensions": sorted(SOURCE | DOCS | CONFIG), "role_overrides": args.role,
        "python_roots": roots, "granularity": metadata["granularity"],
        "extractor": metadata["extractor"], "graph_scope": metadata["scope"],
        "graph_limitations": metadata["limitations"], "entries": sorted(set(args.entry)),
        "role_rule_version": 1, "metric_version": 1,
    }
    report = {"schema_version": 1, "root": str(root), "policy": policy,
              "selection": selection, "size": size, "files": files, "graph": graph,
              "entry_closure": entry_closure(args.entry, adjacency, locations, files),
              "unmeasured": {"fault_detection": None, "collaboration_cost": None, "avoidable_cost": None}}
    if args.baseline:
        report["comparison"] = compare_reports(json.loads(args.baseline.read_text(encoding="utf-8")), report)
    return report


def summary(report: dict[str, Any]) -> str:
    """Render core values and gaps; null is printed as unknown, not zero."""
    lines = [f"Project: {report['root']}", f"Tokens: {ENCODING}, exact per-file sum; selection={report['policy']['selection']}"]
    for role, row in report["size"].items():
        value = row["tokens"] if row["tokens"] is not None else f"unknown (known {row['known_tokens']})"
        lines.append(f"  {role}: {row['files']} files, {value} tokens")
    graph = report["graph"]
    metrics = graph["metrics"]
    pc = f"{metrics['pc']:.6f}" if metrics["pc"] is not None else "undefined (empty graph)"
    lines.append(f"Graph ({graph['metadata']['granularity']}): N={metrics['nodes']}, E={metrics['edges']}, reachable pairs={metrics['reachable_pairs']}, PC={pc}")
    ratio = f"{metrics['cyclic_ratio']:.6f}" if metrics["cyclic_ratio"] is not None else "undefined"
    lines.append(f"Cycles: {metrics['cyclic_nodes']} nodes, ratio={ratio}, largest={metrics['largest_cycle_size']}")
    lines.append(f"Coverage: {graph['coverage']}")
    for key, rows in graph["missing"].items():
        lines.append(f"  Missing {key}: {len(rows)} (details in JSON)")
    for row in metrics["hotspots"][:5]:
        lines.append(f"  {row['node']}: direct in/out={row['direct_fan_in']}/{row['direct_fan_out']}, visible in/out={row['visible_fan_in']}/{row['visible_fan_out']}")
    if metrics["outgoing_hotspots"]:
        lines.append("  Largest visible fan-out: " + ", ".join(f"{row['node']}={row['visible_fan_out']}" for row in metrics["outgoing_hotspots"][:5]))
    if report["entry_closure"]:
        entry = report["entry_closure"]
        lines.append(f"Entry union: {entry['nodes']} nodes, {len(entry['files'])} files, tokens={entry['tokens'] if entry['tokens'] is not None else 'unknown'}")
    if "comparison" in report:
        comparison = report["comparison"]
        lines.append(f"Baseline compatible: {comparison['compatible_policy']}; mismatches={comparison['mismatches']}")
        lines.append("Deltas (after - before; null=unknown): " + json.dumps(comparison["delta_after_minus_before"], sort_keys=True))
    lines.append("Interpretation: structural proxies only; requirements equivalence, fault detection and collaboration costs are unmeasured.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path, help="Project directory; measured read-only")
    parser.add_argument("--selection", choices=("git", "walk"), default="git", help="git: tracked + nonignored untracked; walk: explicit filesystem inventory")
    parser.add_argument("--python-root", action="append", help="Root-relative Python import root; repeatable, default '.'")
    parser.add_argument("--exclude", action="append", default=[], help="Exclude root-relative fnmatch glob; repeatable")
    parser.add_argument("--role", action="append", default=[], help="Whole-file override GLOB=production|tests|documentation|configuration; repeatable")
    parser.add_argument("--graph", type=Path, help="Provenance-bearing schema v1 graph; replaces built-in Python extraction")
    parser.add_argument("--entry", action="append", default=[], help="Normalized node ID; repeat for a deduplicated union closure")
    parser.add_argument("--baseline", type=Path, help="Prior JSON report; delta is after minus before")
    parser.add_argument("--json", type=Path, help="Write complete JSON report (use outside the measured project)")
    args = parser.parse_args(argv)
    if args.json and args.json.resolve().is_relative_to(args.root.resolve()):
        parser.error("--json must be outside the measured project to preserve read-only measurement")
    if args.json and args.json.resolve() in {path.resolve() for path in (args.graph, args.baseline) if path}:
        parser.error("--json must not overwrite the graph or baseline")
    try:
        report = measure(args)
        if args.json:
            args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (ValueError, OSError, KeyError, TypeError, ImportError) as exc:
        parser.error(str(exc))
    print(summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
