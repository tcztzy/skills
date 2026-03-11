# External Artifacts Playbook

## Why this pattern

Keep large upstream sources out of Git history. Pin exact release archives and verify integrity before extraction. This keeps the repository small and reviewable while remaining reproducible.

## Patterns from real projects

### 1) `python-cmake-buildsystem`

- `DOWNLOAD_SOURCES` is enabled by default.
- The build downloads CPython source from python.org and verifies checksums before extraction.
- Version-to-checksum mappings are hard-coded in `CMakeLists.txt`.

References:
- <https://github.com/python-cmake-buildsystem/python-cmake-buildsystem/blob/master/README.rst>
- <https://github.com/python-cmake-buildsystem/python-cmake-buildsystem/blob/master/CMakeLists.txt>

### 2) `python-build-standalone`

- Uses a centralized downloads catalog (`pythonbuild/downloads.py`) with `url`, `size`, `sha256`, and version metadata.
- Mirrors selected upstream files for availability and still keeps hashes pinned.
- Produces source archives (`.tar.zst`) and machine-readable metadata (`PYTHON.json`) for downstream consumers.

References:
- <https://github.com/astral-sh/python-build-standalone/blob/main/pythonbuild/downloads.py>
- <https://github.com/astral-sh/python-build-standalone/blob/main/docs/distributions.rst>

### 3) LLVM releases

- LLVM publishes stable release tarballs for `llvm-project` and `test-suite`.
- Release assets include detached signature files (`.sig`) and provenance metadata (`.jsonl`).
- Prefer a stable tag (non-RC) and pin one specific release in your lock data.

References:
- <https://github.com/llvm/llvm-project/releases>
- <https://github.com/llvm/llvm-project/releases/tag/llvmorg-22.1.0>

## Recommended policy for xcc-like compiler repos

1. Keep upstream archives out of Git; keep only your lock/manifest files and extraction scripts.
2. Pin `url + sha256 + license + version` for each artifact.
3. Extract only required subsets (for example, selected LLVM/Clang test files), not the whole tarball.
4. Commit a curated manifest that records which files were extracted and from which archive.
5. Reuse local cache directories in CI to avoid repeated network cost.
6. Revalidate checksums on every fetch and fail closed on mismatch.

## Suggested lock manifest fields

```json
{
  "name": "llvm-test-suite",
  "version": "22.1.0",
  "url": "https://github.com/llvm/llvm-project/releases/download/llvmorg-22.1.0/test-suite-22.1.0.src.tar.xz",
  "sha256": "<fill-me>",
  "signature_url": "https://github.com/llvm/llvm-project/releases/download/llvmorg-22.1.0/test-suite-22.1.0.src.tar.xz.sig",
  "include": [
    "SingleSource/",
    "MultiSource/"
  ],
  "strip_components": 1,
  "license": "Apache-2.0 WITH LLVM-exception"
}
```

## Example command

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
