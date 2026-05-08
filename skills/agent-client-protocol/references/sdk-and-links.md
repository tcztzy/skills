# ACP SDK and Official Links

Use this file when the task needs concrete implementation entrypoints instead of protocol-only guidance.

## Current Compatibility Snapshot (2026-05)

- Codex CLI: `@agentclientprotocol/codex-acp` via bun. Repo: `https://github.com/zed-industries/codex-acp`
- Claude Agent / Claude Code: `@agentclientprotocol/claude-agent-acp` via bun. Repo: `https://github.com/zed-industries/claude-agent-acp`
- OpenClaw: `openclaw acp` bridge. Docs: `https://docs.openclaw.ai/cli/acp`
- OpenCode: `opencode acp` subcommand
- Hermes: `hermes acp` subcommand
- Gemini CLI: first ACP reference, built into Zed
- GitHub Copilot CLI, Cline, Goose, Qwen Code, Kimi CLI, Mistral Vibe: all ACP-compatible
- ZeroClaw: no verified ACP support

## Rust SDK (SACP)

Official page:

- `https://agentclientprotocol.com/libraries/rust`

Package and repository:

- crate: `agent-client-protocol` (SACP types)
- crate: `agent-client-protocol-tokio` (async runtime integration)
- install: `cargo add agent-client-protocol agent-client-protocol-tokio`
- repository: `https://github.com/agentclientprotocol/rust-sdk`

SACP = Statically-typed ACP. Generated Rust types from the ACP JSON schema. Provides:

- Typed request/response structs for all ACP methods
- JSON-RPC 2.0 message types
- Async connection primitives (tokio-based)
- Serde serialization for all protocol types

Use this SDK when:

- the project is Rust (including SwarmX)
- you want compile-time guarantees on ACP message shapes
- you are building an agent or client in Rust
- you are wrapping an existing Rust CLI with ACP

## ACP Registry

- `https://agentclientprotocol.com/registry`
- `https://github.com/agentclientprotocol/registry`
- Registry format: agents describe themselves via `agent.json`
- CI auto-validates format, icons, download URLs, and auth support
- Clients pull `registry.json` for discovery

## Official Documentation

- Protocol home: `https://agentclientprotocol.com/get-started/introduction`
- Protocol overview: `https://agentclientprotocol.com/protocol/overview`
- Initialization: `https://agentclientprotocol.com/protocol/initialization`
- Session setup: `https://agentclientprotocol.com/protocol/session-setup`
- Prompt turn: `https://agentclientprotocol.com/protocol/prompt-turn`
- Tool calls: `https://agentclientprotocol.com/protocol/tool-calls`
- File system: `https://agentclientprotocol.com/protocol/file-system`
- Terminals: `https://agentclientprotocol.com/protocol/terminals`
- Slash commands: `https://agentclientprotocol.com/protocol/slash-commands`
- Schema: `https://agentclientprotocol.com/protocol/schema`
- Session resume: `https://agentclientprotocol.com/protocol/session-resume`
- Session close: `https://agentclientprotocol.com/protocol/session-close`
- Session list: `https://agentclientprotocol.com/protocol/session-list`
- ACP Registry: `https://agentclientprotocol.com/registry`
- Transport negotiation: `https://agentclientprotocol.com/protocol/transports`
- Main spec repository: `https://github.com/agentclientprotocol/agent-client-protocol`

## TypeScript SDK

Official page:

- `https://agentclientprotocol.com/libraries/typescript`

Package:

- `@agentclientprotocol/sdk`
- install with `npm install @agentclientprotocol/sdk`

Starting points called out by ACP docs:

- `AgentSideConnection`
- `ClientSideConnection`

Official examples and references:

- examples: `https://github.com/agentclientprotocol/typescript-sdk/tree/main/src/examples`
- API reference: `https://agentclientprotocol.github.io/typescript-sdk`

Use this SDK when:

- the project is TypeScript or JavaScript
- you want generated connection primitives instead of hand-rolling JSON-RPC
- you need an agent or client example to copy from official sources

## Python SDK

Official page:

- `https://agentclientprotocol.com/libraries/python`

Package and repository:

- package: `agent-client-protocol`
- install with `pip install agent-client-protocol`
- `uv` install: `uv add agent-client-protocol`
- repository: `https://github.com/agentclientprotocol/python-sdk`

ACP docs describe the Python SDK as shipping:

- Pydantic models
- async base classes
- JSON-RPC plumbing
- helpers for both agents and clients

Official examples and references:

- examples: `https://github.com/agentclientprotocol/python-sdk/tree/main/examples`
- docs: `https://agentclientprotocol.github.io/python-sdk/`

Use this SDK when:

- the project is Python
- typed protocol models are preferable to handwritten payload dicts
- you want runnable demos for agents, clients, or bridges

## Selection Rules

- Prefer official SDK models and connection classes over handwritten ACP schemas.
- Prefer the ACP schema page only when the SDK docs do not expose the field shape clearly.
- If you are wrapping an existing CLI or editor integration, start from the SDK example closest to your side of the protocol.
- If a task mixes ACP and MCP, use ACP session setup docs for transport negotiation and keep MCP server details inside session creation/loading payloads.
- For benchmark harnesses, pin the adapter repo/package name explicitly, start a fresh session for every benchmark item, and treat session resume as out of scope unless the benchmark is explicitly measuring continuation behavior.
