# Google Cloud Tasks: Common pitfalls (issues and limitations)

- URL: https://docs.cloud.google.com/tasks/docs/common-pitfalls
- Accessed: 2026-02-22
- Last updated (page): 2026-02-19 UTC

## Why this matters for batch-submission overload

This page explains that if you enqueue/dispatch work faster than your target can process it, a backlog will build. It also notes that overloaded targets may return 503/429 and that Cloud Tasks may slow down task dispatch in response.

## Relevant excerpts (short)

- Provides an example: if you attempt to execute 100 tasks/second against frontend instances that can only process 10 requests/second, a backlog will build.
- Notes that targets can be overloaded and return 503 (Service Unavailable) or 429 (Too Many Requests), and that Cloud Tasks will slow down as a result.
