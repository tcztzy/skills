# IBM Quantum Documentation: Monitor or Cancel a Job

URL: https://quantum.cloud.ibm.com/docs/en/guides/monitor-job
Accessed: 2026-02-22

## Why this matters for the skill

This page documents the common async-job pattern: a submitted job has a **job ID**, and retrieving results later requires saving that ID.

## Key excerpts

- “Retrieving the job results at a later time requires the job ID.”
- “Call `service.job(<job_id>)` to retrieve a job you previously submitted.”
