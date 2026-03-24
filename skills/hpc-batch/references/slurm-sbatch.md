# Slurm Workload Manager: sbatch

Source: Slurm documentation (SchedMD)
URL: `https://slurm.schedmd.com/sbatch.html`
Accessed: 2026-02-20

## Relevant points for this skill

- `sbatch` controls where batch-job output goes via `--output` (stdout) and `--error` (stderr).
- Slurm documents the **default output behavior**: stdout+stderr go to `slurm-%j.out` by default (where `%j` is the job id), and for job arrays the default file name is `slurm-%A_%a.out` (where `%A` is the job id and `%a` is the array index).
- The same page describes filename-pattern substitutions that can be used to make outputs/logs unique per job/task.

## Why this matters

When running a batch/array workflow, non-unique `--output/--error` settings can hide per-task failures or overwrite logs, resulting in “only one output file” even if multiple tasks ran.
