---
name: hpc-batch
description: Troubleshoot Slurm/LSF batch jobs, arrays, and stuck-job issues. Use when
  prompts mention sbatch/squeue/sacct/scontrol or bsub/bjobs/bhist/bacct, job arrays, N inputs
  producing fewer than N outputs, missing per-task logs/exit codes, stuck pending/running jobs,
  overload/queue saturation, safe retry/resubmit decisions, or output/log filename collisions.
---

# HPC Batch + Job Array Triage (Slurm/LSF)

Use this skill to troubleshoot HPC batch jobs and job arrays end-to-end (submission -> execution -> outputs).
Keep answers evidence-bound; do not guess cluster-specific policies.

If MCQ: return the exact selected option text.

## Core Framing

- Treat submission acceptance as *receipt*, not completion.
- Require per-task observability before concluding root cause: task ID, task log path, task exit code, and a unique output key.
- Separate 4 layers of failure early:
  1) scheduler/queueing,
  2) node/runtime environment,
  3) application logic,
  4) filesystem/output naming collisions.

## Minimal Intake (Ask For These)

- Scheduler: Slurm or LSF (or "unknown").
- Immutable handle: job ID (and array parent ID if applicable).
- Submission script / command (sbatch or bsub flags).
- Expected input IDs and how they map to array indices.
- Output root path pattern and log path pattern.

## Workflow (Use This Order)

1. **Accepted vs completed**
   - Verify state in the scheduler (queue/accounting), not by "no email / no stdout".

2. **Count expected vs observed**
   - Compute `N_expected`, `N_observed`, and a missing-ID list. Do not reason from totals only.

3. **Map missing outputs -> task IDs**
   - For each missing ID, decide: `never started | failed | succeeded-but-output-missing | overwritten | intentionally skipped`.

4. **Check output naming collisions**
   - If multiple tasks write the same leaf path, treat as collision until proven otherwise.

5. **Check exit codes & states**
   - Use accounting to identify systemic patterns (same node, same error, OOM, timeouts).

6. **Overload mitigation**
   - If scale breaks reliability, split into chunks, reduce concurrency, and run a canary before broad retries.

7. **Retry/resubmit safely**
   - Retry only failed/missing items.
   - Ensure idempotency: unique output per input + atomic write patterns.

## Slurm Quick Reference

### Arrays: unique logs and concurrency limit

- Use `--array=START-END%MAX_CONCURRENT` to limit concurrency.
- Require `%A` (array master ID) and `%a` (task index) in `--output/--error` to avoid collisions.

Example (template):

- `#SBATCH --array=1-1000%50`
- `#SBATCH --output=logs/%x-%A_%a.out`
- `#SBATCH --error=logs/%x-%A_%a.err`

### State and "why pending"

- `squeue -j <jobid>` to see whether it is pending/running.
- Use formatted `Reason` to learn why a job is pending (policy/resources/QOS).

### Completion and exit codes

- Use accounting (`sacct`) to see per-task `State` and `ExitCode`.
- For deep details, use `scontrol show job <jobid>` (and for arrays, inspect child IDs).

## LSF Quick Reference (IBM Spectrum LSF)

### Arrays: slot limit and unique logs

- Use `bsub -J "name[1-1000]%50"` to cap concurrent running slots.
- Prefer output patterns that include job ID and array index to avoid collisions.

Example (template):

- `bsub -J "myjob[1-1000]%50" -o "logs/%J.%I.out" -e "logs/%J.%I.err" < run.sh`

### State and history

- `bjobs <jobid>` and `bjobs -l <jobid>` for current state and details.
- Use history/accounting (for example `bhist`, `bacct`) when the job is no longer in the active queue.

## Pattern Library (Map Symptoms -> Likely Cause -> Next Check)

### Symptom: "I submitted N tasks but got <N outputs"

Likely causes:

- tasks never started (queue/policy),
- tasks failed (runtime/app),
- output naming collision/overwrite,
- documented skip/filter rules (expected).

Next checks:

- build missing-ID list,
- check per-task exit codes,
- verify output paths include an input-specific key (ID or array index).

### Symptom: "Logs are combined; I can't tell which task ran"

Likely cause:

- log routing does not include per-task identifiers.

Fix:

- route logs per task (Slurm: `%A_%a`; LSF: `%J.%I`) and re-run a 2-task canary.

