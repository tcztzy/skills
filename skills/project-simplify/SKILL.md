---
name: project-simplify
description: Reduce repository complexity by de-vendoring large third-party sources and replacing them with pinned release artifacts, checksum verification, and minimal subset extraction. Use when Codex needs to shrink Git history, migrate external fixtures (especially LLVM/Clang tests), design artifact lock manifests, or build repeatable fetch/extract workflows.
---

# Project Simplify

## Core workflow

1. Audit repository weight and churn sources (`git count-objects -vH`, largest paths, frequently updated vendor trees).
2. Classify each large path:
   - Keep in Git only if it is small and heavily edited by this project.
   - Externalize if it is upstream-owned, large, or frequently refreshed.
3. Create or update a lock manifest per artifact (`name`, `version`, `url`, `sha256`, `license`, extraction rules).
4. Fetch from stable release archives, verify checksums, and extract only needed subsets.
5. Commit only curated outputs and lock metadata; keep archives and caches out of Git.
6. Validate reproducibility by deleting cache and re-running fetch/extract.

## Non-negotiable rules

- Never commit large upstream tarballs or mirrored source trees into the repository.
- Pin exact artifact versions and hashes; fail immediately on mismatch.
- Prefer stable (non-RC) upstream release tags.
- Extract only required test subsets (for LLVM, avoid importing the whole test suite tree).
- Keep local patches separate and explicit (small patch files or transform scripts).

## Use bundled script

Use `scripts/fetch_release_tarball.py` to download, hash-verify, and extract subsets safely.

Example:

```bash
python scripts/fetch_release_tarball.py \
  --url "https://github.com/llvm/llvm-project/releases/download/llvmorg-22.1.0/test-suite-22.1.0.src.tar.xz" \
  --sha256 "<fill-me>" \
  --dest tests/external/llvm \
  --include "SingleSource" \
  --include "MultiSource" \
  --lock-file tests/external/llvm.lock.json \
  --clean-dest
```

## CI integration checklist

- Add a pre-test fetch target (or tox env) that materializes required external fixtures.
- Cache archive downloads between CI runs.
- Verify lock files in review (version/hash changes require explicit justification).
- Ensure tests fail clearly when artifacts are missing or checksum verification fails.

## Reference material

Read `references/external-artifacts-playbook.md` for:
- techniques borrowed from `python-cmake-buildsystem` and `python-build-standalone`,
- LLVM release asset conventions (`.src.tar.xz`, `.sig`, `.jsonl`),
- suggested lock manifest structure.
