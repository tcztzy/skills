---
name: ddd
description: "Make source-code work follow Documentation-Driven Development (DDD) so each human-maintained file begins with an accurate, language-native contract that explains its purpose, system role, public surface, data flow, side effects, and constraints before implementation details. Use when performing any code-related task: exploring or explaining a repository; planning, writing, debugging, reviewing, testing, refactoring, or documenting code; adding files or APIs; changing behavior; or migrating legacy Python, TypeScript, C, C++, Rust, or mixed-language projects. Trigger even when documentation is not explicitly requested, and apply the touched-file rule unless the user asks for a repository-wide migration."
---

# Documentation-Driven Development

Write down the file's purpose and behavior before changing code, then verify those statements against the implementation and tests. The opening contract should help readers decide whether a file is relevant; read the relevant implementation before changing behavior.

## Non-negotiable outcome

For every human-maintained source file created or materially changed:

1. Put a language-native file or module documentation block at the beginning of the file, after only required shebang, encoding, license, or compiler directives.
2. Start with a one-line purpose summary.
3. Explain the file's architectural role and boundary.
4. Name the key public abstractions or entry points.
5. Describe important input -> transformation -> output flow.
6. Record externally visible side effects, state ownership, invariants, failure behavior, concurrency rules, or security constraints when relevant.
7. Keep the header accurate, concise, and useful without restating syntax.

Keep the contract within about 200 words, usually 5-30 lines. A one-to-three-line contract is enough for a trivial declarative file whose role is fully clear. Omit inapplicable fields instead of writing `None`. Exclude generated and vendored files; document their generator or integration boundary instead.

## Load the right reference

- Read [references/language-profiles.md](references/language-profiles.md) before writing or revising documentation. Load only the relevant language sections when context is tight.
- Read [references/legacy-migration.md](references/legacy-migration.md) for repository-wide adoption, undocumented legacy code, migration plans, baselines, or CI ratchets.
- Read [references/official-sources.md](references/official-sources.md) when choosing a tool, resolving a style dispute, or verifying the research basis.
- Run `scripts/check_file_docs.py` to inventory Python, TypeScript, C, C++, and Rust file headers without loading whole files into context.

## Work documentation-first

### 1. Establish local policy

Inspect repository instructions, documentation tooling, formatter and linter configuration, and a few representative public files. Preserve an established language-native style unless it violates a real contract requirement.

Select one profile per language:

- Python: use Google style for general applications and services by default; use NumPy style for scientific, numerical, and data-oriented libraries. Never mix the two section syntaxes in one project.
- TypeScript: use TSDoc syntax; use TypeDoc for source/module sites or API Extractor for strict package API reports.
- C and C++: use Doxygen unless the repository has an established compatible convention. Use kernel-doc only for Linux-kernel-style projects.
- Rust: use built-in rustdoc and doctests.

If the repository has no policy, record the choice in its contributor or agent instructions as part of a migration task. Do not add project-wide policy files during a narrowly scoped code fix unless requested.

### 2. Read architecture before implementation

Start repository exploration with manifests, directory documentation, file headers, exported declarations, and tests. Build a relevance map before opening full files. Read the full relevant implementation, call sites, and tests before modifying behavior.

Treat a stale or contradicted header as a defect. Verify claims against code, types, tests, configuration, and call sites; do not propagate an unverified summary.

### 3. Write the contract before the code

Before implementation, draft or refresh:

- the file contract;
- public API documentation for new or changed behavior;
- examples or doctests when they clarify the contract;
- expected errors, side effects, ownership, and invariants.

Use the contract to expose design ambiguity. If the behavior cannot be explained concisely, resolve the boundary or split responsibilities before adding code.

### 4. Implement against the contract

Keep signatures and static types as the source of structural type facts. Use documentation for semantics the type system does not express: units, valid ranges, ordering, ownership, mutation, idempotency, blocking, thread safety, error conditions, performance traps, and security assumptions.

