# Changelog
All notable changes to this skill will be documented in this file.

The format is based on Keep a Changelog,
and this project adheres to Semantic Versioning.

## [Unreleased]

### Added
- Added task-first skill-organization guidance covering decision ladders, cross-cutting standards layers, and when tool-first splits are justified.
- Added `references/task-first-skill-design.md` as a repo-specific authoring reference.

### Changed
- Updated the main workflow, template, and checklist to prefer task / family / semantics first and treat tools as second-layer implementation options by default.


## [2026-03-11]
### Added
- Added guidance that `description` is routing metadata and should state trigger timing, task phase, and expected outputs.
- Added sections on `AGENTS.md` coordination, model-vs-script boundaries, and handling fresh external knowledge via official lookup workflows.
- Added a routing-focused example showing how to design end-of-task skills and when to add repo-level mandatory trigger rules.

### Changed
- Updated the workflow to define a routing contract before authoring resources and to validate local stability before CI automation.
- Refined frontmatter and checklist guidance to emphasize narrow skill contracts, deterministic scripts, and matching `AGENTS.md` triggers.

## [2026-01-26]
### Added
- Documented all spec frontmatter fields in the skill body.
- Added optional frontmatter fields (`license`, `compatibility`, `metadata`, `allowed-tools`) to make the skill self-describing.
- Added trigger keywords, compatibility gating guidance, and a concrete example.

### Changed
- Clarified validation expectations to include `agentskills validate`.
