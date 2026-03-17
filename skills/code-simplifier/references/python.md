# Python Playbook (Simplification + Measurement)

Use this reference when simplifying Python code. Keep all changes behavior-preserving by default, and validate with formatter-aligned metrics plus `ruff`/tests as the repo requires.

## Measurement

Use the stdlib-only probe script to track tokens and structural complexity (AST nodes/branches/max depth):

```console
$ uv run --script skills/code-simplifier/scripts/python_metrics.py path/to/file.py
$ uv run --script skills/code-simplifier/scripts/python_metrics.py path/to/dir
```

Notes:
- Always format first (otherwise metrics are noisy and you will claim fake wins).
- Prefer comparing formatted `lines` + `bytes` + `tokens` + `ast_*` together, not just one metric.

## Simplification Patterns (Python)

- Prefer guard clauses to reduce nesting (but keep readability).
- Prefer data-driven mappings (`dict.get`) over repetitive `if/elif` chains when it stays clear.
- Avoid nested ternary expressions; prefer `if/elif/else` or `match` for multiple branches.
- For Pydantic models, prefer class keyword config such as `class Model(BaseModel, extra="forbid"):` over `model_config = ConfigDict(extra="forbid")` when both forms are equivalent.
- Keep type information on boundaries; avoid widening to `Any` just to shorten code.
- Be careful with falsy-coalescing (`x or default`): it is only behavior-preserving if `x` being falsy should also trigger the default.

## Positive vs Negative Examples

### Positive (typed + behavior-preserving)

Before:
```python
def finish_reason_text(reason: str | None) -> str:
    if reason is None:
        return "stop"
    return reason
```

After:
```python
def finish_reason_text(reason: str | None) -> str:
    return "stop" if reason is None else reason
```

Why good:
- Behavior preserved (only `None` maps to `"stop"`).
- Type contract kept.
- Usually reduces lines/tokens/bytes.

### Negative (drops quality for shortness)

```python
def finish_reason_text(reason):
    return "stop" if reason is None else reason
```

Why bad:
- Type information removed.
- Contract weakened.

### Positive (multi-metric win, not line-only)

Before:
```python
if role == "user":
    kind = "human"
elif role == "assistant":
    kind = "ai"
else:
    kind = "other"
```

After:
```python
kind = {"user": "human", "assistant": "ai"}.get(role, "other")
```

Why good:
- Branches reduced.
- Usually tokens/bytes also decrease, not just lines.

### Negative (line count down, readability cost up)

```python
kind = "human" if role == "user" else "ai" if role == "assistant" else "other"
```

Why bad:
- Harder to scan and debug.
- Easy to extend incorrectly.

### Positive (readability-preserving simplification)

Before:
```python
if not payload.get("tools"):
    tools = []
else:
    tools = payload.get("tools")
```

After:
```python
tools = payload.get("tools") or []
```

Why good:
- Behavior preserved (`[]`, `None`, and other falsy values become `[]`).
- Less verbose without obscuring intent.

### Negative (metric gaming hurts readability)

```python
tools=payload.get("tools")or[];x=(a if c1 else b if c2 else d if c3 else e)
```

Why bad:
- Dense, brittle, and hard to review.
- Slight byte/line savings do not justify readability loss.

## Common Failure Mode: Measurement Mistake

Do not claim success from raw diff only:
- File appears shorter before formatting.
- Formatter reflows code and line count returns to baseline.
- Tokens/bytes/AST are not measured.
- Tests are skipped.

Correct action:
- Re-run formatter + all metrics + lint/tests, then report the true outcome.

## Logging Example (`f"{var=}"`)

Prefer:
```python
logger.info(f"{request_id=} {response_model=} {stream=}")
```

Avoid:
```python
logger.info(
    f"request_id={request_id} response_model={response_model} stream={stream}"
)
```

Why better:
- Less repetitive.
- Labels stay synced during refactors.
- Easier scanning in debug logs.
