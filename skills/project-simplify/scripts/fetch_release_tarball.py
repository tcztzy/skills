#!/usr/bin/env python3
"""Fetch a pinned release tarball and extract a curated subset safely."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
from typing import Iterable
from urllib import parse
from urllib import request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download a release tarball, verify SHA256, and extract only selected paths."
        )
    )
    parser.add_argument("--url", required=True, help="Archive URL (http/https/file)")
    parser.add_argument(
        "--sha256",
        required=True,
        help="Expected SHA256 for the full archive",
    )
    parser.add_argument(
        "--dest",
        required=True,
        type=Path,
        help="Destination directory for extracted files",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".cache/project-simplify"),
        help="Archive cache directory",
    )
    parser.add_argument(
        "--archive-name",
        help="Optional archive filename in cache (default: from URL)",
    )
    parser.add_argument(
        "--strip-components",
        type=int,
        default=1,
        help="Number of leading path components to strip during extraction",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help=(
            "Keep only paths under this prefix after strip-components. "
            "Repeat for multiple prefixes."
        ),
    )
    parser.add_argument(
        "--clean-dest",
        action="store_true",
        help="Delete destination directory before extraction",
    )
    parser.add_argument(
        "--lock-file",
        type=Path,
        help="Optional JSON file that records the fetched artifact metadata",
    )
    return parser.parse_args()


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while True:
            chunk = file.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def download_to_cache(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=destination.parent,
        prefix=f"{destination.name}.",
        suffix=".part",
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)
        with request.urlopen(url, timeout=60) as response:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                temp_file.write(chunk)
    temp_path.replace(destination)


def normalize_prefix(prefix: str) -> str:
    cleaned = prefix.strip().strip("/")
    if not cleaned:
        return ""
    parts = [part for part in PurePosixPath(cleaned).parts if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise ValueError(f"Invalid include prefix: {prefix!r}")
    return "/".join(parts)


def normalize_member(member_name: str, strip_components: int) -> PurePosixPath | None:
    parts = [part for part in PurePosixPath(member_name).parts if part not in ("", ".")]
    if any(part == ".." for part in parts):
        return None
    if len(parts) <= strip_components:
        return None
    stripped = parts[strip_components:]
    if any(part == ".." for part in stripped):
        return None
    return PurePosixPath(*stripped)


def match_prefixes(path: PurePosixPath, prefixes: Iterable[str]) -> bool:
    path_text = path.as_posix()
    for prefix in prefixes:
        if not prefix:
            return True
        if path_text == prefix or path_text.startswith(f"{prefix}/"):
            return True
    return False


def safe_join(root: Path, relative: PurePosixPath) -> Path:
    target = root.joinpath(*relative.parts)
    root_abs = root.resolve()
    target_abs = target.resolve(strict=False)
    common = Path(os.path.commonpath([str(root_abs), str(target_abs)]))
    if common != root_abs:
        raise ValueError(f"Refusing path traversal: {relative.as_posix()}")
    return target


def extract_subset(
    archive_path: Path,
    dest: Path,
    strip_components: int,
    include_prefixes: list[str],
) -> list[str]:
    extracted: list[str] = []
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, mode="r:*") as archive:
        for member in archive.getmembers():
            relative = normalize_member(member.name, strip_components)
            if relative is None:
                continue
            # Ignore metadata files produced by macOS tar tooling.
            if "__MACOSX" in relative.parts or any(
                part.startswith("._") for part in relative.parts
            ):
                continue
            if include_prefixes and not match_prefixes(relative, include_prefixes):
                continue
            if member.issym() or member.islnk():
                print(f"skip link: {member.name}")
                continue
            destination = safe_join(dest, relative)
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            source = archive.extractfile(member)
            if source is None:
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as output:
                shutil.copyfileobj(source, output)
            mode = member.mode & 0o777
            if mode:
                destination.chmod(mode)
            extracted.append(relative.as_posix())
    extracted.sort()
    return extracted


def main() -> int:
    args = parse_args()
    expected_sha256 = args.sha256.lower()
    include_prefixes = [normalize_prefix(prefix) for prefix in args.include]

    archive_name = args.archive_name
    if not archive_name:
        archive_name = Path(parse.urlparse(args.url).path).name
    if not archive_name:
        raise SystemExit("Cannot infer archive name from URL. Set --archive-name.")

    archive_path = args.cache_dir / archive_name
    if archive_path.exists() and sha256sum(archive_path) == expected_sha256:
        print(f"cache hit: {archive_path}")
    else:
        if archive_path.exists():
            archive_path.unlink()
        print(f"downloading: {args.url}")
        download_to_cache(args.url, archive_path)

    actual_sha256 = sha256sum(archive_path)
    if actual_sha256 != expected_sha256:
        raise SystemExit(
            f"SHA256 mismatch for {archive_path}: expected {expected_sha256}, got {actual_sha256}"
        )

    if args.clean_dest and args.dest.exists():
        shutil.rmtree(args.dest)

    extracted = extract_subset(
        archive_path=archive_path,
        dest=args.dest,
        strip_components=args.strip_components,
        include_prefixes=include_prefixes,
    )
    print(f"extracted files: {len(extracted)}")

    if args.lock_file:
        args.lock_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "url": args.url,
            "archive": str(archive_path),
            "sha256": actual_sha256,
            "strip_components": args.strip_components,
            "include": include_prefixes,
            "extracted_count": len(extracted),
            "extracted": extracted,
        }
        args.lock_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote lock file: {args.lock_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
