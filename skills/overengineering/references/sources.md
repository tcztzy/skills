# Sources consulted

- [SciTools direct propagation cost](https://docs.scitools.com/metrics/DirPropagationCost.html)
  is direct dependency density. Its linked [propagation cost](https://docs.scitools.com/metrics/PropagationCost.html)
  uses the visibility matrix including indirect dependencies; do not confuse them.
- [MacCormack & Sturtevant, 2016, §3.2–3.3](https://www.hbs.edu/ris/Publication%20Files/2016-JSS%20Technical%20Debt_d793c712-5160-4aa9-8761-781b444cc75f.pdf)
  defines visibility as transitive closure with the diagonal inserted, and studies
  associations between coupling and maintenance activity in two systems. It does
  not establish a universal overengineering score or prove causality for a new project.
- Google Testing Blog: [change detector tests](https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html)
  and [behavior versus implementation](https://testing.googleblog.com/2013/08/testing-on-toilet-test-behavior-not.html)
  explain why mechanically mirroring implementation adds maintenance without an
  independent behavioral oracle, while some internal constraints are legitimate.
- [PIT concepts](https://pitest.org/quickstart/basic_concepts/) distinguishes caught,
  surviving, equivalent, uncovered, nonviable, timed-out, and failed mutants.
- [cargo-modules](https://github.com/regexident/cargo-modules) exports Rust dependency
  DOT with modules and items, and separate ownership/use edges. Item-level counts
  are not module-level counts. Inspect its version, target, features and cfg.
- [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) provides
  TypeScript/JavaScript dependency graphs. Preserve tsconfig and resolution settings.
- [pydeps](https://github.com/thebjorn/pydeps) can supply Python graphs, but defaults
  to two hops (`--max-bacon 2`). Use `--max-bacon 0`, inspect noise filters, and
  retain isolates before claiming whole-project coverage. The bundled AST mode
  avoids this truncation and does not import the target project.
- [tiktoken encoding definitions](https://github.com/openai/tiktoken/blob/main/tiktoken_ext/openai_public.py)
  fixes the `cl100k_base` vocabulary and its verified resource hash. Tokens here
  measure source text size; they are not a bill or a complete model request size.
