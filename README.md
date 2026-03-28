# Skills Repository

This repository keeps installable Agent Skills under a single [`skills/`](./skills) entrypoint, following the layout commonly used by skills repositories such as [openai/skills](https://github.com/openai/skills) and [anthropics/skills](https://github.com/anthropics/skills).

It focuses on project-owned skills that are maintained directly in this repository. Official or third-party skills should stay in their own upstream repositories rather than being vendored here.

## Layout

- [`skills/`](./skills): all discoverable skills
- [`skills/<skill-name>/`](./skills): user-installable skills

## Language Policy

Use precise, professional English throughout this repository unless a skill explicitly concerns another language, such as translation, language-specific writing guidance, or language-specific source code.

## Showcase: End-to-End Research Workflow

This example shows how multiple research-oriented skills in this repository can be composed into one end-to-end workflow instead of being used as isolated point tools.

```mermaid
flowchart TD
    A["Research question / initial observation / spark"] --> B{"Is the direction already shaped?"}
    B -->|No| C["research-ideation-novelty-check<br/>Generate candidate ideas and run novelty sanity checks"]
    B -->|Yes| D["research-impact-strategy<br/>Decide GO / KILL / PIVOT / SCOPE-DOWN"]
    C --> D
    D -->|KILL| Z["Stop this direction / change topics / tighten the scope again"]
    D -->|GO / PIVOT / SCOPE-DOWN| E["zotero + citation-harvest<br/>Collect literature, maintain the reference library, export BibTeX"]
    E --> F["Collect data / run experiments / organize raw artifacts"]
    F --> G["data-to-viz<br/>Choose chart family and plotting route"]
    G --> H["paper-visualizer<br/>Generate or refine paper figures and plots"]
    H --> J["experiment-log-summarizer<br/>Condense the run directory into summary.md / summary.json"]
    J --> K{"Do the evidence and story now close the loop?"}
    K -->|No: positioning or claim is weak| D
    K -->|No: data or experiments are still insufficient| F
    K -->|Yes| L["scientific-paper-writeup<br/>Turn ideas, logs, plots, and citations into a paper draft"]
    L --> M["paper-reviewer<br/>Pre-review argument, structure, figures, and layout"]
    M --> N{"Is it ready to submit?"}
    N -->|Run more experiments| F
    N -->|Revise the story or tighten the claim| D
    N -->|Revise the draft, figures, or citations| L
    N -->|Yes| O["Submit / rebuttal / next revision round"]
```

Recommended minimum loop:

1. [`research-ideation-novelty-check`](./skills/research-ideation-novelty-check/SKILL.md)
2. [`research-impact-strategy`](./skills/research-impact-strategy/SKILL.md)
3. [`zotero`](./skills/zotero/SKILL.md) / [`citation-harvest`](./skills/citation-harvest/SKILL.md)
4. [`data-to-viz`](./skills/data-to-viz/SKILL.md)
5. [`paper-visualizer`](./skills/paper-visualizer/SKILL.md)
6. [`experiment-log-summarizer`](./skills/experiment-log-summarizer/SKILL.md)
7. [`scientific-paper-writeup`](./skills/scientific-paper-writeup/SKILL.md)
8. [`paper-reviewer`](./skills/paper-reviewer/SKILL.md)

The core point of this showcase is:

- Use `research-impact-strategy` first to decide whether the topic is worth pursuing, instead of drafting the paper immediately.
- Use `data-to-viz` before dropping into plotting backends so chart choice stays tied to the analytical question.
- Use `paper-visualizer` when the deliverable is a manuscript-ready figure or plot rather than a quick exploratory chart.
- Use `experiment-log-summarizer` before writing so the run directory becomes a stable input.
- Use `paper-reviewer` before submission to decide whether to add experiments, revise the story, or submit.

## Local Usage

Point your local skill roots at this directory:

- `~/.codex/skills -> /Users/tcztzy/skills/skills`
- `~/.claude/skills -> /Users/tcztzy/skills/skills`

That keeps runtime lookup paths stable for repository-local skills, for example:

- `$CODEX_HOME/skills/skill-manager/scripts/validate-skill.py`
- `$CODEX_HOME/skills/data-to-viz/scripts/gen_matplotlib_skeleton.py`

If you also need official OpenAI skills such as `playwright`, `pdf`, or `openai-docs`, install them from [openai/skills](https://github.com/openai/skills) or use the built-in system skills that ship with Codex.

## Codex App Quickstart (macOS / Windows)

If you want the easiest first-run path in the Codex app, install skills from this repository URL first instead of wiring local symlinks.

1. Download the Codex app
   - macOS (Apple Silicon): [Download Codex.dmg](https://persistent.oaistatic.com/codex-app-prod/Codex.dmg)
   - Windows: [Install from Microsoft Store](https://apps.microsoft.com/detail/9plm9xgg6vks?hl=en-US&gl=US) or run `winget install Codex -s msstore`
2. Open Codex and sign in with your ChatGPT account.
3. Open any local folder or git repository in the Codex app.
4. Paste one of the following prompts into Codex to install skills from this repository:

```text
Use $skill-installer to install skills from https://github.com/tcztzy/skills.
```

If you only want one skill, ask for it explicitly:

```text
Use $skill-installer to install the `skill-manager` skill from https://github.com/tcztzy/skills.
```

If a newly installed skill does not appear immediately, restart Codex.

Why this path:

- Codex repo-local auto-discovery expects skills under `.agents/skills`.
- This repository keeps installable skills under [`skills/`](./skills) as a shared skill source.
- For Codex app beginners, installing from the repository URL is the simplest setup.

## Claude -> Codex Projection

If you want Codex to mirror Claude's enabled skill plugins instead of exposing the whole repository, use [`scripts/sync_codex_skills_from_claude.py`](./scripts/sync_codex_skills_from_claude.py).

The script:

- reads `~/.claude/settings.json`
- resolves enabled plugin ids like `document-skills@anthropic-agent-skills`
- loads the corresponding marketplace metadata from `~/.claude/plugins/marketplaces/*/.claude-plugin/marketplace.json`
- ignores non-skill plugins
- creates symlinks for enabled skills under `~/.codex/skills`

Example:

```bash
python3 scripts/sync_codex_skills_from_claude.py --dry-run
python3 scripts/sync_codex_skills_from_claude.py --replace-symlink
```

`--replace-symlink` is needed if `~/.codex/skills` is currently a direct symlink to this repository, because the enabled-only projection needs a managed directory instead of a pass-through root symlink.

## Claude Marketplace

This repository also exposes a Claude plugin marketplace manifest at [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json).

- Each visible skill under [`skills/`](./skills) is exported as its own Claude plugin entry.
- Hidden and system-only directories are excluded from the marketplace manifest.
- The manifest is generated by [`scripts/generate_claude_marketplace.py`](./scripts/generate_claude_marketplace.py).

Regenerate it after adding, removing, or renaming skills:

```bash
python3 scripts/generate_claude_marketplace.py
```

After the repository is pushed, Claude Code can add it as a marketplace from GitHub and enable individual skill plugins through `enabledPlugins`.
