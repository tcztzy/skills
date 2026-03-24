# Slurm Workload Manager: Job Array Support

Source: Slurm documentation (SchedMD)
URL: `https://slurm.schedmd.com/job_array.html`
Accessed: 2026-02-20

## Relevant points for this skill

- Slurm job arrays add filename pattern tokens for per-task I/O: `%A` expands to `SLURM_ARRAY_JOB_ID` and `%a` expands to `SLURM_ARRAY_TASK_ID`.
- The Slurm docs state the **default output file format for a job array** is `slurm-%A_%a.out` (so each array task can have its own output file).

## Why this matters

If an array job is configured without unique per-task output names, logs/results can be overwritten or merged, making it *look* like only one input ran.
