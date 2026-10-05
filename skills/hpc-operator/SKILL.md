---
name: hpc-operator
description: Operate and troubleshoot IBM Spectrum LSF batch jobs, job arrays, queues, and execution hosts. Use when prompts mention bsub, bjobs, bhist, bacct, bqueues, bhosts, lsload, PEND or EXIT states, missing array outputs, per-task logs, queue saturation, resource requests, or safe targeted resubmission.
---

# HPC Operator (LSF)

Troubleshoot LSF jobs from submission through execution and output verification.
Keep conclusions evidence-bound and treat cluster policy as site-specific.

## Operating contract

- Inspect before mutating. Do not kill, requeue, switch, or resubmit jobs unless
  the user requested that action.
- Treat successful `bsub` submission as receipt, not completion.
- Require a job or array ID before making a job-specific diagnosis.
- Distinguish scheduler state, execution-host state, application failure, and
  output-path failure.
- Do not guess queue limits, fair-share policy, project permissions, or site
  configuration.

## Minimal intake

Collect:

- job ID and array indices, if applicable
- original `bsub` command or `#BSUB` script
- queue, project, resource request, and job-slot request
- expected input IDs and their mapping to `LSB_JOBINDEX`
- stdout, stderr, and output path patterns
- expected versus observed outputs

Ask only for the missing evidence needed for the next decision.

## Diagnostic workflow

### 1. Establish current state

Start with the narrowest read-only query:

```bash
bjobs <job_id>
bjobs -l <job_id>
```

Classify each relevant job or array element as `PEND`, `RUN`, `DONE`, `EXIT`,
or suspended. Do not infer completion from an absent active-job listing.

For historical transitions and completed-job accounting:

```bash
bhist -l <job_id>
bacct -l <job_id>
```

`bacct` is for jobs recorded in accounting, primarily `DONE` and `EXIT`; do not
use its absence as proof that a pending or never-dispatched job did not exist.

### 2. Diagnose pending jobs

Use LSF's pending-reason views before attributing delay to a busy cluster:

```bash
bjobs -p
bjobs -p1
bjobs -l -p
bjobs -psum
```

Separate:

- resource mismatch or unsatisfied host selection
- queue, project, user, or job-slot limits
- dependency or time-window constraints
- lower scheduling priority or fair-share effects
- unavailable, closed, or overloaded hosts

When cluster-level evidence is needed:

```bash
bqueues
bqueues -l <queue>
bhosts
bhosts -l
lsload -w
```

Use `lsload -gpu` or `lsload -gpuload` only if the installed LSF version and
cluster configuration support those views.

### 3. Reconcile arrays and outputs

Compute:

- `N_expected`
- `N_observed`
- exact missing input IDs
- exact corresponding array indices

For every missing output, assign one state:

`never dispatched | pending | running | exited | done but missing |
overwritten | intentionally skipped`

Totals alone are not enough. Join scheduler evidence to the input-to-index
manifest.

### 4. Check logs and collisions

For arrays, include both job ID and array index in log paths:

```bash
bsub \
  -J "name[1-1000]%50" \
  -o "logs/%J.%I.out" \
  -e "logs/%J.%I.err" \
  < run.sh
```

Inside the job, use `LSB_JOBINDEX` to select the corresponding input. Ensure
application outputs also contain a stable input ID or array index.

Treat shared leaf paths as collisions until disproven. Prefer writing a temporary
file and atomically renaming it only after successful completion.

### 5. Diagnose `EXIT`

Correlate:

- `bjobs -l` status and exit information
- `bhist -l` state transitions
- `bacct -l` recorded resource use
- per-index stderr and application logs
- repeated failures by host, input, queue, or resource request

Distinguish memory pressure, runtime limits, host failure, environment problems,
application errors, and invalid input. Do not recommend a larger resource request
without evidence.

### 6. Retry safely

Before resubmission:

- prove which indices need work
- confirm each output path is unique
- make the task idempotent or define cleanup
- run a small canary when changing resources, concurrency, or environment
- resubmit only missing or failed indices

An explicit LSF array index list can target retries:

```bash
bsub -J "retry[3,7,12]%2" -o "logs/%J.%I.out" -e "logs/%J.%I.err" < run.sh
```

Preserve the original input-to-index mapping. Do not renumber retries if the
script derives input identity from `LSB_JOBINDEX`.

## Common symptom routing

- `PEND for hours`: inspect pending reasons, then queue and host evidence.
- `N inputs, fewer outputs`: build the missing-ID/index table before retrying.
- `DONE but no output`: inspect application logs, output paths, atomic-write
  behavior, and post-processing.
- `EXIT at scale`: compare per-index errors and resource use; reduce concurrency
  or split batches only when evidence points to saturation.
- `one combined log`: fix `%J.%I` routing and reproduce with a small canary.

## Output

Return:

1. observed facts and commands used
2. state classification for affected jobs or indices
3. most likely failure layer, with competing explanations
4. the next read-only check
5. any proposed mutation or targeted retry, clearly separated

Use `references/ibm-lsf-official.md` when exact command behavior or source
attribution matters. Prefer the installed cluster's `man` pages and `-h` output
when its LSF version differs from the referenced documentation.
