# Measurement contract

## Outcomes before proxies

Compare a fixed task set under the same agreed R and acceptance. Preserve available
requests, corrections, actions, artifacts, and acceptance evidence. Semantic labels
need locations and adjudication; counts alone cannot establish their truth. Report
the sample, exclusions, unknowns, and the following denominators:

| Measure | Event and denominator / cost boundary |
| --- | --- |
| Requirement omission / substitution | Agreed requirement absent / replaced without authorization; count each separately over requirements assessed against delivered behavior |
| User correction burden | Turns or recorded active minutes restoring agreed goals, scope, or facts; exclude new requirements and ordinary choices |
| Recurrence | Same labeled failure after explicit correction / later eligible opportunities; record the failure definition and correction point |
| Qualified delivery / extra review cost | Elapsed and user time, calls, usage, and billed cost through agreed acceptance; isolate incremental review and repair costs against the stated comparison; report unfinished/failed tasks and spent costs separately |
| Spec staleness / contradiction | Clauses conflicting with R or each other, or retaining superseded decisions / clauses inspected; identify clause pairs and consequences |
| Fixed-fault detection / refactor false blocking | Caught / eligible known faults; false blocks / independently verified behavior-preserving refactors; keep operators, surviving/equivalent cases, tool failures, and adjudication explicit |
| Evidence recall / erroneous blockers | Retrieved relevant / all relevant reference items; blocks lacking an R/evidence/consequence basis / adjudicated blockers; record eligibility and locations |

The script below computes file tokens and static graph proxies. Inspect manifests
and measure representative build/run commands separately for dependency and operational
burden. Distinguish **deterministic computation** over fixed files/logs/labels,
**semantic annotation**, and **controlled experiments**. Unobserved data and
zero-denominator rates are null. Manual walkthroughs test rule usability, not improved
agent behavior. Neither comment counts nor token savings establish outcome gains.
Choose only measures that inform this task; the table requires no new automation,
external judge, or composite score.

## Basis for additions, deletions, and revisions

