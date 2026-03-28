#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "google-genai>=1.29.0",
#   "python-dotenv>=1.0.1",
# ]
# ///

import argparse
import base64
import json
import re
import subprocess
import sys
import textwrap
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from dotenv import load_dotenv
from google import genai
from google.genai import types


SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]
SUMMARIZE_RUN = SKILL_ROOT / "scripts" / "summarize_run.py"
VALIDATE_RUN = SKILL_ROOT / "scripts" / "validate_run.py"
SECTION_RE = re.compile(r"\\(section|subsection|subsubsection)\*?\{")
INCLUDE_CMD_RE = re.compile(r"\\(input|include)\{([^}]+)\}")
FIGURE_BEGIN_RE = re.compile(r"\\begin\{(figure\*?)\}")
INCLUDEGRAPHICS_RE = re.compile(
    r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{[^}]+\}",
    re.DOTALL,
)
LABEL_TEXT_RE = re.compile(r"\b(?:Figure|Fig\.?|图)\s*([0-9]+)\b", re.IGNORECASE)
REF_CMD_TEMPLATE = r"\\(?:ref|autoref|cref|Cref)\{%s\}"
MAX_METHOD_CHARS = 12000
MAX_FIGREF_CHARS = 3000


@dataclass
class FigureOccurrence:
    index: int
    file_path: str
    start: int
    end: int
    env_name: str
    caption: str
    label: str | None
    has_includegraphics: bool
    line: int


@dataclass
class ManuscriptContext:
    manuscript_path: str
    manuscript_kind: str
    figure_number: int
    figure_file: str | None
    caption: str
    label: str | None
    figref_context: str
    method_context: str
    source_excerpt: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def ensure_suffix(path: Path, suffix: str) -> Path:
    if path.suffix:
        return path
    return path.with_suffix(suffix)


def find_brace_span(text: str, open_index: int) -> tuple[str, int]:
    if open_index >= len(text) or text[open_index] != "{":
        raise ValueError("Expected opening brace.")
    depth = 0
    chars: list[str] = []
    index = open_index
    while index < len(text):
        char = text[index]
        if char == "{":
            depth += 1
            if depth > 1:
                chars.append(char)
        elif char == "}":
            depth -= 1
            if depth == 0:
                return "".join(chars), index + 1
            chars.append(char)
        else:
            chars.append(char)
        index += 1
    raise ValueError("Unclosed brace group.")


def strip_tex_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        chars: list[str] = []
        escaped = False
        for char in line:
            if char == "%" and not escaped:
                break
            chars.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        lines.append("".join(chars))
    return "\n".join(lines)


def tex_to_plain_text(text: str) -> str:
    cleaned = strip_tex_comments(text)
    cleaned = re.sub(r"\\caption(?:\[[^\]]*\])?\s*\{", " Caption: ", cleaned)
    cleaned = re.sub(
        r"\\(section|subsection|subsubsection)\*?\{", "\n\nSection: ", cleaned
    )
    cleaned = re.sub(r"\\(?:label|ref|autoref|cref|Cref)\{([^}]*)\}", r" \1 ", cleaned)
    cleaned = re.sub(r"\\(?:textbf|textit|emph|underline)\{([^}]*)\}", r" \1 ", cleaned)
    cleaned = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", cleaned)
    cleaned = cleaned.replace("{", " ").replace("}", " ")
    return collapse_whitespace(cleaned)


def markdown_to_plain_text(text: str) -> str:
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]*\)", r" \1 ", cleaned)
    cleaned = re.sub(r"`{1,3}", " ", cleaned)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    return collapse_whitespace(cleaned)


def typst_to_plain_text(text: str) -> str:
    cleaned = re.sub(r"#\w+\(", " ", text)
    cleaned = cleaned.replace("[", " ").replace("]", " ")
    return collapse_whitespace(cleaned)


def docx_to_plain_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml_data = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml_data)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        runs = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        line = "".join(runs).strip()
        if line:
            paragraphs.append(line)
    return "\n\n".join(paragraphs)


