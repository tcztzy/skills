#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Any

MODE_DIRS = {
    "full": ["candidates"],
    "planner_critic": ["candidates"],
    "planner_stylist": ["candidates"],
    "planner": ["candidates"],
    "vanilla": ["candidates"],
    "chunked_extraction": ["chunked_extraction"],
    "polish": ["polish"],
    "refine": ["refine"],
    "evaluate": ["evaluation"],
}


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def _collect_paths(obj: Any) -> list[Path]:
    paths: list[Path] = []
    if isinstance(obj, str):
        if obj and not obj.startswith("ERROR:"):
            paths.append(Path(obj))
        return paths
    if isinstance(obj, list):
        for item in obj:
            paths.extend(_collect_paths(item))
        return paths
    if isinstance(obj, dict):
        for value in obj.values():
            paths.extend(_collect_paths(value))
        return paths
    return paths


def _resolve_artifact_paths(run_dir: Path, result_data: dict[str, Any]) -> list[Path]:
    raw_paths = _collect_paths(result_data.get("artifacts", {}))
    resolved: list[Path] = []
    for raw in raw_paths:
        if raw.is_absolute():
            resolved.append(raw)
            continue
        if str(raw).startswith("runs/"):
            resolved.append(run_dir.parent.parent / raw.relative_to("runs"))
            continue
        resolved.append(run_dir / raw)
    return resolved


def validate_run(
    run_dir: Path, mode: str, result_file: Path | None = None
) -> tuple[bool, str]:
    if not run_dir.exists():
        return False, f"Run directory not found: {run_dir}"
    if not run_dir.is_dir():
        return False, f"Run path is not a directory: {run_dir}"

    spec_path = run_dir / "workflow_spec.json"
    if not spec_path.exists():
        return False, f"Missing workflow spec: {spec_path}"

    for dirname in MODE_DIRS.get(mode, []):
        if not (run_dir / dirname).exists():
            return False, f"Missing mode directory: {run_dir / dirname}"

    result_data: dict[str, Any] | None = None
    if result_file is not None:
        if not result_file.exists():
            return False, f"Result file not found: {result_file}"
        result_data = _load_json(result_file)
        for artifact in _resolve_artifact_paths(run_dir, result_data):
            if not artifact.exists():
                return False, f"Missing artifact referenced by result: {artifact}"

    if mode == "chunked_extraction" and not (
        run_dir / "chunked_extraction" / "final_inputs.json"
    ).exists():
        return False, (
            "Chunked extraction run is missing "
            "chunked_extraction/final_inputs.json"
        )

    if mode == "evaluate":
        eval_dir = run_dir / "evaluation"
        expected = [
            "faithfulness.json",
            "conciseness.json",
            "readability.json",
            "aesthetics.json",
            "overall.json",
        ]
        missing = [name for name in expected if not (eval_dir / name).exists()]
        if missing:
            return False, f"Evaluation run is missing files: {', '.join(missing)}"

    return True, "Run is valid."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Paper Visualizer workflow run directory."
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--mode", required=True, choices=sorted(MODE_DIRS))
    parser.add_argument("--result-file", default="")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir).resolve()
    result_file = Path(args.result_file).resolve() if args.result_file else None
    valid, message = validate_run(run_dir, args.mode, result_file)
    print(message)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
