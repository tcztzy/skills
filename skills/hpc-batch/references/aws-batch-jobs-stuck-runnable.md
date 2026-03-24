# AWS Batch - Jobs stuck in a RUNNABLE status

- URL: https://docs.aws.amazon.com/batch/latest/userguide/job_stuck_in_runnable.html
- Accessed: 2026-02-20

## Why this matters

This troubleshooting guide describes server-side reasons queued jobs can stop making progress (capacity, queue blocking, configuration), which is analogous to "online tool jobs stuck partway through" when the backend is overloaded.

## Relevant excerpt (verbatim, short)

"causing your job queues to be blocked."

## Notes

- The guide frames a stuck `RUNNABLE` job as a symptom that something is preventing work from being placed onto compute resources, often related to capacity or queueing constraints.
- When many independent submissions show the same stall pattern, a systemic queue/worker bottleneck is typically more plausible than a user-specific network issue.