### Symptom: "Accepted/submitted, but nothing happens"

Likely cause:

- queued/pending with a reason (resources/QOS/fairshare), not "stuck".

Next checks:

- read pending reason,
- confirm your account/queue/project is correct,
- confirm requested resources are feasible.

### Symptom: "Big array works at small scale but fails at large scale"

Likely cause:

- scheduler/filesystem overload, per-user submit limits, array-size limits, or hotspotting (single directory).

Mitigation:

- split into chunks,
- reduce concurrency (`%MAX_CONCURRENT`),
- canary before retries,
- distribute outputs across subdirectories.

## Output/Retry Design Rules (Idempotency)

- One input -> one stable output path (include input ID or index).
- Never let multiple tasks write the same file path.
- Prefer "write temp then rename" to avoid partial outputs being mistaken as complete.
- On retry: rerun only missing/failed IDs; do not replay the entire batch unless the run is non-idempotent.

## Source Reference Mapping

- `batch-array-task-log-forensics`: [azure-batch-stdout-stderr.md](references/azure-batch-stdout-stderr.md), [curc-job-arrays.md](references/curc-job-arrays.md), [slurm-job-arrays.md](references/slurm-job-arrays.md), [slurm-sbatch.md](references/slurm-sbatch.md)
- `batch-output-completeness-triage`: (no references)
- `batch-overload-mitigation-and-canary`: [ebi-jdispatcher-fair-use.md](references/ebi-jdispatcher-fair-use.md), [google-analytics-userdeletion-errors-2026-02-20.md](references/google-analytics-userdeletion-errors-2026-02-20.md), [google-cloud-tasks-common-pitfalls.md](references/google-cloud-tasks-common-pitfalls.md), [google-cloud-tasks-manage-scaling-risks.md](references/google-cloud-tasks-manage-scaling-risks.md), [google-gmail-handle-errors-2026-02-20.md](references/google-gmail-handle-errors-2026-02-20.md), [google-iam-retry-strategy-2026-02-20.md](references/google-iam-retry-strategy-2026-02-20.md), [google-sre-addressing-cascading-failures.md](references/google-sre-addressing-cascading-failures.md), [openai-batch-faq-2026-02-20.md](references/openai-batch-faq-2026-02-20.md), [openai-batch-guide-2026-02-20.md](references/openai-batch-guide-2026-02-20.md), [ulhpc-job-arrays-2026-02-20.md](references/ulhpc-job-arrays-2026-02-20.md)
- `async-job-stall-retry-and-fallback`: [aws-exponential-backoff-jitter.md](references/aws-exponential-backoff-jitter.md), [azure-retry-pattern.md](references/azure-retry-pattern.md), [bae-2014-cas-offinder.md](references/bae-2014-cas-offinder.md), [bioconductor-crisprdesign.md](references/bioconductor-crisprdesign.md), [crisporWebsite-github.md](references/crisporWebsite-github.md), [google-cloud-storage-retry-strategy.md](references/google-cloud-storage-retry-strategy.md), [haeussler-2016-crispor-genomebiology.md](references/haeussler-2016-crispor-genomebiology.md), [haeussler-2016-crispor.md](references/haeussler-2016-crispor.md), [montague-2014-chopchop.md](references/montague-2014-chopchop.md), [oesterle-2017-cod.md](references/oesterle-2017-cod.md), [rfc9110-http-semantics.md](references/rfc9110-http-semantics.md)
- `async-job-triage-accepted-vs-completed`: [atlassian-handbook-major-incident.md](references/atlassian-handbook-major-incident.md), [aws-batch-job-states.md](references/aws-batch-job-states.md), [aws-batch-jobs-stuck-runnable.md](references/aws-batch-jobs-stuck-runnable.md), [celery-task-states.md](references/celery-task-states.md), [github-status-check.md](references/github-status-check.md), [google-sre-queue-management.md](references/google-sre-queue-management.md), [ibm-quantum-monitor-job.md](references/ibm-quantum-monitor-job.md), [little-1961-lambda-w.md](references/little-1961-lambda-w.md), [mailgun-accepted-not-delivered.md](references/mailgun-accepted-not-delivered.md), [microsoft-progress-bars.md](references/microsoft-progress-bars.md), [mit-ocw-mm1-queue-fall-2016.md](references/mit-ocw-mm1-queue-fall-2016.md), [ncbi-blast-url-api.md](references/ncbi-blast-url-api.md), [rfc9110-http-202-accepted.md](references/rfc9110-http-202-accepted.md), [rfc9110-http-503.md](references/rfc9110-http-503.md), [sendgrid-202-accepted-not-sent.md](references/sendgrid-202-accepted-not-sent.md), [slurm-sbatch.md](references/async-job-triage-accepted-vs-completed__slurm-sbatch.md)

