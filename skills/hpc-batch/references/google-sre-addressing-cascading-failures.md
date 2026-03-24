# Google SRE Book: Addressing Cascading Failures

- URL: https://sre.google/sre-book/addressing-cascading-failures/
- Accessed: 2026-02-22

## Why this matters for batch-submission overload

This chapter discusses overload in terms of queuing and latency: as a system approaches overload, queues grow and user-visible latency rises. It also recommends failing fast (for example, with HTTP 503) instead of letting requests sit in long queues, and using signals like queue length to drive throttling/load shedding.

## Relevant excerpts (short)

- Mentions overload symptoms like serving with extremely high latency and suggests throttling based on CPU, memory, or queue length.
- Gives an example where a user's request is slow because an RPC has been queued for 10 seconds (illustrating user-visible latency caused by queuing).
