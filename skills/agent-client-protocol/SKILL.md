---
name: agent-client-protocol
description: Implement or debug Agent Client Protocol (ACP) integrations between coding
  agents and clients/editors. Covers spec v0.11.4 (2026-04-23): full session lifecycle
  (new/load/resume/close/list), prompt turns, tool calls, permissions, file system,
  terminals, slash commands, MCP integration, ACP Registry, and transport negotiation
  (stdio/HTTP/WebSocket). Use when prompts mention ACP, Agent Client Protocol, agent-client-protocol
  crate, ACP agent/client/bridge implementation; when asking whether Codex CLI, Claude Agent,
  OpenClaw, ZeroClaw, or other agents support ACP; when working with ACP in Rust (SACP SDK),
  Python, TypeScript, or Kotlin. Trigger on JSON-RPC ACP methods: initialize, session/new,
  session/load, session/resume, session/prompt, session/update, session/close, session/list,
  session/request_permission, session_info_update, terminal/create, fs/read_text_file,
  available_commands_update, or the official ACP SDKs.
---

# Agent Client Protocol

Use this skill when building or troubleshooting ACP-compatible agents, clients, or bridges.
Prefer official ACP docs and SDKs. Do not invent method names, capability flags, or payload fields.

## Protocol Version

Current stable: **v0.11.4** (2026-04-23). The protocol is developed by Zed Industries with multi-vendor governance. JetBrains' Sergey Ignatov joined as Lead Maintainer (2026-02-18).

Key stable features as of 2026-04:
- `session/resume` and `session/close` stabilized (2026-04-22)
- `session/list` stabilized (2026-03-09)
- `session_info_update` notification stabilized (2026-03-09)
- Session Config Options stabilized (2026-02-04): model, mode, reasoning level
- ACP Registry stabilized (2026-03-09)
- Streamable HTTP & WebSocket Transport in Draft (2026-04-22)
- Transports Working Group formed (JetBrains + Block/Goose, 2026-04-23)

## Compatibility Snapshot (2026-05)

- Codex CLI: ACP via `@agentclientprotocol/codex-acp` (bun x). Adapter repo: `zed-industries/codex-acp`
- Claude Agent / Claude Code: ACP via `@agentclientprotocol/claude-agent-acp` (bun x). Adapter repo: `zed-industries/claude-agent-acp`
- OpenClaw: ACP via `openclaw acp` bridge. Docs: `docs.openclaw.ai/cli/acp`
- Gemini CLI: First ACP reference implementation (Zed)
- OpenCode: ACP via `opencode acp` subcommand
- Hermes: ACP via `hermes acp` subcommand
- GitHub Copilot CLI, Cline, Goose, Qwen Code, Kimi CLI, Mistral Vibe: all ACP-compatible
- ZeroClaw: no verified ACP support as of 2026-05
- Rust SDK: `agentclientprotocol/rust-sdk` (based on SACP)
- Python SDK: `agent-client-protocol` (pip package). Pydantic models, async base classes
- TypeScript SDK: `@agentclientprotocol/sdk`. AgentSideConnection, ClientSideConnection

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
- Call `initialize` before `session/new`, `session/load`, or `session/resume`.
- Create, load, or resume a session before `session/prompt`.
- Accept `session/list` (optional) to enumerate active sessions; advertise via `agentCapabilities.listSessions`.
- Accept `session/resume` when `agentCapabilities.resumeSession` is true; agent replays history via `session/update` then answers the original `session/resume`.
- Accept `session/close` to terminate a session; after close, the agent must reject further `session/prompt` for that session ID.
- Accept `session_info_update` notifications from client (e.g., title changes).
- Check capabilities before optional methods:
  - `clientCapabilities.fs.readTextFile` and `clientCapabilities.fs.writeTextFile`
  - `clientCapabilities.terminal`
  - `agentCapabilities.loadSession`
  - `agentCapabilities.resumeSession`
  - `agentCapabilities.listSessions`
  - `agentCapabilities.mcpCapabilities.http` and `agentCapabilities.mcpCapabilities.sse`
- Keep file paths absolute and line numbers 1-based.
- Finish each prompt turn by replying to the original `session/prompt` with a `stopReason`.

## Implementation Guidance

### Agent-side

- Negotiate `protocolVersion`, `agentCapabilities`, and optional `authMethods` during `initialize`.
- Support the baseline session surface: `session/new`, `session/prompt`, `session/cancel`, and `session/update`.
- If supporting resume, advertise `resumeSession` and implement `session/resume` (replay history via `session/update`, then answer the original request).
- If supporting listing, advertise `listSessions` and implement `session/list`.
- Accept `session/close` to clean up session resources.
- Accept `session_info_update` notifications for client-driven metadata changes.
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

- Pass MCP server connection details in `session/new`, `session/load`, or `session/resume`.
- Expect all ACP agents to support MCP stdio.
- Prefer MCP HTTP (SSE deprecated by MCP spec).
- Streamable HTTP & WebSocket transports for ACP itself are in Draft (2026-04).
- For HTTP/SSE MCP servers, check `agentCapabilities.mcpCapabilities.http` before use.

### ACP Registry

The ACP Registry (`registry.json`) is a community index of ACP-compatible agents and clients. Agents describe themselves via `agent.json` — CI validates format, icons, download URLs, and auth support automatically. Use the registry to discover available agents rather than maintaining a hardcoded list.

### Rust SDK (SACP)

```toml
[dependencies]
agent-client-protocol = "0.11"
agent-client-protocol-tokio = "0.11"
```

Uses SACP (Statically-typed ACP) — generated Rust types from the ACP JSON schema. Provides typed connection primitives, JSON-RPC plumbing, and async support via tokio. Official repo: `https://github.com/agentclientprotocol/rust-sdk`.

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
