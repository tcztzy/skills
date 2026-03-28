#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def _relative_to_repo(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _list_files(root: Path, repo_root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(
        _relative_to_repo(repo_root, path)
        for path in root.rglob("*")
        if path.is_file()
    )


def summarize_run(
    run_dir: Path,
    repo_root: Path,
    mode: str,
    task: str,
    result_file: Path | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "mode": mode,
        "task": task,
        "status": "success",
        "run_dir": _relative_to_repo(repo_root, run_dir),
        "artifacts": {
            "workflow_spec": _relative_to_repo(
                repo_root, run_dir / "workflow_spec.json"
            ),
            "shared": _list_files(run_dir / "shared", repo_root),
            "chunked_extraction": _list_files(
                run_dir / "chunked_extraction", repo_root
            ),
            "candidates": {},
            "polish": _list_files(run_dir / "polish", repo_root),
            "refine": _list_files(run_dir / "refine", repo_root),
            "evaluation": _list_files(run_dir / "evaluation", repo_root),
        },
        "notes": [],
    }

    candidates_dir = run_dir / "candidates"
    if candidates_dir.exists():
        for candidate_dir in sorted(
            path for path in candidates_dir.iterdir() if path.is_dir()
        ):
            summary["artifacts"]["candidates"][candidate_dir.name] = _list_files(
                candidate_dir, repo_root
            )

    if result_file is not None and result_file.exists():
        result_data = _load_json(result_file)
        if "status" in result_data:
            summary["status"] = result_data["status"]
        if isinstance(result_data.get("notes"), list):
            summary["notes"] = list(result_data["notes"])
        if result_data.get("artifacts"):
            summary["artifacts"]["reported"] = result_data["artifacts"]

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize a Paper Visualizer workflow run directory."
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--result-file", default="")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir).resolve()
    repo_root = Path(args.repo_root).resolve()
    result_file = Path(args.result_file).resolve() if args.result_file else None
    summary = summarize_run(run_dir, repo_root, args.mode, args.task, result_file)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
