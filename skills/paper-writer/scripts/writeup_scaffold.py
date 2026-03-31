#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from llm_adapter import chat

PROFILE_SPECS = {
    "conference": {
        "template": "conference_template.tex",
        "target": "an 8-page standard conference paper",
        "sections": (
            "abstract",
            "introduction",
            "related",
            "methods",
            "experiments",
            "results",
            "discussion",
        ),
        "placeholders": {
            "{ABSTRACT}": "abstract",
            "{INTRO}": "introduction",
            "{RELATED}": "related",
            "{METHODS}": "methods",
            "{EXPERIMENTS}": "experiments",
            "{RESULTS}": "results",
            "{DISCUSSION}": "discussion",
        },
    },
    "icbinb": {
        "template": "icbinb_template.tex",
        "target": "a concise 4-page ICBINB paper",
        "sections": (
            "abstract",
            "introduction",
            "methods",
            "results",
            "discussion",
        ),
        "placeholders": {
            "{ABSTRACT}": "abstract",
            "{INTRO}": "introduction",
            "{METHODS}": "methods",
            "{RESULTS}": "results",
            "{DISCUSSION}": "discussion",
        },
    },
}

PROFILE_ALIASES = {
    "conference": "conference",
    "standard": "conference",
    "normal": "conference",
    "icbinb": "icbinb",
}


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"[ERROR] File not found: {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"[ERROR] Invalid JSON: {path}: {e}")


def _first_idea(obj):
    if isinstance(obj, dict) and "ideas" in obj and isinstance(obj["ideas"], list):
        return obj["ideas"][0] if obj["ideas"] else None
    if isinstance(obj, dict) and "idea" in obj and isinstance(obj["idea"], dict):
        return obj["idea"]
    if isinstance(obj, list):
        return obj[0] if obj else None
    if isinstance(obj, dict):
        return obj
    return None


