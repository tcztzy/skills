# Google Cloud Storage: Retry strategy (idempotency + retryable errors)

URL: https://cloud.google.com/storage/docs/retry-strategy

Accessed: 2026-02-20

## Why this matters for "stuck job" resubmission

- Lists common **retryable** failure classes (including `503`) and recommends retrying transient failures.
- Emphasizes **idempotency** as the key safety property for retries/resubmissions.

## Quotes (verbatim, short)

- Retry support statement: "By default, operations support retries for the following errors:" (e.g., Java section)
- One listed retryable HTTP code: "`503 Service Unavailable`" (e.g., Java section)
- Retry safety depends on idempotency: "By default, all idempotent operations are retried," and "Non-idempotent operations are not retried." (Idempotency section)
