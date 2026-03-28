#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "huggingface-hub>=0.35.0",
# ]
# ///

import argparse
import json
import shutil
from pathlib import Path
from zipfile import ZipFile

REPO_ID = "dwzhu/PaperBananaBench"
ARCHIVE_NAME = "PaperBananaBench.zip"
_, ARCHIVE_ROOT = REPO_ID.split("/")
REQUIRED_FILES = ("diagram/ref.json", "plot/ref.json")


def resolve_skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_asset_dataset_dir() -> Path:
    return resolve_skill_root() / "assets" / "paperbanana" / ARCHIVE_ROOT


def resolve_asset_archive_path() -> Path:
    return resolve_skill_root() / "assets" / "paperbanana" / ARCHIVE_NAME


def is_dataset_directory(path: Path) -> bool:
    return path.is_dir() and all(
        (path / required_file).is_file() for required_file in REQUIRED_FILES
    )


def extract_archive(archive_path: Path, target_dir: Path) -> Path:
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if is_dataset_directory(target_dir):
        return target_dir.resolve()

    staging_root = target_dir.parent / f".{ARCHIVE_ROOT}.extracting"
    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_root.mkdir(parents=True, exist_ok=True)

    try:
        with ZipFile(archive_path) as archive:
            archive.extractall(staging_root)

        extracted_dir = staging_root / ARCHIVE_ROOT
        if not is_dataset_directory(extracted_dir):
            raise FileNotFoundError(
                f"Extracted PaperBananaBench directory is incomplete: {extracted_dir}"
            )

        if target_dir.exists():
            shutil.rmtree(target_dir)
        extracted_dir.replace(target_dir)
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root, ignore_errors=True)

    return target_dir.resolve()


def existing_or_extracted_dataset(
    target_dir: Path, local_archive_path: Path
) -> Path | None:
    if is_dataset_directory(target_dir):
        return target_dir.resolve()
    if local_archive_path.is_file():
        return extract_archive(local_archive_path.resolve(), target_dir)
    return None


def download_archive_to_target(dataset_dir: Path) -> Path:
    from huggingface_hub import hf_hub_download

    download_dir = dataset_dir.parent / ".downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    downloaded_archive = Path(
        hf_hub_download(
            repo_id=REPO_ID,
            repo_type="dataset",
            filename=ARCHIVE_NAME,
            local_dir=download_dir,
        )
    ).resolve()
    if not downloaded_archive.is_file():
        raise FileNotFoundError(
            f"Downloaded PaperBananaBench archive is missing: {downloaded_archive}"
        )
    return extract_archive(downloaded_archive, dataset_dir)


def resolve_dataset_dir(work_dir: Path, dataset_dir: Path | None = None) -> Path:
    work_dir = work_dir.resolve()
    asset_dataset_dir = resolve_asset_dataset_dir()
    asset_archive_path = resolve_asset_archive_path()
    default_dataset_dir = work_dir / "data" / ARCHIVE_ROOT

    if dataset_dir is not None:
        target_dir = dataset_dir.expanduser().resolve()
        if is_dataset_directory(target_dir):
            return target_dir
        return existing_or_extracted_dataset(
            target_dir, asset_archive_path
        ) or download_archive_to_target(target_dir)

    if is_dataset_directory(asset_dataset_dir):
        return asset_dataset_dir.resolve()
    if is_dataset_directory(default_dataset_dir):
        return default_dataset_dir.resolve()
    return existing_or_extracted_dataset(
        default_dataset_dir, asset_archive_path
    ) or download_archive_to_target(default_dataset_dir)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve PaperBananaBench to a local extracted directory."
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path.cwd(),
        help=(
            "Working directory where the default data/PaperBananaBench extraction "
            "target and downloaded archive cache are created after checking skill "
            "assets."
        ),
    )
    parser.add_argument(
        "--dataset-dir",
        "--target-dir",
        dest="dataset_dir",
        type=Path,
        default=None,
        help="Optional explicit extraction directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of a plain path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dataset_dir = resolve_dataset_dir(
        work_dir=args.work_dir,
        dataset_dir=args.dataset_dir,
    )
    if args.json:
        print(json.dumps({"dataset_dir": str(dataset_dir)}, ensure_ascii=False))
    else:
        print(dataset_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
