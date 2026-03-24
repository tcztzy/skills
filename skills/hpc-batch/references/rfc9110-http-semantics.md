# RFC 9110: HTTP Semantics (503 Service Unavailable, Retry-After)

URL: https://www.rfc-editor.org/rfc/rfc9110

Accessed: 2026-02-20

## Why this matters for "stuck job" resubmission

- `503 Service Unavailable` explicitly covers **temporary overload** and suggests the problem can clear after waiting.
- `Retry-After` provides an explicit **wait time** for a follow-up request (including when paired with `503`).

## Quotes (verbatim, short)

- 503 is for temporary conditions: "temporary overload or scheduled maintenance, which will likely be alleviated after some delay." (Section 15.6.4)
- `Retry-After` guidance: "indicates how long the user agent ought to wait before making a follow-up request." (Section 10.2.3)
