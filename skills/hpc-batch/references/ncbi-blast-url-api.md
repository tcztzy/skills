# NCBI BLASTHelp: Common URL API

URL: https://blast.ncbi.nlm.nih.gov/doc/blast-help/urlapi.html
Accessed: 2026-02-22

## Why this matters for the skill

This page documents a standard async-job API pattern: **submit** a job, receive a **request ID**, then later **check status / retrieve results** using that ID.

## Key excerpts

- “You may use `Put` for search submission, or `Get` for checking the status of a submission or retrieving results after its completion.”
- “`RID` … The Request ID (RID) returned when the search was submitted.”
