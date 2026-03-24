# Microsoft Azure Architecture Center: Retry pattern

URL: https://learn.microsoft.com/en-us/azure/architecture/patterns/retry

Accessed: 2026-02-20

## Why this matters for "stuck job" resubmission

- Frames many failures as **transient faults** where repeating the operation after a delay can succeed.
- Calls out **idempotency** as a key safety check before retrying.
- Warns against overly aggressive retry loops (need limits/delays).

## Quotes (verbatim, short)

- Transient faults can clear: "These faults are typically self-correcting, and if the action that triggered a fault is repeated after a suitable delay it's likely to be successful." (Context and problem section)
- Safety check: "Consider whether the operation is idempotent. If so, it's inherently safe to retry." (Idempotency section)
