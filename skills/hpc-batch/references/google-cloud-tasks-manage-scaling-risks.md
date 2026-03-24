# Google Cloud Tasks: Manage scaling risks (traffic tuning)

- URL: https://docs.cloud.google.com/tasks/docs/tuning/traffic
- Accessed: 2026-02-22
- Last updated (page): 2026-02-09 UTC

## Why this matters for batch-submission overload

This page defines "queue overload" and calls out causes consistent with batch submissions (for example, running batch jobs that inject large numbers of tasks). It also states that queue overload can increase creation latency, cause errors, and reduce dispatch rates.

## Relevant excerpts (short)

- Defines queue overload as a sudden increase in traffic when task creation and dispatch increases faster than the queue infrastructure can adapt; notes it can lead to increased task creation latency.
- Lists scenarios that can lead to overload, including running batch jobs that inject large numbers of tasks.
- States that overloaded queues can experience increased task creation latency, errors, and reduced dispatch rates.
