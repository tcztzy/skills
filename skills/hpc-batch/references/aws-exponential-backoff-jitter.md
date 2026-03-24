# AWS Architecture Blog: Exponential Backoff And Jitter

URL: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/

Accessed: 2026-02-20

## Why this matters for "stuck job" resubmission

- When many clients retry at the same cadence, retries can synchronize and amplify load spikes ("thundering herd").
- Adding randomization ("jitter") to backoff spreads retries out and reduces coordinated bursts.

## Quote (short excerpt)

- "The solution isn't to remove backoff. It's to add jitter." (Blog post body)
