# Legacy migration workflow

Convert an undocumented repository incrementally. Optimize for verified coverage and non-regression, not a large count of generated comments.

## Contents

- [Principles](#principles)
- [Phase 0: establish safety](#phase-0-establish-safety)
- [Phase 1: inventory and baseline](#phase-1-inventory-and-baseline)
- [Phase 2: choose profiles and policy](#phase-2-choose-profiles-and-policy)
- [Phase 3: prioritize semantic boundaries](#phase-3-prioritize-semantic-boundaries)
- [Phase 4: run a pilot](#phase-4-run-a-pilot)
- [Phase 5: migrate in bounded batches](#phase-5-migrate-in-bounded-batches)
- [Phase 6: ratchet enforcement](#phase-6-ratchet-enforcement)
- [Phase 7: verify comprehension](#phase-7-verify-comprehension)
- [Migration outputs](#migration-outputs)

## Principles

- Never infer semantics from filenames or signatures alone.
- Ground documentation in implementation, tests, call sites, configuration, and existing design records.
- Separate **missing documentation** from **unknown behavior**. Investigate unknowns; do not turn guesses into permanent contracts.
- Keep migration commits reviewable and behavior-neutral unless a discovered defect receives its own tested fix.
- Prefer boundaries with high routing value before low-level leaf helpers.
- Add enforcement as a ratchet so legacy debt does not block every change on day one.

## Phase 0: establish safety

1. Record the clean/dirty worktree state and preserve unrelated changes.
2. Identify generated, vendored, third-party, fixture, snapshot, and build-output paths.
3. Find repository instructions and owners.
4. Locate existing tests, doc builds, linters, and API compatibility checks.
5. Decide whether documentation-only changes can safely share a commit with formatting changes. Default to separate changes.

## Phase 1: inventory and baseline

Run the bundled scanner on source roots:

```bash
python3 /path/to/ddd/scripts/check_file_docs.py src include --format json \
  > ddd-baseline.json
```

Supplement the mechanical report with:

- language and extension counts;
- current Python docstring convention;
- TSDoc/TypeDoc/API Extractor configuration;
- Doxygen or kernel-doc configuration;
- rustdoc and missing-docs lint status;
- exported/public symbol coverage;
- documentation build and warning counts;
- files that change frequently or attract defects.

Do not treat a present header as correct. Sample headers and label them `missing`, `syntactic`, `useful`, `stale`, or `contradicted`.

## Phase 2: choose profiles and policy

Select one documented profile per language using `language-profiles.md`. Record:

- required file-header contract;
- public API coverage threshold;
- exclusions and how generated code points back to its generator;
- authoritative location for declaration/definition docs;
- validation commands;
- the touched-file rule;
- ownership for documentation failures.

For Python, measure the dominant style before choosing Google or NumPy. If a style migration is necessary, convert whole coherent modules or packages; never leave mixed section syntax in one file.

## Phase 3: prioritize semantic boundaries

Rank files using evidence rather than size alone:

1. package, crate, library, service, or executable entry points;
2. public API and cross-package boundaries;
3. persistence, network, filesystem, process, FFI, and security boundaries;
4. state machines, concurrency coordinators, schedulers, and ownership hubs;
5. high fan-in/fan-out or high-churn files;
6. complex algorithms and domain rules;
7. leaf helpers and straightforward adapters;
8. tests, with special attention to fixtures, oracles, environment needs, and unusual execution.

Within a header/source pair, document the public header contract before implementation detail. Within Rust, document crate and module navigation before every leaf item. Within TypeScript, document package/module entry points before internal exports.

## Phase 4: run a pilot

Choose a small vertical slice containing one entry point, one public abstraction, one side-effect boundary, and representative tests.

For every pilot file:

1. Read implementation, types, tests, call sites, and configuration.
2. Draft the file contract from verified facts.
3. Document changed or public APIs.
4. Add a tested example where it improves understanding.
5. Build native docs and run code tests.
6. Ask a reviewer to read only directory context and file headers, then explain the slice and choose which implementation file to open for a sample change.
7. Revise the template and policy based on failures.

Success means a reader routes correctly and docs remain concise, not that every optional heading is present.

## Phase 5: migrate in bounded batches

Use coherent batches such as one package, component, or architectural layer. Keep each batch small enough for semantic review.

Apply this per-file sequence:

1. Classify the file's role and authoritative documentation location.
2. Extract evidence from code, tests, call sites, and config.
3. Write the opening contract.
4. Add or repair public and non-obvious API docs.
5. Remove comments that merely narrate code or conflict with the new contract.
6. Run formatter, linter, documentation build, examples/doctests, and tests.
7. Review the diff for accidental behavior or formatting churn.

Do not use an LLM or script to mass-fill semantic prose without file-level verification. Automation may insert syntax scaffolds, inventory symbols, or report missing fields; a reviewer must establish meaning.

## Phase 6: ratchet enforcement

Adopt enforcement in this order:

1. Require compliant headers and API docs for new files.
2. Require them for materially touched files.
3. Store a baseline of existing failures or restrict linting to changed paths.
4. Reduce the baseline batch by batch.
5. Enable repository-wide failure only when legacy debt is intentionally cleared.

Useful gates include:

- bundled file-header audit;
- Python docstring lint and Sphinx/numpydoc validation;
- `eslint-plugin-tsdoc`, TypeDoc, or API Extractor;
- Doxygen warnings with `EXTRACT_ALL = NO` after initial exploration;
- rustdoc warnings, `missing_docs`, and `cargo test --doc`.

CI must distinguish missing docs, malformed docs, broken links/examples, and stale or contradicted semantics. Tools catch the first three; review and tests catch the last.

## Phase 7: verify comprehension

Periodically run a header-only routing exercise:

1. Give a reviewer a directory tree plus the opening contract of each file.
2. Ask for the component's responsibility, major flow, state owner, side effects, and likely files for a concrete change.
3. Compare the answer with architecture and implementation.
4. Mark misleading headers as defects and update the guide when the same confusion repeats.

Track useful outcomes:

- percentage of human-maintained files with useful headers;
- percentage of public APIs with contract docs;
- doc-build warning count;
- tested example count;
- stale-doc defects found in review;
- files that agents can exclude after header inspection;
- tokens or lines avoided during repository exploration, when measurable.

Do not optimize for raw comment lines. More prose can increase context cost and drift.

## Migration outputs

Produce:

- a baseline report with exclusions and confidence limits;
- the chosen language profiles and validation commands;
- a risk-ranked migration plan;
- a reviewed pilot;
- bounded, behavior-neutral migration batches;
- a touched-file/new-file CI ratchet;
- a remaining-debt list with owners or next boundaries;
- evidence from doc builds, doctests/examples, and header-only comprehension checks.
