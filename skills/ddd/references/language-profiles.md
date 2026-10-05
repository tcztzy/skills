# Language profiles

Use one native documentation system per language and one Python docstring style per repository. The shared DDD contract is semantic; syntax remains native to the ecosystem.

## Contents

- [Shared file contract](#shared-file-contract)
- [Python](#python)
- [TypeScript](#typescript)
- [C](#c)
- [C++](#c-1)
- [Rust](#rust)
- [Cross-language review rules](#cross-language-review-rules)

## Shared file contract

Place a compact routing contract at the start of every human-maintained source file. Include only applicable information:

1. **Summary:** one line stating the file's purpose.
2. **Role:** where it sits in the architecture and what it owns.
3. **Key abstractions:** public exports, entry points, or protocols.
4. **Flow:** important inputs -> transformations -> outputs.
5. **Side effects:** I/O, mutation, persistence, network, process, or global state.
6. **Constraints:** invariants, ordering, ownership, concurrency, security, or performance limits.
7. **Failure model:** caller-visible errors, panics, exceptions, status codes, or partial effects.
8. **Read next:** a precise pointer to the deeper design or paired interface when useful.

Do not turn these labels into empty boilerplate. Prefer a short paragraph when it communicates the same contract more naturally. Keep detail on each API item rather than copying the whole API into the file header.

## Python

### Select one style

- Preserve the repository's established style.
- If no style exists, choose **Google style** for applications, services, CLIs, and general libraries.
- Choose **NumPy style** for scientific, numerical, array-oriented, and data-analysis libraries.
- Do not combine Google `Args:` syntax with NumPy `Parameters`/underline syntax.
- Follow PEP 257 in both profiles: a docstring is the first statement, begins with a one-line summary, separates details with a blank line, and does not repeat an introspectable signature.

### Google-style file contract

Use triple double quotes. A module summary and usage are standard Google guidance; the short DDD labels below extend the module description without changing function-section syntax.

```python
"""Route accepted orders from the HTTP boundary to the domain service.

Role:
    Adapt validated transport requests into domain commands. This module owns
    no business rules and is the only layer that maps domain errors to HTTP.
Key exports:
    `create_order` handles the endpoint; `OrderResponse` is its wire model.
Flow:
    Request model -> domain command -> order service -> response model.
Side effects:
    Calls the order service and emits request metrics; it does not commit data.
"""
```

Document public, nontrivial, or non-obvious functions. With type annotations, describe semantics rather than repeating types.

```python
def reserve_stock(sku: str, quantity: int) -> Reservation:
    """Reserve available units for one checkout attempt.

    Args:
        sku: Stable catalog identifier.
        quantity: Positive number of units requested.

    Returns:
        A reservation that remains valid until its documented expiry.

    Raises:
        OutOfStockError: The requested quantity is not currently available.
        ValueError: `quantity` is not positive.
    """
```

Use `Yields:` for generators and `Attributes:` for public class attributes. Mention mutation, environment dependencies, retry/idempotency behavior, and restrictions when relevant. Keep summary voice consistent within the repository.

### NumPy-style file contract

Use the standard order: summary, extended summary, routine listings, `See Also`, `Notes`, `References`, and `Examples` as applicable. Put architectural facts in the extended summary or `Notes`; use a recognized routine-listing section for exports.

```python
"""Transform calibrated detector frames into normalized spectra.

This module is the numerical boundary between detector-specific arrays and the
instrument-independent spectrum model. Raw frames are validated, corrected,
and reduced; persistence is delegated to the caller.

Functions
---------
reduce_frame
    Validate and reduce one detector frame.
estimate_background
    Estimate the background without mutating the input array.

Notes
-----
Inputs use row-major detector coordinates. Returned wavelengths are in nm.
The routines allocate output arrays and do not modify caller-owned buffers.
"""
```

Use numpydoc sections in their standard order and include only applicable sections:

```python
def reduce_frame(frame: NDArray[np.float64], gain: float) -> Spectrum:
    """Reduce a calibrated detector frame to a spectrum.

    Parameters
    ----------
    frame : ndarray of float
        Two-dimensional calibrated intensities. The array is not mutated.
    gain : float
        Positive detector gain in electrons per count.

    Returns
    -------
    Spectrum
        Wavelengths in nm paired with normalized intensity values.

    Raises
    ------
    ValueError
        If `frame` is not two-dimensional or `gain` is not positive.
    """
```

NumPy style traditionally includes parameter and return types even when annotated. Follow the repository's numpydoc validator instead of inventing hybrid rules.

### Python validation

Use the configured stack. Common choices include Ruff's `D` rules with `lint.pydocstyle.convention = "google"` or `"numpy"`, `numpydoc validate <importable-object>`, numpydoc validation during Sphinx builds, or a repository's existing docstring checker. Do not enable mutually incompatible conventions at the same time. Treat doctest examples as tests when the project uses them.

## TypeScript

Use `/** ... */` TSDoc comments. The TypeScript type system owns type shapes; documentation owns semantics, units, mutation, lifecycle, error behavior, and examples.

### File contract

- For a package entry point or API Extractor entry point, use the TSDoc core `@packageDocumentation` marker.
- For an ordinary module rendered by TypeDoc, use TypeDoc's `@module` marker.
- Put the marked block before imports and make it the first documentation comment. A line-comment license may precede it.
- If the project uses another TSDoc consumer, verify its configured custom tags instead of silently adding unsupported tags.

```typescript
/**
 * Coordinates cache reads and origin fetches for immutable product records.
 *
 * @remarks
 * **Role:** Owns cache policy between repository callers and the HTTP client.
 *
 * **Key exports:** {@link ProductRepository} is the only supported entry point.
 *
 * **Flow:** Product ID -> cache lookup -> optional origin fetch -> cached record.
 *
 * **Side effects:** Reads and writes the shared cache and may perform HTTP I/O.
 *
 * @module
 */
```

Use a brief summary, optional `@remarks`, then contract tags. Use `@param name - description`, `@returns`, one `@throws` block per relevant exception type, `@typeParam`, `@example`, `@see`, and `{@link ...}` as supported by the selected tool.

```typescript
/**
 * Loads one product, preferring a non-expired cache entry.
 *
 * @param id - Stable product identifier, not a display SKU.
 * @returns The canonical product record; callers may retain it.
 * @throws {@link ProductNotFoundError}
 * Thrown when the origin confirms that `id` does not exist.
 */
export async function loadProduct(id: ProductId): Promise<Product> {
  // ...
}
```

Do not write `@param {string}` in `.ts` files; the signature already expresses it. That form remains useful in checked JavaScript files when JSDoc supplies types.

### TypeScript validation

Use `eslint-plugin-tsdoc` for syntax. Use TypeDoc to build module/API sites or API Extractor when a library needs strict `.d.ts` API review. TypeDoc accepts more than strict TSDoc, so a successful TypeDoc build alone does not prove strict conformance.

## C

Use Doxygen-style `/** ... */` blocks by default. Add `@file` so global declarations are associated with the documented file. Use `@brief` explicitly unless project configuration reliably enables autobrief.

```c
/**
 * @file packet_decoder.c
 * @brief Decodes validated wire packets into owned protocol messages.
 *
 * Role: Implements the wire-to-domain boundary declared in packet_decoder.h.
 * Flow: Byte span -> header validation -> payload decode -> owned message.
 * Side effects: Allocates message payloads; performs no I/O.
 * Invariants: Input buffers remain caller-owned and may be released on return.
 * Failure model: Returns packet_status values and leaves output pointers null.
 */
```

For functions, document `@param[in]`, `@param[out]`, or `@param[in,out]`; ownership, nullability, buffer lengths, units, aliasing, thread/interrupt context, and partial effects; then `@return` or status values. Use `@pre`, `@post`, `@warning`, or `@note` only when they add a real contract.

Keep public API contracts with declarations in headers. In `.c` files, document file role, private contracts, algorithms, and invariants without copying header prose.

For Linux kernel code, follow kernel-doc instead: its symbol-prefixed brief, `@parameter:` fields, `Context:`, and `Return:` sections have their own parser rules. Do not mix kernel-doc and generic Doxygen syntax in one subsystem.

Use a normal leading block for the DDD file contract in a kernel-doc project so the kernel-doc parser does not mistake it for an item. Include `File role:` to distinguish the contract from a license block:

```c
/*
 * Decodes transport frames before they enter the networking state machine.
 *
 * File role: Owns frame validation and dispatch; socket I/O stays with callers.
 * Flow: Byte span -> validated header -> protocol-specific handler.
 * Context: Callable in process context; does not sleep while holding a spinlock.
 */
```

### C validation

Build Doxygen with warnings enabled. For strict projects, keep `EXTRACT_ALL = NO`, enable undocumented/incomplete/parameter warnings as appropriate, and fail CI on warnings after the legacy baseline is under control.

## C++

Use the same Doxygen file block as C, plus C++ contract concepts:

- Put caller-facing contracts with declarations in `.h`, `.hpp`, or module interfaces.
- Put implementation rationale and algorithmic constraints with definitions.
- Document ownership and lifetime for references, pointers, views, spans, callbacks, and returned handles.
- Document exception guarantees with `@throws` and, when material, basic/strong/no-throw guarantees.
- Document templates with `@tparam`, constraints not fully expressed by concepts, and complexity when it affects use.
- Document class invariants, thread safety, lock requirements, iterator/reference invalidation, and move-from state when relevant.
- For override docs, state only behavioral differences unless the repository intentionally copies inherited documentation.

```cpp
/**
 * @file session_pool.h
 * @brief Declares the thread-safe lease boundary for reusable sessions.
 *
 * Role: Owns session lifetime between transport clients and the connection
 * factory. Leases return sessions to the pool when destroyed.
 * Concurrency: Public operations are thread-safe; a lease is single-owner.
 * Failure model: Acquisition reports timeout without mutating pool capacity.
 */
```

Use Doxygen as the conservative default generator. `clang-doc` can consume Doxygen-style comments but remains a tooling choice, not a different contract style.

## Rust

Use inner line doc comments (`//!`) for the crate or file-backed module contract and outer comments (`///`) for the item that follows. Prefer line doc comments because they compose cleanly with Markdown.

```rust
//! Coordinates durable job state between the scheduler and worker runtime.
//!
//! # Architecture
//!
//! This module owns state transitions; transport adapters submit commands but
//! cannot write job state directly.
//!
//! # Flow
//!
//! Validated command -> transition check -> persisted event -> worker signal.
//!
//! # Invariants
//!
//! Job versions increase monotonically and terminal states never transition.
```

For public items, write a one-line summary, details, and a useful copyable example when reasonable. Use conventional sections only when applicable:

- `# Examples`
- `# Errors` for `Result` failure conditions
- `# Panics` for reachable caller-relevant panics
- `# Safety` for every `unsafe` contract
- `# Aborts` and `# Undefined Behavior` when relevant

Do not restate argument or return types. Link related items with intra-doc links. Prefer examples that explain why an API exists, and write fallible examples with `?` rather than casual `unwrap()`.

### Rust validation

Run `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps` when compatible, `cargo test --doc`, and the repository's Clippy/rustdoc lints. Use `#![warn(missing_docs)]` as a migration ratchet and `#![deny(missing_docs)]` only after the baseline is ready.

## Cross-language review rules

- Write summaries that distinguish the file from neighboring files.
- Put stable contracts in documentation and volatile implementation sequences in code.
- Prefer exact units, ownership, state transitions, and error conditions over adjectives.
- Do not promise thread safety, idempotency, atomicity, complexity, or security properties without evidence.
- Avoid author names, change logs, timestamps, and issue narratives in API docs; version control owns history.
- Keep examples minimal, valid, and tested when the ecosystem supports it.
- When a declaration and definition are separate, keep one authoritative caller contract and avoid drift-prone duplication.
