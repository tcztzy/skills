# Skill Quality Checklist

- [ ] `name` must be 1-64 characters, only contain unicode lowercase alphanumeric characters and hyphens, not start or end with `-`, not contain consecutive hyphens (`--`) and match the parent directory name.
- [ ] `description` must be 1-1024 characters, should describe both what the skill does and when to use it, should lead with a short trigger-friendly phrase plus clear keywords, and should not collapse the skill into a tool brand when the real task is broader.
- [ ] If the canonical `name` is long or awkward in prompts, add `metadata.short_name` (and optional comma-separated `metadata.aliases`) instead of renaming the directory-backed identifier casually.
- [ ] Includes a “When to Use” section with clear triggers
- [ ] Top-level organization follows the user task / decision axis, not tool brands by default
- [ ] If multiple tools serve the same task, they appear as second-layer implementation options or recipes, not separate sibling skills by default
- [ ] Cross-cutting constraints such as publication rules, compliance, export requirements, accessibility, or safety are written as their own layer instead of being buried in backend notes
- [ ] Includes an `Input -> Actions -> Output` minimal contract section
- [ ] Workflow steps are concrete and executable
- [ ] At least one example includes expected output and demonstrates the path from task -> semantic choice -> implementation
- [ ] References and assets are one level deep and properly linked
- [ ] SKILL.md is concise; long detail moved to references/