## References

- [async-job-triage-accepted-vs-completed__slurm-sbatch.md](references/async-job-triage-accepted-vs-completed__slurm-sbatch.md)
- [atlassian-handbook-major-incident.md](references/atlassian-handbook-major-incident.md)
- [aws-batch-job-states.md](references/aws-batch-job-states.md)
- [aws-batch-jobs-stuck-runnable.md](references/aws-batch-jobs-stuck-runnable.md)
- [aws-exponential-backoff-jitter.md](references/aws-exponential-backoff-jitter.md)
- [azure-batch-stdout-stderr.md](references/azure-batch-stdout-stderr.md)
- [azure-retry-pattern.md](references/azure-retry-pattern.md)
- [bae-2014-cas-offinder.md](references/bae-2014-cas-offinder.md)
- [bioconductor-crisprdesign.md](references/bioconductor-crisprdesign.md)
- [celery-task-states.md](references/celery-task-states.md)
- [crisporWebsite-github.md](references/crisporWebsite-github.md)
- [curc-job-arrays.md](references/curc-job-arrays.md)
- [ebi-jdispatcher-fair-use.md](references/ebi-jdispatcher-fair-use.md)
- [github-status-check.md](references/github-status-check.md)
- [google-analytics-userdeletion-errors-2026-02-20.md](references/google-analytics-userdeletion-errors-2026-02-20.md)
- [google-cloud-storage-retry-strategy.md](references/google-cloud-storage-retry-strategy.md)
- [google-cloud-tasks-common-pitfalls.md](references/google-cloud-tasks-common-pitfalls.md)
- [google-cloud-tasks-manage-scaling-risks.md](references/google-cloud-tasks-manage-scaling-risks.md)
- [google-gmail-handle-errors-2026-02-20.md](references/google-gmail-handle-errors-2026-02-20.md)
- [google-iam-retry-strategy-2026-02-20.md](references/google-iam-retry-strategy-2026-02-20.md)
- [google-sre-addressing-cascading-failures.md](references/google-sre-addressing-cascading-failures.md)
- [google-sre-queue-management.md](references/google-sre-queue-management.md)
- [haeussler-2016-crispor-genomebiology.md](references/haeussler-2016-crispor-genomebiology.md)
- [haeussler-2016-crispor.md](references/haeussler-2016-crispor.md)
- [ibm-quantum-monitor-job.md](references/ibm-quantum-monitor-job.md)
- [little-1961-lambda-w.md](references/little-1961-lambda-w.md)
- [mailgun-accepted-not-delivered.md](references/mailgun-accepted-not-delivered.md)
- [microsoft-progress-bars.md](references/microsoft-progress-bars.md)
- [mit-ocw-mm1-queue-fall-2016.md](references/mit-ocw-mm1-queue-fall-2016.md)
- [montague-2014-chopchop.md](references/montague-2014-chopchop.md)
- [ncbi-blast-url-api.md](references/ncbi-blast-url-api.md)
- [oesterle-2017-cod.md](references/oesterle-2017-cod.md)
- [openai-batch-faq-2026-02-20.md](references/openai-batch-faq-2026-02-20.md)
- [openai-batch-guide-2026-02-20.md](references/openai-batch-guide-2026-02-20.md)
- [rfc9110-http-202-accepted.md](references/rfc9110-http-202-accepted.md)
- [rfc9110-http-503.md](references/rfc9110-http-503.md)
- [rfc9110-http-semantics.md](references/rfc9110-http-semantics.md)
- [sendgrid-202-accepted-not-sent.md](references/sendgrid-202-accepted-not-sent.md)
- [slurm-job-arrays.md](references/slurm-job-arrays.md)
- [slurm-sbatch.md](references/slurm-sbatch.md)
- [ulhpc-job-arrays-2026-02-20.md](references/ulhpc-job-arrays-2026-02-20.md)
