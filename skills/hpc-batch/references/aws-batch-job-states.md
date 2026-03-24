# AWS Batch - Jobs Can Be Submitted Without Running

Source: AWS Batch User Guide - "Job states"

URL: https://docs.aws.amazon.com/batch/latest/userguide/job_states.html

Key excerpt (verbatim, short):

> When you submit a job to an AWS Batch job queue, the job enters the `SUBMITTED` state.

Why this matters for this skill:

- It documents an explicit state machine where submission/acceptance (`SUBMITTED`, `PENDING`, `RUNNABLE`) is distinct from execution (`RUNNING`).
- The correct "is it running?" signal is the system's job state, not any out-of-band confirmation email.