- [Fowler](https://refactoring.com/) defines refactoring by preserved observable
  behavior; [AlOmar et al.](https://arxiv.org/abs/2106.13900) map complementary
  preservation checks. Separate deliberate behavior changes and test the affected
  contracts instead of inferring equivalence from a smaller diff.
- [Kim et al.](https://www.microsoft.com/en-us/research/publication/an-empirical-study-of-refactoring-challenges-and-benefits-at-microsoft/)
  observed size growth alongside reduced dependencies and complexity in studied
  modules. Count size separately from demonstrated maintenance benefits.
- [Sommers](https://publicationsncte.org/content/journals/10.58680/ccc198015930)
  motivates revising meaning across the whole text;
  [McNamara et al.](https://doi.org/10.1207/s1532690xci1401_1) found comprehension
  interacts with reader knowledge and coherence. Preserve the explanation needed
  by the intended reader. These human studies do not prove model behavior.
- [LLMLingua](https://aclanthology.org/2023.emnlp-main.825/) evaluates compressed
  prompts on downstream tasks. Likewise, assess an instruction edit on its actual
  tasks and model; its results do not validate arbitrary skill deletion. Until
  evaluated, report content/loading checks separately from behavioral equivalence.

## Runtime and commands

Python >=3.11; `scripts/measure.py` declares `tiktoken==0.12.0` using PEP 723.
`uv run /absolute/path/scripts/measure.py --help` reads that declaration. With an
existing environment: `python -m pip install tiktoken==0.12.0`, then run with Python.
The first encoding load may fetch the public vocabulary into tiktoken's cache;
set `TIKTOKEN_CACHE_DIR` to a writable/prewarmed cache for offline use. No model API
or LLM judge is used. Git is required only for default git selection. External
extractors are optional and separately installed; the script invokes none of them.

```bash
python /path/to/scripts/measure.py /project --python-root src \
  --entry app.cli --json /tmp/before.json
python /path/to/scripts/measure.py /project --python-root src \
  --entry app.cli --baseline /tmp/before.json --json /tmp/after.json
python /path/to/scripts/measure.py /plain-directory --selection walk
python -m unittest discover -s /path/to/overengineering/tests -v
```

Reports must be outside the measured root. Exit 0 means measurement completed,
including a partial result with explicit gaps; exit 2 means invalid input or an
unavailable required dependency/graph. Always inspect `graph.missing`, file
`missing`, `graph.coverage`, and `graph.metadata.limitations`. Empty graph is valid:
N=E=reachable pairs=0, PC and cycle ratio=null. Missing structural extraction is
not an empty graph: non-Python source without `--graph` is an error.

## Selection and size

Default: `git ls-files --cached --others --exclude-standard` relative to the root;
untracked nonignored files are included. Deleted tracked files remain explicit
unreadable records. Use `--selection walk` outside Git; this intentionally does
not implement .gitignore. Symlinks, common build/cache/vendor directories, .env
files and unsupported extensions are excluded. Git-ignored files are omitted by
Git and not individually inventoried. JSON retains included paths, hashes and
counts, explicit/default exclusions, and missing reasons; no source text is saved.
There is no generated-code detector: review the manifest and use repeatable
`--exclude 'generated/*'` globs. Vendored or generated code outside standard excluded
directories must be explicitly excluded, consistently before and after.

Recognized source: .py, .rs, .ts, .tsx, .js, .jsx, .mjs, .cjs. Docs: .md, .rst, .txt,
.adoc. Config: .toml, .json, .yaml, .yml, .ini, .cfg, .sh. Other languages are not
covered. Whole-file classification defaults to documentation/config by extension,
then tests by test/tests/__tests__ path, test_* or *_test/.test/.spec stem or
conftest.py; remaining source is production. Last matching
`--role 'GLOB=production|tests|documentation|configuration'` wins (choose one role).
Inline tests and doc examples are not split from their containing files. Tokens
for a Rust file containing `#[cfg(test)]` therefore include its tests in that
file's role; state this gap rather than estimating an unsupported allocation.

UTF-8 is decoded strictly with no newline normalization. Count ordinary tokens
(special-looking strings are source text) with fixed `cl100k_base`, sum per file;
do not tokenize a concatenated repository or estimate from characters/lines.
Unreadable/invalid UTF-8 files have null counts. Role totals are null if any member
is missing, alongside known subtotal and missing paths. Empty enumerated roles
have zero counts. Bytes and physical text lines are supplementary, not scores.

## Graph extraction and normalization

Edges point from dependent to dependency. Always retain isolates. External
packages are outside this internal graph; record unresolved/internal exclusions.
Graph scope covers all selected source roles, including tests; use explicit
exclusions for a production-only graph. Do not compare differently scoped graphs.

**Python built-in:** `ast.parse` over selected Python files, module node per file
(package __init__.py is its package node). `--python-root src` chooses import roots;
repeat for several roots. The longest containing root assigns each file's import
identity; duplicate identities are an error, not merged. Import roots do not
simulate runtime sys.path. Choose the parent directory as import root when
analyzing a package so relative imports retain its real package name.
Resolve local `import`, absolute/relative `from`, and known imported submodules;
include known package initialization modules. AST sees imports inside functions,
optional branches and TYPE_CHECKING, so this is conservative static coupling.
No project code is executed. Syntax failures, files outside import roots and
recognized dynamic import sites are reported as gaps. External-or-unresolved
imports are listed together for inspection: unresolved internal names can require
a corrected source root or external graph. Namespace package initialization,
dynamic/aliased import calls, star re-export targets and call/data flow are not
fully modeled. Metrics are exact for the extracted graph, not all runtime edges.

**TypeScript/JavaScript:** use dependency-cruiser with the project's resolution
settings and JSON output, e.g. an already installed
`depcruise src test --no-config --output-type json > /tmp/cruise.json`. Supply
`--ts-config tsconfig.json` where needed. Normalize `modules[].source` into file
nodes, and `dependencies[].resolved` into dependent→dependency edges only for
internal selected sources. Preserve dependency-free module records. Inventory
unresolved imports, missing alias resolution, and skipped files. Record exact
version, command, roots and config identity; do not run an unpinned download merely
to measure. The script accepts the schema below, not raw depcruise JSON.

**Rust:** use cargo-modules dependency DOT for the chosen crate/target/features.
Record version, command, features, target, cfg and source map. Do not use a module
hierarchy graph as a dependency graph, and do not use `--no-uses` to remove the
dependency evidence. DOT has items and modules plus `owns` and `uses` edges. Using
a real DOT parser or the extractor's structured API, map every internal item's
owner to its nearest enclosing *module* via ownership information, retain all
modules including isolates, and keep only use/dependency edges. No Rust regex
parser is bundled. Export item nodes with explicit `owner` below or pre-collapse
them to module nodes. Never truncate the path blindly: associated functions/types
and inline modules make the last `::` segment insufficient to infer ownership.
External crate/sysroot nodes are outside the internal graph. Map inline modules
to their actual source file(s); several modules may share one file. The loader
collapses owners, unions their files, deduplicates edges and drops between-item
edges internal to one owner (including recursive item calls); these are not
architectural self cycles. An explicit module→itself edge remains a self cycle.
Do not silently mix items and modules in N.

**pydeps alternative:** export structured imports with `--max-bacon 0`, inspect
`--noise-level` filters, disable depth coalescing and retain isolates. The default
two-hop output is not a whole-project graph. Convert `imports`, not the reversed
`imported_by` relation, into the schema. Record filters and missing modules.

### Accepted graph v1

```json
{
  "schema_version": 1,
  "scope": "all selected internal sources, crate demo --lib, default features",
  "granularity": "module",
  "extractor": {"name": "cargo-modules", "version": "record-installed-version", "command": "record-exact-command-and-config"},
  "limitations": ["chosen crate/target only; macro expansion follows extractor"],
  "unresolved": [],
  "nodes": [
    {"id": "demo::a", "kind": "module", "files": ["src/a.rs"]},
    {"id": "demo::a::f", "kind": "item", "owner": "demo::a", "files": ["src/a.rs"]},
    {"id": "demo::b", "kind": "module", "files": ["src/b.rs"]}
  ],
  "edges": [["demo::a::f", "demo::b"]]
}
```

For TS use `granularity: file`, kind `file`, root-relative paths as IDs and file
associations. Python imports can also be supplied in this schema. Node IDs are
unique before collapsing; owners identify final modules; files are root-relative
without `..`. Each owner must have a module node even when it has no edges.
`files: []` is allowed but explicitly missing for closure tokens. Missing or
excluded source files are never assigned zero tokens. `unresolved` and
`limitations` are mandatory lists, even when known empty. Include normalizer
version/config in extractor provenance. Input hash is recorded as evidence, but
does not prevent comparing changed edges from the same extraction policy.

## Formulas and interpretation

For N observed nodes, A[i,j]=1 means i directly depends on j. Let V be the
**reflexive** transitive closure: V[i,i]=1. PC = sum(V[i,j]) / N², represented as a
fraction in JSON. Reachable pair count and N are also reported. Visible fan-out
is row sum; visible fan-in is column sum. Direct fan counts exclude self. PC is
dependency exposure, not the probability of a defect or an effort estimate.

Cycles are strongly connected components of size >1, plus explicit singleton
self loops. Cyclic ratio = nodes in cyclic SCCs / N; largest cycle is the largest
such SCC, not the largest of all SCCs. Reflexive closure does not itself make every
node cyclic. Hotspots report both direct and visible fan-in/out. The exact
algorithm condenses SCCs, uses DAG reachability bitsets and no recursion; worst
case memory is quadratic in N bits, so very large graphs may need an agreed,
explicitly reported subsystem boundary. Never silently truncate.

`--entry ID` computes reachable nodes including entries; repeat for their union.
Tokens = sum of whole-file tokens over the union of their file associations, once
per file. It is an upper-bound file context under this graph, not runtime usage
or the minimum context needed for a change. Shared files/inline modules are not
double-counted. Unknown mapping yields null tokens plus a known subtotal.

Chain A→B→C: reachable pairs=6, N²=9, PC=2/3, no cycles. A↔B plus isolated C:
pairs=5, PC=5/9, cyclic ratio=2/3, largest cycle=2. Three isolated nodes: PC=1/3.
Removing an isolate can raise PC even while reducing absolute cost.

Baseline JSON reports `after - before`, additions/removals and policy mismatches.
Incompatible encoding, selection, roles, source roots, extractor/options, scope,
granularity or entry sets produce null deltas. Graph gaps suppress structural and
entry deltas; missing role totals suppress that role's delta. Comparable proxies
still require independently established requirements equivalence. No baseline
comparison proves preserved behavior or a reduction in unmeasured effort.
