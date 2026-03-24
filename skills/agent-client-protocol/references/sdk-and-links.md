# ACP SDK and Official Links

Use this file when the task needs concrete implementation entrypoints instead of protocol-only guidance.

## Current Compatibility Snapshot

Use this snapshot for routing and trigger interpretation, not as a substitute for re-checking live docs when the user asks for the latest status.

- Codex CLI:
  - ACP agents page lists `Codex CLI` as usable with an ACP client via Zed's adapter.
  - official adapter repo: `https://github.com/zed-industries/codex-acp`
- Claude Agent / Claude Code:
  - ACP agents page lists `Claude Agent` via Zed's SDK adapter.
  - official adapter repo now resolves to `https://github.com/zed-industries/claude-agent-acp`
  - older notes may still say `claude-code-acp`, but the live official adapter repo/package is `claude-agent-acp`
  - OpenClaw docs still use the older product wording `Claude Code` in examples
- OpenClaw:
  - ACP clients/connectors page lists OpenClaw through the `openclaw acp` bridge.
  - official docs: `https://docs.openclaw.ai/cli/acp`
- ZeroClaw:
  - no ACP support page was found in ACP official docs
  - no ACP support page was found in ZeroClaw official docs/repo searches used for this skill
  - treat ACP support as unverified

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
