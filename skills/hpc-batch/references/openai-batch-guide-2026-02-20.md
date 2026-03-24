# OpenAI API Docs - Batch API guide

- URL: https://platform.openai.com/docs/guides/batch
- Accessed: 2026-02-20

## Relevant excerpts

- "Batches that do not complete in time eventually move to an `expired` state; unfinished requests within that batch are cancelled..."
- "For now, the completion window can only be set to `24h`."

## Used for

- Batch jobs can expire when not completed within the completion window, cancelling unfinished work.
