#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

NEUTRAL_WINNERS = {"Both are good", "Both are bad"}


def determine_tier_outcome(dim1_outcome: str, dim2_outcome: str) -> str:
    outcome_1 = dim1_outcome.strip()
    outcome_2 = dim2_outcome.strip()

    if outcome_1 == outcome_2:
        return "Tie" if outcome_1 in NEUTRAL_WINNERS else outcome_1
    if "Model" in (outcome_1, outcome_2) and {outcome_1, outcome_2} & NEUTRAL_WINNERS:
        return "Model"
    if "Human" in (outcome_1, outcome_2) and {outcome_1, outcome_2} & NEUTRAL_WINNERS:
        return "Human"
    return "Tie"


def _load_winner(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    winner = data.get("winner")
    if not isinstance(winner, str) or not winner.strip():
        raise ValueError(f"{path} must contain a non-empty string winner.")
    return winner


def compute_overall(
    *,
    faithfulness: str,
    readability: str,
    conciseness: str,
    aesthetics: str,
) -> dict[str, str]:
    tier1_outcome = determine_tier_outcome(faithfulness, readability)
    if tier1_outcome in {"Model", "Human"}:
        decision_path = (
            f"Tier1({faithfulness}, {readability}) -> {tier1_outcome} "
            "[Decided at Tier 1]"
        )
        return {
            "comparison_reasoning": f"Rule-based calculation: {decision_path}",
            "winner": tier1_outcome,
        }

    tier2_outcome = determine_tier_outcome(conciseness, aesthetics)
    decision_path = (
        f"Tier1({faithfulness}, {readability}) -> Tie; "
        f"Tier2({conciseness}, {aesthetics}) -> {tier2_outcome} "
        "[Decided at Tier 2]"
    )
    return {
        "comparison_reasoning": f"Rule-based calculation: {decision_path}",
        "winner": tier2_outcome,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute Paper Visualizer overall evaluation output from per-dimension winners."
    )
    parser.add_argument(
        "--evaluation-dir",
        type=Path,
        default=None,
        help="Directory containing faithfulness.json, readability.json, conciseness.json, and aesthetics.json.",
    )
    parser.add_argument("--faithfulness", default="")
    parser.add_argument("--readability", default="")
    parser.add_argument("--conciseness", default="")
    parser.add_argument("--aesthetics", default="")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the computed overall JSON.",
    )
    return parser.parse_args(argv)


def _resolve_inputs(args: argparse.Namespace) -> tuple[str, str, str, str]:
    if args.evaluation_dir is not None:
        evaluation_dir = args.evaluation_dir.resolve()
        return (
            _load_winner(evaluation_dir / "faithfulness.json"),
            _load_winner(evaluation_dir / "readability.json"),
            _load_winner(evaluation_dir / "conciseness.json"),
            _load_winner(evaluation_dir / "aesthetics.json"),
        )

    required = {
        "faithfulness": args.faithfulness,
        "readability": args.readability,
        "conciseness": args.conciseness,
        "aesthetics": args.aesthetics,
    }
    missing = [name for name, value in required.items() if not value.strip()]
    if missing:
        missing_args = ", ".join(f"--{name}" for name in missing)
        raise ValueError(
            "Missing per-dimension winners. Provide --evaluation-dir or all of: "
            f"{missing_args}"
        )
    return (
        args.faithfulness,
        args.readability,
        args.conciseness,
        args.aesthetics,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    faithfulness, readability, conciseness, aesthetics = _resolve_inputs(args)
    overall = compute_overall(
        faithfulness=faithfulness,
        readability=readability,
        conciseness=conciseness,
        aesthetics=aesthetics,
    )
    output = json.dumps(overall, ensure_ascii=False, indent=2)
    if args.output is None:
        print(output)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
