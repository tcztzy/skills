# Google SRE Book - "Addressing Cascading Failures" (Queue Management)

- URL: https://sre.google/sre-book/addressing-cascading-failures/
- Accessed: 2026-02-22

## Relevant excerpt (short)

> "Queued requests consume memory and increase latency."

## Why this matters for the skill

- The chapter's "Queue Management" section explains that when incoming work exceeds processing capacity, queues saturate and latency grows because work spends time waiting before execution.
- This supports using "extreme queue depth / many queued jobs" as a primary explanation for slow-but-progressing processing.