def read_plain_manuscript(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".md":
        return markdown_to_plain_text(read_text(path))
    if suffix in {".typ", ".typst"}:
        return typst_to_plain_text(read_text(path))
    if suffix == ".docx":
        return docx_to_plain_text(path)
    return read_text(path)


def extract_command_argument(text: str, command: str) -> str | None:
    pattern = re.compile(rf"\\{command}(?:\[[^\]]*\])?\s*\{{")
    match = pattern.search(text)
    if not match:
        return None
    try:
        content, _ = find_brace_span(text, match.end() - 1)
    except ValueError:
        return None
    return collapse_whitespace(tex_to_plain_text(content))


def line_number_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def resolve_tex_include(base_dir: Path, token: str) -> Path | None:
    raw = token.strip()
    if not raw:
        return None
    candidates = [base_dir / raw, ensure_suffix(base_dir / raw, ".tex")]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def find_matching_figure_end(text: str, start: int, env_name: str) -> int:
    end_token = rf"\end{{{env_name}}}"
    end_index = text.find(end_token, start)
    if end_index == -1:
        raise ValueError(f"Missing {end_token}.")
    return end_index + len(end_token)


def scan_tex_file(
    path: Path,
    expanded_parts: list[str],
    figures: list[FigureOccurrence],
    include_stack: set[Path],
) -> None:
    path = path.resolve()
    if path in include_stack:
        return
    include_stack.add(path)
    text = read_text(path)
    position = 0
    while position < len(text):
        include_match = INCLUDE_CMD_RE.search(text, position)
        figure_match = FIGURE_BEGIN_RE.search(text, position)
        token_match: re.Match[str] | None = None
        token_kind = ""
        if include_match and figure_match:
            if include_match.start() < figure_match.start():
                token_match = include_match
                token_kind = "include"
            else:
                token_match = figure_match
                token_kind = "figure"
        elif include_match:
            token_match = include_match
            token_kind = "include"
        elif figure_match:
            token_match = figure_match
            token_kind = "figure"

        if token_match is None:
            expanded_parts.append(text[position:])
            break

        expanded_parts.append(text[position : token_match.start()])

        if token_kind == "include":
            included_path = resolve_tex_include(path.parent, token_match.group(2))
            if included_path is None:
                expanded_parts.append(text[token_match.start() : token_match.end()])
            else:
                scan_tex_file(
                    included_path,
                    expanded_parts=expanded_parts,
                    figures=figures,
                    include_stack=include_stack,
                )
            position = token_match.end()
            continue

        env_name = token_match.group(1)
        env_end = find_matching_figure_end(text, token_match.start(), env_name)
        env_text = text[token_match.start() : env_end]
        figures.append(
            FigureOccurrence(
                index=len(figures) + 1,
                file_path=str(path),
                start=token_match.start(),
                end=env_end,
                env_name=env_name,
                caption=extract_command_argument(env_text, "caption") or "",
                label=extract_command_argument(env_text, "label"),
                has_includegraphics=INCLUDEGRAPHICS_RE.search(env_text) is not None,
                line=line_number_at(text, token_match.start()),
            )
        )
        expanded_parts.append(env_text)
        position = env_end

    include_stack.remove(path)


def collect_tex_bundle(path: Path) -> tuple[str, list[FigureOccurrence]]:
    expanded_parts: list[str] = []
    figures: list[FigureOccurrence] = []
    scan_tex_file(
        path=path,
        expanded_parts=expanded_parts,
        figures=figures,
        include_stack=set(),
    )
    return "".join(expanded_parts), figures


def find_sections(expanded_text: str) -> list[tuple[str, str]]:
    matches = list(SECTION_RE.finditer(expanded_text))
    sections: list[tuple[str, str]] = []
    if not matches:
        return sections
    for index, match in enumerate(matches):
        try:
            title, body_start = find_brace_span(expanded_text, match.end() - 1)
        except ValueError:
            continue
        next_start = (
            matches[index + 1].start() if index + 1 < len(matches) else len(expanded_text)
        )
        body = expanded_text[body_start:next_start]
        sections.append(
            (
                collapse_whitespace(tex_to_plain_text(title)),
                tex_to_plain_text(body),
            )
        )
    return sections


def sentence_snippets(text: str, pattern: re.Pattern[str], max_chars: int) -> str:
    snippets: list[str] = []
    for raw in re.split(r"(?<=[.!?。！？])\s+", text):
        sentence = collapse_whitespace(raw)
        if not sentence:
            continue
        if pattern.search(sentence):
            snippets.append(sentence)
        if sum(len(item) for item in snippets) >= max_chars:
            break
    return "\n".join(snippets)


def select_method_context(expanded_text: str, caption: str, figref_text: str) -> str:
    sections = find_sections(expanded_text)
    if not sections:
        return tex_to_plain_text(expanded_text)[:MAX_METHOD_CHARS]

    preferred_titles = {
        "method",
        "methods",
        "approach",
        "framework",
        "overview",
        "model",
        "pipeline",
        "architecture",
        "system",
        "implementation",
    }
    keywords = set(
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", f"{caption} {figref_text}")
    )

    scored: list[tuple[int, str, str]] = []
    for title, body in sections:
        title_words = set(re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", title.lower()))
        body_lower = body.lower()
        score = 0
        if title_words & preferred_titles:
            score += 8
        score += sum(1 for keyword in keywords if keyword in body_lower)
        if "figure 1" in body_lower or "fig. 1" in body_lower:
            score += 4
        scored.append((score, title, body))

    scored.sort(key=lambda item: item[0], reverse=True)
    picked: list[str] = []
    total_chars = 0
    for score, title, body in scored[:3]:
        if score <= 0 and picked:
            continue
        section_text = f"{title}\n{body}".strip()
        if not section_text:
            continue
        picked.append(section_text)
        total_chars += len(section_text)
        if total_chars >= MAX_METHOD_CHARS:
            break
    return "\n\n".join(picked)[:MAX_METHOD_CHARS]


def figure_number_from_text(text: str) -> int:
    stripped = text.strip()
    if stripped.isdigit():
        return int(stripped)
    match = LABEL_TEXT_RE.search(text)
    if not match:
        raise ValueError(f"Could not parse figure number from: {text}")
    return int(match.group(1))


def collect_generic_context(path: Path, figure_number: int) -> ManuscriptContext:
    raw_text = read_plain_manuscript(path)
    caption_pattern = re.compile(
        rf"(?:^|\n)(?:Figure|Fig\.?|图)\s*{figure_number}\s*[:：.]\s*(.+)",
        re.IGNORECASE,
    )
    caption_match = caption_pattern.search(raw_text)
    caption = (
        collapse_whitespace(caption_match.group(1))
        if caption_match
        else f"Figure {figure_number}"
    )

    figref_pattern = re.compile(
        rf"\b(?:Figure|Fig\.?|图)\s*{figure_number}\b",
        re.IGNORECASE,
    )
    figref_context = sentence_snippets(raw_text, figref_pattern, MAX_FIGREF_CHARS)

    method_blocks = re.split(r"\n\s*\n", raw_text)
    method_context = "\n\n".join(
        block
        for block in method_blocks
        if re.search(
            r"\b(method|approach|framework|pipeline|overview|model|system|implementation)\b",
            block,
            re.IGNORECASE,
        )
    )[:MAX_METHOD_CHARS]
    if not method_context:
        method_context = raw_text[:MAX_METHOD_CHARS]

    source_excerpt = "\n\n".join(
        chunk for chunk in [caption, figref_context, method_context] if chunk
    )[: MAX_METHOD_CHARS + MAX_FIGREF_CHARS]

    return ManuscriptContext(
        manuscript_path=str(path),
        manuscript_kind=path.suffix.lower().lstrip(".") or "text",
        figure_number=figure_number,
        figure_file=None,
        caption=caption,
        label=None,
        figref_context=figref_context,
        method_context=method_context,
        source_excerpt=source_excerpt,
    )


def collect_tex_context(path: Path, figure_number: int) -> tuple[ManuscriptContext, FigureOccurrence]:
    expanded_text, figures = collect_tex_bundle(path)
    if not figures:
        raise ValueError(f"No LaTeX figure environment found in: {path}")
    if figure_number < 1 or figure_number > len(figures):
        raise ValueError(
            f"Figure {figure_number} is out of range. Found {len(figures)} figure environments."
        )

    target = figures[figure_number - 1]
    caption = target.caption or f"Figure {figure_number}"
    search_space = tex_to_plain_text(expanded_text)
    figref_patterns: list[re.Pattern[str]] = []
    if target.label:
        figref_patterns.append(re.compile(REF_CMD_TEMPLATE % re.escape(target.label)))
    figref_patterns.append(
        re.compile(rf"\b(?:Figure|Fig\.?|图)\s*{figure_number}\b", re.IGNORECASE)
    )

    figref_snippets: list[str] = []
    for raw in re.split(r"(?<=[.!?。！？])\s+", search_space):
        sentence = collapse_whitespace(raw)
        if not sentence:
            continue
        if any(pattern.search(sentence) for pattern in figref_patterns):
            figref_snippets.append(sentence)
        if sum(len(item) for item in figref_snippets) >= MAX_FIGREF_CHARS:
            break
    figref_context = "\n".join(figref_snippets)

    method_context = select_method_context(expanded_text, caption, figref_context)
    source_excerpt = "\n\n".join(
        chunk for chunk in [caption, figref_context, method_context] if chunk
    )[: MAX_METHOD_CHARS + MAX_FIGREF_CHARS]

    context = ManuscriptContext(
        manuscript_path=str(path),
        manuscript_kind="tex",
        figure_number=figure_number,
        figure_file=target.file_path,
        caption=caption,
        label=target.label,
        figref_context=figref_context,
        method_context=method_context,
        source_excerpt=source_excerpt,
    )
    return context, target


def select_style_guides(context: ManuscriptContext, task: str) -> list[Path]:
    guide_dir = SKILL_ROOT / "assets" / "style_guides"
    combined_text = f"{context.caption}\n{context.figref_context}\n{context.method_context}".lower()
    bio_keywords = {
        "protein",
        "gene",
        "genome",
        "genomic",
        "rna",
        "dna",
        "cell",
        "cells",
        "sequencing",
        "peptide",
        "pathway",
        "biomedical",
        "bioinformatics",
        "molecule",
        "molecular",
        "antibody",
        "metagenomics",
        "alphafold",
    }
    chosen: list[Path] = []
    if any(keyword in combined_text for keyword in bio_keywords):
        visual_path = guide_dir / "bioinformatics_visual_style_guide.md"
        task_path = guide_dir / f"bioinformatics_{task}_style_guide.md"
        if visual_path.exists():
            chosen.append(visual_path)
        if task_path.exists():
            chosen.append(task_path)

    fallback = guide_dir / f"neurips2025_{task}_style_guide.md"
    if fallback.exists():
        chosen.append(fallback)

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in chosen:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(resolved)
    return deduped


def style_guide_preview(paths: list[Path], max_chars: int = 7000) -> str:
    chunks: list[str] = []
    total = 0
    for path in paths:
        text = read_text(path)
        block = f"[{path.name}]\n{text}".strip()
        if total + len(block) > max_chars:
            remaining = max_chars - total
            if remaining > 0:
                chunks.append(block[:remaining])
            break
        chunks.append(block)
        total += len(block)
    return "\n\n".join(chunks)


def build_local_draft_prompt(context: ManuscriptContext, aspect_ratio: str) -> str:
    figref_section = (
        context.figref_context
        or "No explicit figure references were found in the manuscript text."
    )
    return textwrap.dedent(
        f"""
        Create a publication-quality scientific diagram for Figure {context.figure_number}.

        Scope:
        - Preserve the paper semantics exactly.
        - Do not invent modules, entities, or evaluation results.
        - Do not render the full caption text inside the image.
        - Prefer a clear narrative layout unless the manuscript strongly implies another structure.
        - Default aspect ratio: {aspect_ratio}.

        Figure caption:
        {context.caption}

        In-text figure references:
        {figref_section}

        Method context:
        {context.method_context}

        The figure should make the method flow, components, inputs, outputs, and relationships clear enough that Figure {context.figure_number} can stand alone in the paper.
        """
    ).strip()


def build_refinement_prompt(
    context: ManuscriptContext,
    draft_prompt: str,
    style_guide_text: str,
) -> str:
    return textwrap.dedent(
        f"""
        You are preparing a final image-generation prompt for a scientific paper diagram.
        Return strict JSON with exactly these keys:
        - summary
        - content
        - visual_intent
        - diagram_prompt
        - aspect_ratio

        Requirements:
        - Keep the semantics faithful to the manuscript.
        - The `summary` should be 3-6 sentences.
        - The `content` should be a concise but detailed prose summary of the method details needed for the figure.
        - The `visual_intent` should be a compact description of what Figure {context.figure_number} must communicate.
        - The `diagram_prompt` should be directly usable as a Gemini image-generation prompt for a scientific diagram.
        - The `aspect_ratio` must be one of: 1:1, 4:3, 3:4, 16:9, 9:16.
        - Never ask the renderer to place the full caption text inside the image.

        Manuscript path: {context.manuscript_path}
        Figure number: {context.figure_number}
        Figure label: {context.label or "N/A"}

        Figure caption:
        {context.caption}

        In-text figure references:
        {context.figref_context or "None found."}

        Method context:
        {context.method_context}

        Style guide excerpt:
        {style_guide_text}

        Draft prompt:
        {draft_prompt}
        """
    ).strip()


def parse_json_object(text: str) -> dict[str, Any]:
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object.")
    return parsed


def gemini_client() -> genai.Client:
    load_dotenv()
    return genai.Client()


def refine_with_gemini(
    client: genai.Client,
    text_model: str,
    refinement_prompt: str,
) -> dict[str, Any]:
    response = client.models.generate_content(
        model=text_model,
        contents=refinement_prompt,
    )
    if not response.text:
        raise RuntimeError("Gemini text model returned no text.")
    return parse_json_object(response.text)


def to_image_bytes(part: Any) -> tuple[bytes, str]:
    inline = part.inline_data
    raw_data = inline.data
    if isinstance(raw_data, str):
        payload = base64.b64decode(raw_data)
    else:
        payload = bytes(raw_data)
    mime_type = inline.mime_type or "image/png"
    return payload, mime_type


def generate_diagram_image(
    client: genai.Client,
    image_model: str,
    prompt: str,
    aspect_ratio: str,
) -> tuple[bytes, str]:
    response = client.models.generate_content(
        model=image_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        ),
    )
    for part in response.parts or []:
        if getattr(part, "inline_data", None) is not None:
            return to_image_bytes(part)
    raise RuntimeError("Gemini image model returned no inline image.")


def image_extension(mime_type: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
    }
    return mapping.get(mime_type.lower(), ".png")


def path_for_tex_include(from_file: Path, to_file: Path) -> str:
    relative = os.path.relpath(to_file, start=from_file.parent)
    return Path(relative).as_posix()


def relative_posix_path(path: Path, base: Path) -> str:
    return path.resolve().relative_to(base.resolve()).as_posix()


def replace_or_insert_includegraphics(
    env_text: str,
    relative_image_path: str,
) -> tuple[str, str]:
    replacement = rf"\includegraphics[width=\linewidth]{{{relative_image_path}}}"
    if INCLUDEGRAPHICS_RE.search(env_text):
        updated = INCLUDEGRAPHICS_RE.sub(replacement, env_text, count=1)
        return updated, "replaced existing \\includegraphics"

    caption_match = re.search(r"\\caption(?:\[[^\]]*\])?\s*\{", env_text)
    if caption_match:
        updated = (
            env_text[: caption_match.start()]
            + replacement
            + "\n"
            + env_text[caption_match.start() :]
        )
        return updated, "inserted \\includegraphics before \\caption"

    begin_match = FIGURE_BEGIN_RE.search(env_text)
    if begin_match is None:
        raise ValueError("Could not locate figure environment header.")
    updated = (
        env_text[: begin_match.end()]
        + "\n\\centering\n"
        + replacement
        + "\n"
        + env_text[begin_match.end() :]
    )
    return updated, "inserted \\includegraphics after figure begin"


def update_tex_manuscript(target: FigureOccurrence, image_path: Path) -> str:
    figure_file = Path(target.file_path)
    original = read_text(figure_file)
    env_text = original[target.start : target.end]
    relative_image_path = path_for_tex_include(figure_file, image_path)
    updated_env, note = replace_or_insert_includegraphics(env_text, relative_image_path)
    updated_text = original[: target.start] + updated_env + original[target.end :]
    figure_file.write_text(updated_text, encoding="utf-8")
    return note


def update_markdown_manuscript(path: Path, figure_number: int, image_path: Path) -> str:
    text = read_text(path)
    relative = Path(os.path.relpath(image_path, start=path.parent)).as_posix()
    insertion = f"![Figure {figure_number}]({relative})"
    if insertion in text:
        return "markdown image reference already present"
    marker_re = re.compile(
        rf"(^|\n)(?:Figure|Fig\.?|图)\s*{figure_number}\s*[:：.].*",
        re.IGNORECASE,
    )
    match = marker_re.search(text)
    if match:
        updated = text[: match.end()] + "\n\n" + insertion + text[match.end() :]
        path.write_text(updated, encoding="utf-8")
        return "inserted markdown image after figure caption"
    path.write_text(text.rstrip() + "\n\n" + insertion + "\n", encoding="utf-8")
    return "appended markdown image at end of manuscript"


def update_typst_manuscript(path: Path, figure_number: int, image_path: Path) -> str:
    text = read_text(path)
    relative = Path(os.path.relpath(image_path, start=path.parent)).as_posix()
    figure_block = f'#figure(image("{relative}"), caption: [Figure {figure_number}])'
    if figure_block in text:
        return "typst figure block already present"
    marker_re = re.compile(
        rf"(^|\n)(?:=+\s*)?(?:Figure|Fig\.?|图)\s*{figure_number}\b.*",
        re.IGNORECASE,
    )
    match = marker_re.search(text)
    if match:
        updated = text[: match.end()] + "\n\n" + figure_block + text[match.end() :]
        path.write_text(updated, encoding="utf-8")
        return "inserted typst figure block near figure marker"
    path.write_text(text.rstrip() + "\n\n" + figure_block + "\n", encoding="utf-8")
    return "appended typst figure block at end of manuscript"


def insert_image_into_manuscript(
    manuscript_path: Path,
    figure_number: int,
    image_path: Path,
    tex_target: FigureOccurrence | None,
) -> str:
    suffix = manuscript_path.suffix.lower()
    if suffix == ".tex":
        if tex_target is None:
            raise ValueError("LaTeX insertion requires a concrete figure target.")
        return update_tex_manuscript(tex_target, image_path)
    if suffix == ".md":
        return update_markdown_manuscript(manuscript_path, figure_number, image_path)
    if suffix in {".typ", ".typst"}:
        return update_typst_manuscript(manuscript_path, figure_number, image_path)
    raise ValueError(f"Automatic manuscript insertion is not implemented for: {suffix or 'unknown'}")


def build_run_dir(manuscript_path: Path, run_id: str | None) -> Path:
    repo_root = manuscript_path.parent.resolve()
    final_run_id = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = repo_root / "runs" / "paper-visualizer" / final_run_id
    (run_dir / "shared").mkdir(parents=True, exist_ok=True)
    (run_dir / "candidates" / "candidate_00").mkdir(parents=True, exist_ok=True)
    return run_dir


def run_summary(
    run_dir: Path,
    repo_root: Path,
    mode: str,
    task: str,
    result_file: Path | None,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(SUMMARIZE_RUN),
        "--run-dir",
        str(run_dir),
        "--repo-root",
        str(repo_root),
        "--mode",
        mode,
        "--task",
        task,
    ]
    if result_file is not None:
        command.extend(["--result-file", str(result_file)])
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def validate_run(run_dir: Path, mode: str, result_file: Path) -> None:
    command = [
        sys.executable,
        str(VALIDATE_RUN),
        "--run-dir",
        str(run_dir),
        "--mode",
        mode,
        "--result-file",
        str(result_file),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


def collect_context(
    manuscript_path: Path,
    figure_number: int,
) -> tuple[ManuscriptContext, FigureOccurrence | None]:
    if manuscript_path.suffix.lower() == ".tex":
        context, target = collect_tex_context(manuscript_path, figure_number)
        return context, target
    return collect_generic_context(manuscript_path, figure_number), None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract manuscript context, generate a figure diagram with Gemini, and insert it back into the manuscript.",
    )
    parser.add_argument("manuscript", help="Path to the manuscript file, typically main.tex.")
    parser.add_argument(
        "--figure",
        required=True,
        help='Target figure number, e.g. "1" or "Figure 1".',
    )
    parser.add_argument(
        "--task",
        default="diagram",
        choices=["diagram"],
        help="Task type. Only diagram is currently implemented by this runner.",
    )
    parser.add_argument(
        "--text-model",
        default="gemini-2.5-flash",
        help="Gemini text model used for summary and prompt refinement.",
    )
    parser.add_argument(
        "--image-model",
        default="gemini-2.5-flash-image",
        help="Gemini image model used for diagram generation.",
    )
    parser.add_argument(
        "--style-guide",
        default="",
        help="Optional explicit style guide path. If omitted, the runner selects guides from manuscript context.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="16:9",
        choices=["1:1", "4:3", "3:4", "16:9", "9:16"],
        help="Fallback aspect ratio when the refinement stage does not override it.",
    )
    parser.add_argument("--run-id", default="", help="Optional explicit run id.")
    parser.add_argument(
        "--draft-only",
        action="store_true",
        help="Stop after extraction and prompt generation. Do not call Gemini image generation or edit the manuscript.",
    )
    parser.add_argument(
        "--no-insert",
        action="store_true",
        help="Generate the image but do not rewrite the manuscript.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manuscript_path = Path(args.manuscript).expanduser().resolve()
    if not manuscript_path.exists():
        print(f"[ERROR] Manuscript not found: {manuscript_path}")
        return 2

    try:
        figure_number = figure_number_from_text(args.figure)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 2

    run_dir = build_run_dir(manuscript_path, args.run_id or None)
    repo_root = manuscript_path.parent.resolve()
    context_path = run_dir / "shared" / "manuscript_context.json"
    draft_prompt_path = run_dir / "candidates" / "candidate_00" / "planner_draft.txt"
    planner_prompt_path = run_dir / "candidates" / "candidate_00" / "planner.txt"
    plan_path = run_dir / "shared" / "diagram_plan.json"
    result_file = run_dir / "result.json"

    try:
        context, tex_target = collect_context(manuscript_path, figure_number)
    except Exception as exc:
        print(f"[ERROR] Context extraction failed: {exc}")
        return 3

    style_guide_paths = (
        [Path(args.style_guide).expanduser().resolve()]
        if args.style_guide
        else select_style_guides(context, args.task)
    )

    write_json(context_path, asdict(context))

    draft_prompt = build_local_draft_prompt(context, args.aspect_ratio)
    draft_prompt_path.write_text(draft_prompt + "\n", encoding="utf-8")

    plan_payload: dict[str, Any] = {
        "summary": "",
        "content": context.method_context,
        "visual_intent": context.caption,
        "diagram_prompt": draft_prompt,
        "aspect_ratio": args.aspect_ratio,
        "style_guides": [str(path) for path in style_guide_paths],
        "used_gemini_refinement": False,
    }

    style_preview = style_guide_preview(style_guide_paths)
    refinement_prompt = build_refinement_prompt(context, draft_prompt, style_preview)

    if not args.draft_only:
        client = gemini_client()
        refined = refine_with_gemini(
            client=client,
            text_model=args.text_model,
            refinement_prompt=refinement_prompt,
        )
        plan_payload.update(
            {
                "summary": collapse_whitespace(str(refined.get("summary", ""))),
                "content": collapse_whitespace(
                    str(refined.get("content", context.method_context))
                ),
                "visual_intent": collapse_whitespace(
                    str(refined.get("visual_intent", context.caption))
                ),
                "diagram_prompt": str(refined.get("diagram_prompt", draft_prompt)).strip()
                or draft_prompt,
                "aspect_ratio": str(refined.get("aspect_ratio", args.aspect_ratio)).strip()
                or args.aspect_ratio,
                "used_gemini_refinement": True,
            }
        )

    planner_prompt_path.write_text(plan_payload["diagram_prompt"] + "\n", encoding="utf-8")
    write_json(plan_path, plan_payload)

    workflow_spec = {
        "mode": "planner",
        "task": "diagram",
        "source_manuscript": str(manuscript_path),
        "figure_number": figure_number,
        "text_model": args.text_model,
        "image_model": args.image_model,
        "draft_only": args.draft_only,
        "style_guides": [str(path) for path in style_guide_paths],
    }
    write_json(run_dir / "workflow_spec.json", workflow_spec)

    notes: list[str] = []
    if args.draft_only:
        notes.append("Draft-only run: skipped Gemini image generation and manuscript insertion.")
        dry_summary = {
            "mode": "planner",
            "task": "diagram",
            "status": "success",
            "run_dir": relative_posix_path(run_dir, repo_root),
            "artifacts": {
                "workflow_spec": relative_posix_path(run_dir / "workflow_spec.json", repo_root),
                "shared": [
                    relative_posix_path(context_path, repo_root),
                    relative_posix_path(plan_path, repo_root),
                ],
                "candidates": {
                    "candidate_00": [
                        relative_posix_path(draft_prompt_path, repo_root),
                        relative_posix_path(planner_prompt_path, repo_root),
                    ]
                },
            },
            "notes": notes,
        }
        print(json.dumps(dry_summary, ensure_ascii=False, indent=2))
        return 0

    try:
        client = gemini_client()
        image_bytes, mime_type = generate_diagram_image(
            client=client,
            image_model=args.image_model,
            prompt=plan_payload["diagram_prompt"],
            aspect_ratio=plan_payload["aspect_ratio"],
        )
    except Exception as exc:
        print(f"[ERROR] Gemini image generation failed: {exc}")
        return 4

    output_dir = repo_root / "figures" / "paper_visualizer"
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"figure_{figure_number:02d}{image_extension(mime_type)}"
    image_path.write_bytes(image_bytes)

    candidate_image_path = (
        run_dir / "candidates" / "candidate_00" / f"planner_image{image_path.suffix}"
    )
    candidate_image_path.write_bytes(image_bytes)

    if args.no_insert:
        notes.append("Skipped manuscript insertion because --no-insert was set.")
    else:
        try:
            note = insert_image_into_manuscript(
                manuscript_path=manuscript_path,
                figure_number=figure_number,
                image_path=image_path,
                tex_target=tex_target,
            )
            notes.append(note)
        except Exception as exc:
            notes.append(f"Image generated but manuscript insertion failed: {exc}")

    notes.append(f"Saved generated image to {image_path}")

    result_payload = {
        "status": "success",
        "artifacts": {
            "context": relative_posix_path(context_path, repo_root),
            "plan": relative_posix_path(plan_path, repo_root),
            "planner_prompt": relative_posix_path(planner_prompt_path, repo_root),
            "image": relative_posix_path(candidate_image_path, repo_root),
            "manuscript_image": relative_posix_path(image_path, repo_root),
        },
        "notes": notes,
    }
    write_json(result_file, result_payload)

    try:
        validate_run(run_dir=run_dir, mode="planner", result_file=result_file)
        summary = run_summary(
            run_dir=run_dir,
            repo_root=repo_root,
            mode="planner",
            task="diagram",
            result_file=result_file,
        )
    except Exception as exc:
        print(f"[ERROR] Run post-processing failed: {exc}")
        return 5

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
