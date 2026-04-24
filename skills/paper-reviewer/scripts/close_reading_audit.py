#!/usr/bin/env python3
"""
Create and validate a close-reading audit ledger for paper reviews.

The ledger makes coverage explicit: each source unit must be marked reviewed
before the final review is written.
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


TODO_STATUS = "todo"
VALID_REVIEW_STATUSES = {"ok", "issue", "question", "na"}
KNOWN_HEADINGS = {
    "abstract",
    "introduction",
    "background",
    "related work",
    "method",
    "methods",
    "methodology",
    "approach",
    "experiments",
    "experiment",
    "results",
    "evaluation",
    "analysis",
    "discussion",
    "limitations",
    "conclusion",
    "conclusions",
    "references",
    "appendix",
    "supplement",
    "supplementary material",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def maybe_heading(text: str) -> str | None:
    line = normalize_text(text.splitlines()[0] if text.splitlines() else text)
    if not line or len(line) > 140:
        return None

    stripped = re.sub(r"^\d+(\.\d+)*\.?\s*", "", line).strip()
    stripped = re.sub(r"^[A-Z]\.\s*", "", stripped).strip()
    lowered = stripped.lower().rstrip(":")

    if lowered in KNOWN_HEADINGS:
        return stripped

    if re.match(r"^\d+(\.\d+)*\.?\s+[A-Z][A-Za-z0-9 ,:/()&-]{2,90}$", line):
        return line

    words = stripped.split()
    if 1 <= len(words) <= 10 and stripped.isupper() and any(ch.isalpha() for ch in stripped):
        return stripped.title()

    return None


def new_unit(
    *,
    source: str,
    page: int | None,
    section: str,
    unit_index: int,
    kind: str,
    text: str,
    line_start: int | None = None,
    line_end: int | None = None,
    block: int | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> dict[str, Any]:
    locator_parts = []
    if page is not None:
        locator_parts.append(f"p.{page}")
    if line_start is not None and line_end is not None:
        line_locator = f"lines {line_start}-{line_end}" if line_start != line_end else f"line {line_start}"
        locator_parts.append(line_locator)
    if block is not None:
        locator_parts.append(f"block {block}")

    return {
        "id": f"u{unit_index:04d}",
        "source": source,
        "page": page,
        "section": section,
        "kind": kind,
        "locator": ", ".join(locator_parts) if locator_parts else f"unit {unit_index}",
        "line_start": line_start,
        "line_end": line_end,
        "block": block,
        "bbox": [round(v, 2) for v in bbox] if bbox else None,
        "text": normalize_text(text),
        "review_status": TODO_STATUS,
        "review_note": "",
        "finding_ids": [],
    }


def text_units(path: Path, min_chars: int) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    units: list[dict[str, Any]] = []
    current: list[str] = []
    start_line: int | None = None
    section = "Front matter"

    def flush(end_line: int) -> None:
        nonlocal current, start_line, section
        if not current or start_line is None:
            return
        text = "\n".join(current)
        heading = maybe_heading(text)
        kind = "heading" if heading else "paragraph"
        if len(normalize_text(text)) >= min_chars or heading:
            if heading:
                section = heading
            units.append(
                new_unit(
                    source=str(path),
                    page=None,
                    section=section,
                    unit_index=len(units) + 1,
                    kind=kind,
                    text=text,
                    line_start=start_line,
                    line_end=end_line,
                )
            )
        current = []
        start_line = None

    for line_number, line in enumerate(lines, start=1):
        if line.strip():
            if start_line is None:
                start_line = line_number
            current.append(line)
        else:
            flush(line_number - 1)
    flush(len(lines))
    return units


def pdf_units(path: Path, min_chars: int, max_pages: int | None) -> list[dict[str, Any]]:
    try:
        import fitz  # type: ignore[import-not-found]
    except Exception as exc:
        message = (
            "PyMuPDF is required for PDF input. Try: "
            "uv run --with PyMuPDF scripts/close_reading_audit.py prepare --pdf paper.pdf"
        )
        raise RuntimeError(message) from exc

    document = fitz.open(str(path))
    page_limit = min(document.page_count, max_pages) if max_pages is not None else document.page_count
    units: list[dict[str, Any]] = []
    section = "Front matter"

    for page_index in range(page_limit):
        page = document.load_page(page_index)
        blocks = page.get_text("blocks")
        text_blocks = sorted(
            [block for block in blocks if len(block) >= 5 and normalize_text(str(block[4]))],
            key=lambda block: (round(float(block[1]), 1), round(float(block[0]), 1)),
        )
        for block_index, block in enumerate(text_blocks, start=1):
            x0, y0, x1, y1, text = block[:5]
            clean = normalize_text(str(text))
            heading = maybe_heading(clean)
            kind = "heading" if heading else "block"
            if len(clean) < min_chars and not heading:
                continue
            if heading:
                section = heading
            units.append(
                new_unit(
                    source=str(path),
                    page=page_index + 1,
                    section=section,
                    unit_index=len(units) + 1,
                    kind=kind,
                    text=clean,
                    block=block_index,
                    bbox=(float(x0), float(y0), float(x1), float(y1)),
                )
            )
    return units


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_coverage(path: Path, rows: list[dict[str, Any]]) -> None:
    sections: dict[str, dict[str, Any]] = {}
    for row in rows:
        section = str(row["section"])
        entry = sections.setdefault(
            section,
            {"section": section, "unit_count": 0, "pages": [], "unit_ids": []},
        )
        entry["unit_count"] += 1
        entry["unit_ids"].append(row["id"])
        if row["page"] is not None and row["page"] not in entry["pages"]:
            entry["pages"].append(row["page"])

    coverage = {
        "unit_count": len(rows),
        "sections": list(sections.values()),
        "status": "prepared",
        "instructions": (
            "Fill review_status with ok, issue, question, or na and add a short "
            "review_note for every unit before scoring."
        ),
    }
    path.write_text(json.dumps(coverage, indent=2, ensure_ascii=False), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
    return rows


def validate_rows(rows: list[dict[str, Any]]) -> tuple[list[str], Counter[str]]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    status_counts: Counter[str] = Counter()

    for index, row in enumerate(rows, start=1):
        unit_id = str(row.get("id") or f"row {index}")
        if unit_id in seen_ids:
            errors.append(f"{unit_id}: duplicate id")
        seen_ids.add(unit_id)

        status = str(row.get("review_status", "")).strip().lower()
        status_counts[status or "<missing>"] += 1
        if status == TODO_STATUS:
            errors.append(f"{unit_id}: still todo")
        elif status not in VALID_REVIEW_STATUSES:
            errors.append(f"{unit_id}: invalid review_status {status!r}")

        note = str(row.get("review_note", "")).strip()
        if len(note) < 3:
            errors.append(f"{unit_id}: missing review_note")

        if status in {"issue", "question"} and len(note) < 12:
            errors.append(f"{unit_id}: issue/question note is too short to be auditable")

    return errors, status_counts


def command_prepare(args: argparse.Namespace) -> int:
    sources = [bool(args.pdf), bool(args.text)]
    if sum(sources) != 1:
        print("[ERROR] Provide exactly one of --pdf or --text.")
        return 2

    if args.min_chars < 1:
        print("[ERROR] --min-chars must be positive.")
        return 2

    if args.pdf:
        source = Path(args.pdf).expanduser().resolve()
        if not source.exists():
            print(f"[ERROR] PDF not found: {source}")
            return 2
        try:
            rows = pdf_units(source, min_chars=args.min_chars, max_pages=args.max_pages)
        except RuntimeError as exc:
            print(f"[ERROR] {exc}")
            return 3
    else:
        source = Path(args.text).expanduser().resolve()
        if not source.exists():
            print(f"[ERROR] Text file not found: {source}")
            return 2
        rows = text_units(source, min_chars=args.min_chars)

    out_path = Path(args.out).expanduser().resolve()
    coverage_path = Path(args.coverage).expanduser().resolve()
    write_jsonl(out_path, rows)
    write_coverage(coverage_path, rows)
    print(f"[OK] Wrote {len(rows)} audit units: {out_path}")
    print(f"[OK] Wrote coverage map: {coverage_path}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    audit_path = Path(args.audit).expanduser().resolve()
    if not audit_path.exists():
        print(f"[ERROR] Audit file not found: {audit_path}")
        return 2

    try:
        rows = read_jsonl(audit_path)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 2

    errors, status_counts = validate_rows(rows)
    print(f"[INFO] Units: {len(rows)}")
    print("[INFO] Status counts: " + ", ".join(f"{k}={v}" for k, v in sorted(status_counts.items())))
    if errors:
        for error in errors[:50]:
            print(f"[ERROR] {error}")
        if len(errors) > 50:
            print(f"[ERROR] ... {len(errors) - 50} more")
        return 1

    print("[OK] Close-reading audit complete.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare or validate close-reading audit ledgers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Create a JSONL audit ledger from PDF or text.")
    prepare.add_argument("--pdf", help="Input PDF path.")
    prepare.add_argument("--text", help="Input text/Markdown/LaTeX path.")
    prepare.add_argument("--out", default="close_reading_audit.jsonl", help="Output audit JSONL.")
    prepare.add_argument("--coverage", default="coverage_map.json", help="Output coverage map JSON.")
    prepare.add_argument(
        "--min-chars",
        type=int,
        default=40,
        help="Ignore non-heading units shorter than this.",
    )
    prepare.add_argument("--max-pages", type=int, default=None, help="Optional PDF page limit.")
    prepare.set_defaults(func=command_prepare)

    validate = subparsers.add_parser("validate", help="Validate a completed audit ledger.")
    validate.add_argument("--audit", default="close_reading_audit.jsonl", help="Completed audit JSONL.")
    validate.set_defaults(func=command_validate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
