# CURC (University of Colorado Boulder): Job Arrays

Source: CU Research Computing documentation
URL: `https://curc.readthedocs.io/en/latest/running-jobs/job-arrays.html`
Accessed: 2026-02-20

## Relevant points for this skill

- The CURC job-array guide explicitly calls out modifying `#SBATCH --output` to include `%A` and `%a` and gives an example like `#SBATCH --output=example-%A-%a.out` so each array task writes to a distinct file.
- The same section notes it is important to include `%A` (`SLURM_ARRAY_JOB_ID`) and `%a` (`SLURM_ARRAY_TASK_ID`) to differentiate outputs, and shows a matching `--error` example (`example-%A-%a.err`).

## Why this matters

If you don’t include array ids in the output filename, multiple tasks can write to the same file, making a batch run appear incomplete.
