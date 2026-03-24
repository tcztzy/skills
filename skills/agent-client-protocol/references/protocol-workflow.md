# ACP Protocol Workflow

Use this file when the task needs exact lifecycle ordering, capability checks, or optional ACP features.

## Core Model

- ACP standardizes communication between coding agents and clients/editors.
- ACP uses JSON-RPC 2.0.
- Methods are request/response pairs.
- Notifications are one-way messages with no response.
- ACP reuses MCP JSON structures where possible and uses Markdown for user-readable text.

## Required Order

1. `initialize`
2. `session/new` or `session/load`
3. `session/prompt`
4. optional `session/update`, `session/request_permission`, `fs/*`, `terminal/*`
5. `session/prompt` response with `stopReason`

Do not skip steps. Most ACP bugs are lifecycle bugs.

## Initialization

- The client starts with `initialize`.
- The request includes:
  - `protocolVersion`
  - `clientCapabilities`
  - usually `clientInfo`
- The agent responds with:
  - chosen `protocolVersion`
  - `agentCapabilities`
  - usually `agentInfo`
  - optional `authMethods`

Rules:

- The client sends the latest ACP major version it supports.
- If the agent supports that version, it must echo it back.
- Omitted capabilities mean unsupported.
- New capabilities are non-breaking; do not treat them as mandatory.

Useful capabilities to check:

- Client:
  - `fs.readTextFile`
  - `fs.writeTextFile`
  - `terminal`
- Agent:
  - `loadSession`
  - `promptCapabilities.image`
  - `promptCapabilities.audio`
  - `promptCapabilities.embeddedContext`
  - `mcpCapabilities.http`
  - `mcpCapabilities.sse`

## Session Setup

### Creating a session

- Use `session/new`.
- Pass an absolute `cwd`.
- Optionally include MCP server definitions for the agent to connect to.
- The agent must return a unique `sessionId`.

### Loading a session

- Only valid if `agentCapabilities.loadSession` is true.
- Use `session/load` with the existing `sessionId`, absolute `cwd`, and MCP servers.
- The agent must replay the full session history to the client via `session/update` notifications before answering the original `session/load`.

Rules:

- `cwd` must be absolute.
- Session IDs are the handle for `session/prompt`, `session/cancel`, and `session/load`.
- For reproducible benchmarks, create a fresh session per task and keep task-specific workspace, logs, and memory roots outside any shared resumed session state.

## Prompt Turn

A prompt turn is one user interaction from `session/prompt` until the agent answers that same request.

### Start

- The client sends `session/prompt` with `sessionId` and a `prompt` array of content blocks.
- The client must restrict content types to what the agent advertised during initialization.

### Streaming progress

The agent reports progress through `session/update`, including:

- `plan`
- `agent_message_chunk`
- `user_message_chunk` when replaying history
- `tool_call`
- `tool_call_update`
- `available_commands_update`

### Completion

- If no tool calls remain, the agent must answer the original `session/prompt` with a `stopReason`.
- Common stop reasons documented in ACP:
  - `end_turn`
  - `max_tokens`
  - `max_turn_requests`
  - `refusal`
  - `cancelled`

### Cancellation

- The client may cancel with `session/cancel`.
- After cancelling, the client should mark unfinished tool calls as cancelled locally.
- The client must answer pending permission requests with outcome `cancelled`.
- The agent should stop model work and tool execution quickly.
- The agent must still answer the original `session/prompt` with `stopReason: cancelled`.
- Do not leak cancellation as a generic transport or tool error.

## Tool Calls and Permissions

Tool calls are announced through `session/update`.

Typical flow:

1. agent emits `tool_call` with status `pending`
2. agent optionally sends `session/request_permission`
3. client returns selected or cancelled outcome
4. agent emits `tool_call_update` with `in_progress`
5. agent emits `tool_call_update` with final status and optional content

Status values documented in ACP:

- `pending`
- `in_progress`
- `completed`
- `failed`

Permission option kinds documented in ACP:

- `allow_once`
- `allow_always`
- `reject_once`
- `reject_always`

## File System

Only use these methods if the client advertised support.

- `fs/read_text_file`
- `fs/write_text_file`

Rules:

- Paths must be absolute.
- Line numbers are 1-based.
- `fs/read_text_file` can expose unsaved editor state.
- `fs/write_text_file` should be treated as client-owned file mutation, not direct agent disk access.

## Terminals

Only use terminal methods if `clientCapabilities.terminal` is true.

Methods:

- `terminal/create`
- `terminal/output`
- `terminal/wait_for_exit`
- `terminal/kill`
- `terminal/release`

Rules:

- `terminal/create` returns immediately with `terminalId`.
- `cwd` must be absolute.
- `outputByteLimit` truncates from the start when output grows too large.
- The agent must call `terminal/release` when done, even after `terminal/kill`.

## Slash Commands

- Slash commands are advertised through `available_commands_update`.
- They are executed as ordinary `session/prompt` text such as `/web agent client protocol`.
- The command list may change during a session.

## MCP in ACP Sessions

ACP lets the client hand MCP server connection info to the agent during session setup.

Rules from ACP docs:

- Agents must support MCP stdio transport.
- Agents should support MCP HTTP transport for modern servers.
- MCP SSE transport is still described but marked deprecated by the MCP spec.
- Clients must check `mcpCapabilities.http` or `mcpCapabilities.sse` before using those transport types.

## Failure Checklist

Start here when debugging:

1. Was `initialize` completed successfully first?
2. Are both sides using the same `protocolVersion`?
3. Did the code check capability flags before optional methods?
4. Are all file paths absolute and all line numbers 1-based?
5. Does each `session/prompt` eventually receive exactly one terminal response with a `stopReason`?
6. On cancel, does the agent return `cancelled` instead of surfacing an exception?
