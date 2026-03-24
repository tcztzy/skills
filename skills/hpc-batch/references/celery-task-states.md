# Celery - "Pending" Can Mean Waiting or Unknown

Source: Celery documentation - User Guide -> Tasks -> States -> Built-in States (`PENDING`)

URL: https://docs.celeryq.dev/en/stable/userguide/tasks.html#task-states

Key excerpt (verbatim, short):

> Task is waiting for execution or unknown. Any task id that's not known is implied to be in the pending state.

Why this matters for this skill:

- Some systems explicitly distinguish "accepted" from "started," and even model the "unknown/not found" case.
- If a user can't confirm a job ID exists in the authoritative system, a confirmation email alone is insufficient evidence that anything is running.
