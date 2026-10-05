# Official research sources

Research checked on 2026-08-04. Prefer these primary sources when project conventions or tool behavior need verification.

## Python

- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/): defines module/function/class docstrings, one-line summaries, blank-line structure, and the principle of documenting behavior rather than repeating introspectable signatures.
- [numpydoc style guide](https://numpydoc.readthedocs.io/en/latest/format.html): defines NumPy section names and ordering, parameter/return formatting, module docstrings, notes, references, and examples.
- [numpydoc validation](https://numpydoc.readthedocs.io/en/stable/validation.html): documents the `numpydoc validate` command and Sphinx validation configuration.
- [Google Python Style Guide - Comments and Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings): requires module descriptions, defines `Args:`, `Returns:`/`Yields:`, `Raises:`, and `Attributes:`, and emphasizes caller semantics over implementation detail.
- [Ruff FAQ - NumPy and Google docstrings](https://docs.astral.sh/ruff/faq/#does-ruff-support-numpy-or-google-style-docstrings): documents convention-specific `D`-rule configuration.

Key synthesis: both styles require a useful opening summary and semantic contracts. Their section grammars differ, so select one rather than blending them. Google style is compact with typed Python; NumPy style is richer for scientific API concepts and terminal-readable reference docs.

## TypeScript

- [TSDoc `@remarks`](https://tsdoc.org/pages/tags/remarks/): separates the brief index summary from detailed remarks.
- [TSDoc `@param`](https://tsdoc.org/pages/tags/param/), [`@returns`](https://tsdoc.org/pages/tags/returns/), and [`@throws`](https://tsdoc.org/pages/tags/throws/): define core API contract tags; `@throws` is in the extended standardization group.
- [TSDoc `@packageDocumentation`](https://tsdoc.org/pages/tags/packagedocumentation/): marks package entry-point documentation and must be the first `/**` documentation comment encountered there.
- [TypeDoc doc comments](https://typedoc.org/documents/Doc_Comments.html) and [`@module`](https://typedoc.org/documents/Tags._module.html): describe source comment discovery and the TypeDoc-specific file/module marker.
- [TypeDoc TSDoc support](https://typedoc.org/documents/Doc_Comments.TSDoc_Support.html): explains that TypeDoc parses TSDoc but does not enforce strict conformance.
- [API Extractor doc comment syntax](https://api-extractor.com/pages/tsdoc/doc_comment_syntax/): describes strict package API extraction from emitted declarations and entry-point package documentation.
- [TypeScript JSDoc reference](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html): distinguishes type-carrying JSDoc in JavaScript from documentation tags in TypeScript.

Key synthesis: TSDoc is a syntax/contract model, not a complete generator. Pair it with TypeDoc for module-oriented sites, API Extractor for strict library API review, and `eslint-plugin-tsdoc` for syntax linting. Avoid type annotations in TypeScript comments because the signature owns them.

## C and C++

- [Doxygen - Documenting the code](https://www.doxygen.nl/manual/docblocks.html): defines special C/C++ comment blocks, brief/detailed descriptions, parameter direction, and placement.
- [Doxygen `@file` command](https://www.doxygen.nl/manual/commands.html#cmdfile): associates a block with a source/header file and affects global-symbol extraction.
- [Doxygen configuration](https://www.doxygen.nl/manual/config.html): documents `EXTRACT_ALL`, undocumented/incomplete/parameter warnings, and warnings-as-errors behavior.
- [Google C++ Style Guide - Comments](https://google.github.io/styleguide/cppguide.html#Comments): separates file collection descriptions, declaration usage contracts, definition rationale, lifetimes, nullability, concurrency, and non-obvious implementation comments.
- [Linux kernel-doc](https://docs.kernel.org/doc-guide/kernel-doc.html): defines the kernel-specific function, parameter, `Context:`, and `Return:` grammar.
- [clang-doc](https://clang.llvm.org/extra/clang-doc.html): generates C/C++ documentation and can restrict input to Doxygen-style comments, but its documentation labels the tool early-stage.

Key synthesis: Doxygen is the portable default syntax and generator. Place public contracts at declarations and implementation rationale at definitions. Kernel-doc is a separate ecosystem convention, not a cosmetic Doxygen variant.

## Rust

- [Rust Reference - Comments](https://doc.rust-lang.org/reference/comments.html): defines `///`/`/** */` outer docs and `//!`/`/*! */` inner docs; inner docs commonly document file-backed modules.
- [rustdoc - How to write documentation](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html): recommends a brief summary, details, examples, and relevant panic documentation while avoiding redundant type restatement.
- [rustdoc - Documentation tests](https://doc.rust-lang.org/rustdoc/documentation-tests.html): explains executable documentation examples.
- [Rust API Guidelines - Documentation](https://rust-lang.github.io/api-guidelines/documentation.html): covers crate docs, examples, links, and `Errors`, `Panics`, and `Safety` contracts.
- [RFC 1574 - API documentation conventions](https://rust-lang.github.io/rfcs/1574-more-api-documentation-conventions.html): distinguishes broad module-level navigation from self-contained type documentation and lists conventional headings.
- [Rust Style Guide - Comments and documentation](https://doc.rust-lang.org/stable/style-guide/index.html#comments): prefers outer docs for items and inner docs for module/crate-level documentation.

Key synthesis: Rust has the most integrated solution. Use inner module docs for file routing, outer item docs for APIs, conventional failure/safety sections, intra-doc links, and doctests as the synchronization mechanism.