def _load_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _stringify_item(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "; ".join(f"{k}: {v}" for k, v in value.items())
    return str(value)


def _format_listish(value) -> str:
    if isinstance(value, list):
        return "\n".join(f"- {_stringify_item(item)}" for item in value if item is not None)
    if isinstance(value, (str, int, float)):
        return str(value)
    if isinstance(value, dict):
        return "\n".join(f"- {k}: {v}" for k, v in value.items())
    return ""


def _render_figures(manifest: dict) -> str:
    figures = manifest.get("figures", []) if isinstance(manifest, dict) else []
    blocks = []
    for fig in figures:
        filename = fig.get("filename")
        caption = fig.get("caption", "")
        if not filename:
            continue
        blocks.append(
            "\\begin{figure}[t]\n"
            "\\centering\n"
            f"\\includegraphics[width=0.9\\linewidth]{{figures/{filename}}}\n"
            f"\\caption{{{caption}}}\n"
            "\\end{figure}\n"
        )
    return "\n".join(blocks) if blocks else ""


def _safe_section(text: str, fallback: str) -> str:
    return text.strip() if text and text.strip() else fallback


def _normalize_profile(raw: str) -> str:
    profile = raw.strip().lower().replace("_", "-")
    normalized = PROFILE_ALIASES.get(profile)
    if normalized:
        return normalized
    supported = ", ".join(sorted(PROFILE_SPECS))
    raise SystemExit(
        f"[ERROR] Unknown profile: {raw}. Use one of: {supported} "
        "(aliases: standard, normal)."
    )


def _default_sections(profile: str, idea, summary, summary_md: str) -> dict[str, str]:
    intro = ""
    results = ""
    discussion = ""
    if isinstance(summary, dict):
        intro = summary.get("Description", "") or ""
        results = summary.get("Experiment_description", "") or ""
        discussion = summary.get("Significance", "") or ""

    if not intro and summary_md:
        intro = summary_md

    abstract = ""
    related = ""
    experiments = ""
    limitations = ""
    if isinstance(idea, dict):
        abstract = idea.get("Abstract", "") or ""
        related = idea.get("Related Work", "") or ""
        experiments = _format_listish(idea.get("Experiments"))
        limitations = _format_listish(idea.get("Risk Factors and Limitations"))

    sections = {
        "abstract": abstract,
        "introduction": intro,
        "related": related,
        "methods": "",
        "experiments": experiments,
        "results": results,
        "discussion": discussion or limitations,
    }

    if profile == "icbinb":
        sections.pop("related", None)
        sections.pop("experiments", None)

    return sections


def _draft_with_llm(profile: str, idea, summary, summary_md: str, manifest, model: str) -> dict:
    os.environ["ASV2_ONLINE"] = "1"
    spec = PROFILE_SPECS[profile]
    section_keys = ", ".join(spec["sections"])
    prompt = (
        f"Use the provided idea, summary, markdown notes, and plot manifest to draft "
        f"grounded sections for {spec['target']}. Return strict JSON with keys: "
        f"{section_keys}. Only use information present in the inputs. If evidence is "
        "missing for a section, return an empty string for that section.\n\n"
        f"IDEA: {json.dumps(idea, ensure_ascii=False)}\n\n"
        f"SUMMARY_JSON: {json.dumps(summary, ensure_ascii=False)}\n\n"
        f"SUMMARY_MD: {summary_md}\n\n"
        f"PLOTS: {json.dumps(manifest, ensure_ascii=False)}"
    )
    system = (
        "You are a concise scientific writer. Keep claims conservative, surface "
        "limitations honestly, and do not invent citations, baselines, or results."
    )
    response = chat(prompt=prompt, system=system, model=model)
    try:
        data = json.loads(response)
    except json.JSONDecodeError as e:
        raise SystemExit(f"[ERROR] LLM response was not valid JSON: {e}")
    if not isinstance(data, dict):
        raise SystemExit("[ERROR] LLM response must be a JSON object.")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate a scientific-paper LaTeX scaffold from idea/summary artifacts."
    )
    ap.add_argument(
        "--profile",
        default="conference",
        help="Scaffold profile: conference (aliases: standard, normal) or icbinb.",
    )
    ap.add_argument("--idea-json", help="Path to idea JSON.")
    ap.add_argument("--summary-json", help="Path to summary JSON.")
    ap.add_argument("--summary-md", help="Path to summary markdown.")
    ap.add_argument("--plots-manifest", help="Path to plot manifest JSON.")
    ap.add_argument("--out-dir", required=True, help="Output directory.")
    ap.add_argument("--title", help="Override title.")
    ap.add_argument("--authors", default="Anonymous", help="Author list.")
    ap.add_argument("--online", action="store_true", help="Enable LLM generation.")
    ap.add_argument("--model", default="gpt-4o-mini", help="Model name.")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing output.")
    args = ap.parse_args()

    profile = _normalize_profile(args.profile)
    spec = PROFILE_SPECS[profile]

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_tex = out_dir / "paper.tex"
    if out_tex.exists() and not args.overwrite:
        print(f"[ERROR] Output exists: {out_tex} (use --overwrite)")
        return 2

    idea = None
    if args.idea_json:
        idea = _first_idea(_load_json(Path(args.idea_json)))

    summary = None
    if args.summary_json:
        summary = _load_json(Path(args.summary_json))

    summary_md = ""
    if args.summary_md:
        summary_md = Path(args.summary_md).read_text(encoding="utf-8")

    manifest = None
    if args.plots_manifest:
        manifest = _load_json(Path(args.plots_manifest))

    title = args.title or (idea.get("Title") if isinstance(idea, dict) else None) or "Untitled"
    sections = _default_sections(profile, idea, summary, summary_md)

    if args.online:
        drafted = _draft_with_llm(profile, idea, summary, summary_md, manifest, args.model)
        for key in spec["sections"]:
            if key in drafted and isinstance(drafted[key], str):
                sections[key] = drafted[key]

    template_path = Path(__file__).parent.parent / "references" / spec["template"]
    template = _load_template(template_path)
    figures_block = _render_figures(manifest) if manifest else ""

    filled = template
    filled = filled.replace("{{{TITLE}}}", "{" + title + "}")
    filled = filled.replace("{{{AUTHORS}}}", "{" + args.authors + "}")
    for placeholder, section_name in spec["placeholders"].items():
        filled = filled.replace(placeholder, _safe_section(sections.get(section_name, ""), "TBD."))
    filled = filled.replace("{FIGURES}", figures_block)

    out_tex.write_text(filled, encoding="utf-8")
    print(f"[OK] Wrote {out_tex} using profile={profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
