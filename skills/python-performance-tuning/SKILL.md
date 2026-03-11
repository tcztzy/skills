---
name: python-performance-tuning
description: Improve Python runtime and memory performance with a profile-first workflow. Use when users ask to speed up Python code, reduce latency, optimize hot paths, cut memory growth, compare alternative implementations, or make code more efficient without changing behavior.
---

# Python Performance Tuning

Use a profile-first process: measure, change one thing, and re-measure.

## Workflow

1. Reproduce and baseline.
- Capture Python version, OS, and command used for baseline runs.
- Prefer release builds and representative input sizes.

2. Find hotspots before changing code.
- Use `cProfile` for whole-program CPU hotspots.
- Use `timeit` (or `scripts/benchmark_snippet.py`) for micro-benchmarks.
- Use `tracemalloc` when memory growth or peaks matter.

3. Choose high-leverage changes first.
- Improve algorithm/data structure before micro-optimizing syntax.
- Replace Python loops with C-implemented stdlib primitives where possible (`sum`, `sorted`, `str.join`, `itertools`).
- Use caching (`functools.cache`/`lru_cache`) only for pure, repeatedly-called computations.

4. Validate correctness and fair benchmarking.
- Run tests before/after optimization.
- Benchmark with multiple repeats; compare best/min value for lower-bound runtime.
- Keep benchmark setup stable (same data, same environment, low background noise).

5. Report impact clearly.
- Include baseline vs new runtime (and memory if relevant), speedup ratio, and caveats.
- Note trade-offs (readability, memory, cache invalidation, complexity).

## Quick Commands

- CPU profile script/module:
```bash
python -m cProfile -o prof.out your_script.py
python - <<'PY'
import pstats
from pstats import SortKey

p = pstats.Stats("prof.out")
p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats(20)
PY
```

- Memory diff with tracemalloc:
```python
import tracemalloc

tracemalloc.start()
snap1 = tracemalloc.take_snapshot()
# call suspected code path
snap2 = tracemalloc.take_snapshot()
for stat in snap2.compare_to(snap1, "lineno")[:10]:
    print(stat)
```

- Micro-benchmark helper:
```bash
python /Users/tcztzy/.codex/skills/python-performance-tuning/scripts/benchmark_snippet.py \
  --stmt "sorted(data)" \
  --setup "import random; data=[random.randint(0, 10_000) for _ in range(10_000)]"
```

## Decision Rules

- Optimize only measured hotspots, not guessed hotspots.
- Prefer algorithm/data-structure wins over tiny syntax tweaks.
- Do not accept optimizations that break tests or change required behavior.
- Avoid overfitting to tiny benchmarks; confirm on realistic workloads.
- If CPU-bound and still too slow after Python-level work, evaluate process parallelism or native extensions.

## References

- For source-backed guidance and link collection, read `references/perf-playbook.md`.
