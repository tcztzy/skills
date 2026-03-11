# Python Performance Playbook (Source-backed)

## Core principles

1. Measure first, then optimize.
   - Use deterministic profiling (`cProfile`/`profile`) to find real hotspots.
2. Benchmark fairly.
   - `timeit` disables GC by default for comparability; re-enable when GC cost is part of the workload.
   - Prefer multiple repeats and compare best/min time.
3. Track memory explicitly.
   - Use `tracemalloc` snapshots and `compare_to` to identify top allocation sites.
4. Favor algorithmic wins.
   - Data structure choice and asymptotic complexity usually beat syntax-level tweaks.
5. Preserve correctness and maintainability.
   - Any speedup must pass tests and keep behavior unchanged unless a behavior change is requested.

## High-value optimization patterns

- Replace repeated list membership checks with `set`/`dict` lookups when order is not required.
- Build strings with `str.join` for many pieces.
- Cache pure function results with `functools.cache`/`functools.lru_cache` when hit rate is high.
- Reduce temporary allocations in hot loops; hoist invariant computation outside loops.
- Batch I/O and reduce per-call overhead in tight paths.

## Measurement checklist

- Record Python version and machine info.
- Use representative input data sizes.
- Warm up before timing (especially newer CPython versions with adaptive specialization).
- Keep runs isolated from unrelated system load when possible.
- Report both absolute times and speedup ratios.

## Primary sources

- cProfile/profile docs: https://docs.python.org/3/library/profile.html
- timeit docs: https://docs.python.org/3/library/timeit.html
- tracemalloc docs: https://docs.python.org/3/library/tracemalloc.html
- functools cache/lru_cache docs: https://docs.python.org/3/library/functools.html
- CPython FAQ (performance-related questions): https://docs.python.org/3/faq/programming.html
- pyperformance benchmark suite: https://github.com/python/pyperformance
- PEP 659 (specializing adaptive interpreter): https://peps.python.org/pep-0659/