Use inline comments for local **why**, subtle algorithms, and non-obvious tradeoffs. Do not narrate obvious statements or copy the implementation into prose.

Document public/exported APIs and any private abstraction whose contract is not obvious. For overrides, inherited APIs, and declaration/definition pairs, document differences at the narrowest authoritative location rather than duplicating text.

### 5. Verify documentation and implementation

After changing code:

1. Re-read the file header and changed API docs without relying on implementation context.
2. Confirm every claim remains true.
3. Run the project's documentation build, doc linter, doctests, type checker, and relevant tests when available.
4. Run the bundled header audit on changed source paths.
5. Report documentation changes and validation with the code changes.

Do not declare completion with stale docs, examples that do not compile, or public behavior absent from the contract.

## Use the touched-file rule

For ordinary coding tasks, improve only files materially changed by the task:

- Add or repair the file contract in each touched human-maintained source file.
- Update docs for every changed public contract.
- Avoid opportunistic repository-wide comment churn.
- If a required header would be misleading without a broader investigation, document only verified facts and report the remaining migration debt.

For a dedicated legacy conversion, follow the staged workflow in [references/legacy-migration.md](references/legacy-migration.md). Do not bulk-generate semantic documentation from filenames or symbol lists and present it as verified.

## Audit file headers

Run from the target repository:

```bash
python3 /path/to/ddd/scripts/check_file_docs.py src include
```

Produce machine-readable output for a migration baseline:

```bash
python3 /path/to/ddd/scripts/check_file_docs.py . --format json > ddd-baseline.json
```

The checker looks for leading documentation markers and a summary of at least 20 trimmed characters by default. It does not assess usefulness, semantic accuracy, or complete documentation syntax; review the implementation and tests and run the language's documentation tools.

Scanner boundaries:

- Python requires a module docstring starting within the first 80 lines and parses the entire file using the running Python version. Other languages inspect only the first 80 lines; a block must finish within that prefix. Change the limit with `--max-lines`.
- TypeScript requires the first `/** */` block to contain `@module` or `@packageDocumentation`. C/C++ requires a Doxygen `/** */` or `/*! */` block with `@file`; use `--c-style kernel-doc` for a normal block with `File role:`. Rust accepts `//!` and `/*! */`.
- Non-Python headers must precede source code. Leading comments, shebangs, C/C++ preprocessor directives, and simple single-line Rust inner attributes are allowed. This is a structural scan, not a full lexer; use native tools for nested comments and complex attributes.
- Files must be UTF-8. Symlinks and common vendor, environment, cache, and build directories are excluded. Generated-file markers in the first eight lines cause a heuristic skip; use `--include-generated` to audit those files too.
- Exit status is 0 when no checked file fails, 1 when a header fails, and 2 for invalid input paths/options or no supported source files. Inspect the JSON `skip` count when using the result as a coverage baseline.

Run the scanner's regression tests with `python3 -m unittest discover -s /path/to/ddd/tests -v`.

## Quality gate

Accept documentation only when it is:

- **Routing-useful:** the opening summary lets a reader decide whether to continue.
- **Contract-focused:** it explains purpose and observable behavior, not line-by-line mechanics.
- **Specific:** it names boundaries, side effects, invariants, and failure conditions that matter.
- **Non-duplicative:** it does not repeat types, signatures, inherited text, or obvious code.
- **Verifiable:** claims are grounded in code, tests, configuration, or authoritative design material.
- **Synchronized:** the same change updates code, tests, examples, and docs.
- **Tool-valid:** native documentation generation and linting succeed.

## Expected output

For a code change, produce:

- code and tests that implement the requested behavior;
- an accurate file contract for every touched human-maintained source file;
- updated docs for changed public or non-obvious contracts;
- documentation/tool validation results.

For repository exploration, produce a header-derived architecture map, identify which full files require inspection, and flag stale or missing contracts.

For legacy migration, produce a measured baseline, chosen language profiles, prioritized batches, a pilot, a non-regression ratchet, and verified documentation changes.
