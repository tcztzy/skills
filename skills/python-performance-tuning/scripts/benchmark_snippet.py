#!/usr/bin/env python3
"""Run a small, repeatable micro-benchmark with timeit.

This helper is for quick local comparisons when iterating on Python snippets.
"""

from __future__ import annotations

import argparse
import gc
import json
import statistics
import timeit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stmt", required=True, help="Statement to benchmark")
    parser.add_argument("--setup", default="pass", help="Setup code executed once per timing run")
    parser.add_argument("--repeat", type=int, default=7, help="Number of repeated timing runs")
    parser.add_argument("--number", type=int, default=0, help="Executions per run (0 = auto)")
    parser.add_argument(
        "--enable-gc",
        action="store_true",
        help="Enable gc during measurement (timeit disables it by default)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timer = timeit.Timer(stmt=args.stmt, setup=args.setup)

    if args.enable_gc:
        gc.enable()

    if args.number > 0:
        loops = args.number
    else:
        loops, _ = timer.autorange()

    samples = timer.repeat(repeat=max(1, args.repeat), number=loops)
    result = {
        "loops": loops,
        "repeat": len(samples),
        "samples_seconds": samples,
        "best_seconds": min(samples),
        "median_seconds": statistics.median(samples),
        "per_loop_best_seconds": min(samples) / loops,
        "per_loop_median_seconds": statistics.median(samples) / loops,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
