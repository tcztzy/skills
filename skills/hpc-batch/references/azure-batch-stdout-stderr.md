# Microsoft Learn: Azure Batch task failure with no stdout/stderr log

Source: Microsoft Learn (Azure troubleshooting)
URL: `https://learn.microsoft.com/en-us/troubleshoot/azure/hpc/batch/azure-batch-task-failure-no-stdout-stderr-log`
Accessed: 2026-02-20

## Relevant points for this skill

- Azure Batch tasks have an **exit code** recorded in task execution information, and tasks can be marked failed based on that return code.
- Azure Batch captures standard output and standard error for a task into `stdout.txt` and `stderr.txt`, but this article documents cases where a task can fail without producing those files—so checking task status/exit codes is important.

## Why this matters

“Job finished” does not imply “all tasks produced expected outputs”; use per-task status/exit codes (and logs where available) to distinguish true completion from partial failure.
