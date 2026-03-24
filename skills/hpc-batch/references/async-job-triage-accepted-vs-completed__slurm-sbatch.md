# Slurm `sbatch` - Submission Returns Before Execution

Source: SchedMD Slurm Workload Manager documentation - `sbatch`

URL: https://slurm.schedmd.com/sbatch.html

Key excerpt (verbatim, short):

> sbatch exits immediately after the script is successfully transferred to the Slurm controller and assigned a Slurm job ID.

Why this matters for this skill:

- The submission acknowledgment (and any notification tied to submission) can occur even though the job has not started yet.
- Slurm's documentation explicitly notes queued/pending time before resources are available; the job ID + queue status is the authoritative indicator, not the submission acknowledgement.
