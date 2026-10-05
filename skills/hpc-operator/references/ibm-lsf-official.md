# IBM Spectrum LSF official references

Use these pages for exact LSF 10.1 behavior. If the installed cluster runs a
different version, prefer its `man` pages, command help, and administrator
documentation.

## Job lifecycle and inspection

- [bjobs command reference](https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=reference-bjobs):
  current pending, running, and suspended jobs; use `bhist` for older history.
- [Viewing pending reasons](https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=jobs-view-pending-reasons):
  `bjobs -p`, pending-reason levels, detailed output, summaries, and
  parse-oriented output.
- [bhist command reference](https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=reference-bhist):
  historical job events and state transitions.
- [bacct command reference](https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=reference-bacct):
  accounting statistics for completed and exited jobs.

## Arrays

- [LSF job arrays](https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=administration-job-arrays):
  array syntax, index identity, `%I`, `%J`, `LSB_JOBINDEX`, and array slot
  limits.

## Queue and host evidence

- [bqueues command reference](https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=reference-bqueues):
  queue status, limits, windows, policies, hosts, and job-state statistics.
- [bhosts command reference](https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=reference-bhosts):
  execution-host status, job-slot limits, and static/dynamic resources.
- [lsload command reference](https://www.ibm.com/docs/en/spectrum-lsf/10.1.0?topic=reference-lsload):
  host load and resource views, including optional GPU views.
