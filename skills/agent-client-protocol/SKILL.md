---
name: agent-client-protocol
description: Implement or debug Agent Client Protocol (ACP) integrations between coding
  agents and clients/editors. Use when prompts mention ACP, Agent Client Protocol, or ask
  whether tools like Codex CLI (via `zed-industries/codex-acp`), Claude Agent / Claude Code
  (via `zed-industries/claude-agent-acp`, with older docs sometimes still saying `claude-code-acp`),
  OpenClaw (via `openclaw acp`), Zed, Visual Studio
  Code with the ACP Client extension, JetBrains, neovim, Emacs, marimo notebook, or Obsidian
  support ACP; also use for ACP compatibility checks such as whether ZeroClaw has ACP support.
  Trigger on JSON-RPC ACP methods like initialize, session/new, session/load, session/prompt,
  session/update, session/request_permission, terminal/create, fs/read_text_file, slash commands,
  or the official ACP TypeScript/Python SDKs.
---

# Agent Client Protocol

Use this skill when building or troubleshooting ACP-compatible agents, clients, or bridges.
Prefer official ACP docs and SDKs. Do not invent method names, capability flags, or payload fields.

## Compatibility Snapshot

As of March 16, 2026, the ACP docs and linked project docs support these practical routing assumptions:

- Codex CLI is available to ACP clients through the `zed-industries/codex-acp` adapter.
- Claude Agent / Claude Code is available to ACP clients through the `zed-industries/claude-agent-acp` adapter.
- OpenClaw is listed by ACP as both an ACP-capable agent entry and a connector via `openclaw acp`.
- ZeroClaw does not have ACP support that this skill can currently verify from ACP official docs or ZeroClaw official docs; treat ACP support as unverified until a primary source appears.

## Workflow

1. Decide which side you are implementing.
   - Agent: accepts `initialize`, `session/new`, `session/prompt`, and optional `session/load`; emits `session/update`.
   - Client: starts the connection, advertises capabilities, owns filesystem/terminal access, and answers `session/request_permission`.
   - Bridge: must satisfy ACP lifecycle rules on one side and host-runtime constraints on the other.
2. Read `references/protocol-workflow.md`.
3. If the task is language-specific, read `references/sdk-and-links.md`.
4. Implement the smallest ACP surface that satisfies the request.
5. Verify lifecycle invariants before returning code or advice.

## Lifecycle Invariants

- Use JSON-RPC 2.0 request/response semantics for methods and one-way semantics for notifications.
- Call `initialize` before `session/new` or `session/load`.
- Create or load a session before `session/prompt`.
- Check capabilities before optional methods:
  - `clientCapabilities.fs.readTextFile` and `clientCapabilities.fs.writeTextFile`
  - `clientCapabilities.terminal`
  - `agentCapabilities.loadSession`
  - `agentCapabilities.mcpCapabilities.http` and `agentCapabilities.mcpCapabilities.sse`
- Keep file paths absolute and line numbers 1-based.
- Finish each prompt turn by replying to the original `session/prompt` with a `stopReason`.

## Implementation Guidance

### Agent-side

- Negotiate `protocolVersion`, `agentCapabilities`, and optional `authMethods` during `initialize`.
- Support the baseline session surface: `session/new`, `session/prompt`, `session/cancel`, and `session/update`.
- If supporting resume, advertise `loadSession` and implement `session/load`.
- During a prompt turn, stream plans, message chunks, and tool progress through `session/update`.
- Catch cancellation-related runtime errors and return `stopReason: cancelled` instead of leaking a generic tool or transport exception.

### Client-side

- Advertise only capabilities that are actually implemented.
- Own `fs/read_text_file`, `fs/write_text_file`, `terminal/*`, and `session/request_permission`.
- Treat omitted capabilities as unsupported.
- Accept post-cancel `session/update` notifications until the Agent answers the original `session/prompt`.
- Treat slash commands as ordinary prompt text; command discovery is advertised separately via `available_commands_update`.
- For benchmark clients, use one fresh ACP session per benchmark item and keep run-local memory, workspace, and log state isolated instead of resuming prior sessions.

### ACP + MCP

- Pass MCP server connection details in `session/new` or `session/load`.
- Expect all ACP agents to support MCP stdio.
- Prefer MCP HTTP transport when available.
- Avoid new SSE-only designs; ACP docs note MCP has deprecated SSE.

## Output Rules

- Prefer exact ACP method names from the spec.
- If the user asks for a plan, organize it as: initialization -> session setup -> prompt turn -> optional features -> tests.
- If the user asks for bug triage, identify the first violated protocol invariant before discussing symptoms.
- If a field shape is uncertain, route to the ACP schema or SDK reference instead of guessing.

## References

- `references/protocol-workflow.md`: lifecycle, invariants, optional features, and failure checks.
- `references/sdk-and-links.md`: official SDK packages, examples, and doc entrypoints.

## Example Triggers

- Give my editor an ACP agent integration.
- Explain why `session/request_permission` blocks the rest of the turn.
- Build an ACP client in Python.
- Wrap an existing CLI with ACP.
- Add slash commands, filesystem access, or terminal support to my ACP agent.
