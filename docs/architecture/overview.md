# Target Architecture Overview

## Status

Proposed architecture for phased replacement of the legacy Python desktop application. This document does not authorize removal of legacy code or modification of the DeepSeek wire protocol.

## Architectural goals

The system must be:

- provider-neutral at its core
- streaming and cancellable by design
- independently testable without a live DeepSeek account
- secure by default for credentials and rendered content
- usable through both a Tauri desktop shell and a local HTTP API
- durable through explicit SQLite migrations
- branch-aware for edit/regenerate/compare workflows
- observable without logging secrets or conversation content by default
- packageable on Windows, macOS, and Linux

## Non-goals for the first vertical slice

- Removing the legacy application
- Rewriting the undocumented DeepSeek wire protocol in Rust
- Implementing every provider
- Implementing cloud synchronization
- Exposing the local API beyond loopback
- Visual polish before core/provider/database contracts work

## System context

```text
┌───────────────────────────────────────────────────────────────┐
│ User                                                          │
└───────────────────────┬───────────────────────────────────────┘
                        │
              ┌─────────▼─────────┐
              │ Tauri 2 Desktop   │
              │ React/TypeScript  │
              └─────────┬─────────┘
                        │ typed commands/events
              ┌─────────▼─────────┐
              │ Rust App Core     │◄──────────┐
              │ execution engine  │           │ normalized requests/events
              └───┬───────┬───────┘           │
                  │       │                   │
          ┌───────▼───┐ ┌─▼────────────┐ ┌────┴───────────┐
          │ SQLite    │ │ Auth/Keyring │ │ Axum Local API │
          └───────────┘ └──────────────┘ └────────────────┘
                  │
          provider registry
                  │
       ┌──────────┴──────────┐
       │                     │
┌──────▼───────┐     ┌───────▼────────────────┐
│ MockProvider │     │ DeepSeek Provider       │
│ native Rust  │     │ Rust adapter + sidecar  │
└──────────────┘     └───────────┬────────────┘
                                │ supervised IPC
                     ┌──────────▼───────────┐
                     │ Python protocol worker│
                     │ pinned p2d behavior   │
                     └──────────┬───────────┘
                                │
                     existing chat.deepseek.com protocol
```

## Core boundaries

### Frontend

Responsibilities:

- render application state
- collect user intent
- run command palette and shortcuts
- reduce ordered provider events into transient UI state
- request durable data through commands/queries

Forbidden dependencies:

- provider protocol payloads
- SQL
- credential values after submission
- filesystem paths except user-approved display values
- direct HTTP calls to DeepSeek

### Tauri shell

Responsibilities:

- expose narrow, typed commands
- forward normalized run events
- own desktop lifecycle/capabilities
- open safe external links and native dialogs
- construct the Rust application state

The shell must remain thin. Business rules do not belong in Tauri command handlers.

### Rust application core

Responsibilities:

- execute normalized chat requests
- own run lifecycle and cancellation
- resolve provider/model/account capabilities
- coordinate persistence and events
- implement edit/regenerate/branch commands
- expose the same engine to Tauri and Axum
- produce typed errors and structured tracing

The core must not import Tauri or Axum types.

### Provider abstraction

Responsibilities:

- authenticate/health/model/capability operations
- accept normalized generation requests
- emit normalized, ordered provider events
- honor cancellation
- map provider errors to typed provider errors

DeepSeek session IDs, patch paths, PoW, cookies, and private p2d types remain inside its adapter.

### Persistence

Responsibilities:

- repositories over a migrated SQLite schema
- transactions and FTS maintenance
- stable graph IDs and branch traversal
- legacy data import

The database is durable state, not the complete live application state. Active streams, selected UI panels, and transient partial deltas belong in runtime state.

### Authentication

Responsibilities:

- resolve credential references through OS secure storage
- return account status/capabilities without returning secrets to UI
- provide scoped credential material to provider execution
- redact structured errors/log fields

### Local API

Responsibilities:

- translate HTTP/OpenAI-compatible requests into normalized core requests
- stream core events as SSE
- share provider registry, cancellation, auth, and persistence with desktop

It must not contain a second DeepSeek implementation.

## Dependency direction

```text
apps/desktop frontend  -> Tauri command/event contract
apps/desktop src-tauri -> crates/core + adapter crates
crates/api             -> crates/core
crates/core            -> traits in provider/database/auth + models/common
provider implementations -> provider traits + models/common
concrete database      -> database interfaces + models/common
Python sidecar         -> existing DeepSeek protocol only
```

Rules:

