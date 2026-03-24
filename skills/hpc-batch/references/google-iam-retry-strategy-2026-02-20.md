# Google Cloud - IAM: Retry failed requests

- URL: https://cloud.google.com/iam/docs/retry-strategy
- Accessed: 2026-02-20

## Relevant excerpts

- "If your application retries failed requests without waiting, it might send a large number of retries ... in a short period of time."
- "We strongly recommend that you use truncated exponential backoff with introduced jitter..."

## Used for

- Retry safely under load: back off between retries and add jitter to avoid synchronized retry storms.