1. `models` and `common` depend on no framework adapters.
2. `core` depends on traits, not concrete p2d/Tauri/Axum types.
3. `api` and Tauri are inbound adapters to `core`.
4. Database, auth, MockProvider, and DeepSeek are outbound adapters.
5. Frontend shared types represent normalized contracts only.
6. Cross-boundary payloads are versioned and schema-tested.

## Principal runtime services

### `ExecutionService`

- validates a normalized request
- resolves account/model/provider
- creates a `run_id`
- starts provider stream with cancellation token
- assigns event sequence numbers
- persists durable events/parts transactionally
- fans events to subscribers
- emits exactly one terminal run event

### `ConversationService`

- creates workspaces/conversations/branches
- edits by creating a new branch rather than mutating history in place
- selects branch heads
- assembles provider context
- supports regenerate/retry/compare semantics

### `ProviderRegistry`

- discovers configured providers
- reports capabilities and models
- resolves a provider by stable ID
- includes mandatory MockProvider in development/test profiles

### `RunRegistry`

- stores active run handles keyed by `run_id`
- owns cancellation tokens and task handles
- prevents conflicting writes to the same branch as policy requires
- supports desktop and HTTP cancellation callers

### `SearchService`

- queries FTS5 and structured filters
- returns stable IDs/snippets
- does not expose raw SQL to UI

### `CredentialService`

- stores/fetches/deletes provider credentials in OS secure storage
- tracks non-secret provider account records in SQLite
- supplies secret values only to provider adapters

## Desktop request flow

```text
React command
  -> invoke Tauri command with normalized request
  -> core validates and returns run_id
  -> core starts provider stream
  -> provider events enter core
  -> core sequences/persists/forwards events
  -> Tauri emits run-scoped event channel
  -> React reducer applies event
  -> UI renders incremental reasoning/answer/source state
```

## Local API request flow

```text
POST /v1/chat/completions
  -> Axum validates/authenticates request
  -> OpenAI adapter creates normalized request
  -> same ExecutionService used by desktop
  -> normalized events
  -> OpenAI SSE translator
  -> HTTP client
```

## State ownership

| State | Owner |
| --- | --- |
| Active run task/cancellation | Rust `RunRegistry` |
| Durable conversations/parts/branches | SQLite repositories |
| Provider wire session IDs | provider metadata/repository behind provider boundary |
| Credential secret | OS credential store |
| Account metadata | SQLite |
| Current UI selection/layout | React client state |
| Query results/cache | TanStack Query |
| Incremental display buffer | chat reducer keyed by run/event sequence |
| Provider implementation details | concrete provider adapter |

## Frontend state direction

Recommended split:

- **TanStack Query:** durable queries and command invalidation (conversations, models, settings, search)
- **Zustand or a small explicit store:** selected workspace/conversation/branch, panel state, command palette
- **Reducer per active run:** ordered streaming state with invariant checks
- **Component-local state:** ephemeral input/focus/menus only

Do not duplicate the entire database in a global frontend store.

## Legacy coexistence

Until replacement parity:

- keep `main.py`, `app/`, `config/`, and `requirements.txt`
- keep the current DeepSeek implementation unchanged except isolated fixes backed by tests
- add new workspace files alongside legacy paths
- use a separate new database path during development
- build a read-only legacy importer before writing to user databases
- retain a launch command for the legacy app
- do not move legacy files merely for aesthetic repository structure

A later commit may move legacy files under `legacy/python-desktop/`, but only after import paths, packaging, data lookup, and rollback are validated.

## Cross-platform packaging strategy

The Tauri bundle must include:

- Rust desktop binary
- frontend assets
- platform-specific Python provider sidecar or embedded Python distribution
- pinned p2d package and WASM artifact
- license notices
- migrations

A packaging spike belongs early in the plan because p2d's Python, NumPy, Wasmtime, and WASM dependencies materially affect bundle size and platform compatibility.

## Quality gates

A feature is not considered integrated unless:

- domain/provider API is typed
- cancellation behavior is tested
- no secret is logged or returned to UI
- migration/persistence behavior is tested where relevant
- MockProvider can exercise the UI path without network
- frontend reducer tests cover event ordering
- protocol-specific code remains outside core/UI
- Windows, macOS, and Linux build implications are documented

## Related documents

- [Legacy audit](legacy-audit.md)
- [Provider architecture](provider.md)
- [Streaming architecture](streaming.md)
- [Database architecture](database.md)
- [Authentication architecture](authentication.md)
- [Desktop architecture](desktop.md)
- [Existing DeepSeek protocol](../protocol/deepseek-existing.md)
- [Architecture decisions](adr/)
