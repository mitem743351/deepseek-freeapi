# Legacy Architecture Audit

**Audit date:** 2026-08-16

**Repository:** `mitem743351/deepseek-freeapi`

**Audited revision:** `19089165d0a0936c23b8e8666b4ab24efa66d4be`

**Scope:** Phase 1 repository reconnaissance only

## Executive summary

The repository is a single-process Python 3 desktop application. Its strongest asset is a working adapter around the unofficial `p2d-deepseek` package and, through that package, the existing `chat.deepseek.com` web protocol. The application already supports answer streaming, DeepThink, web-search flags, short-lived remote conversation context, local SQLite history, token management, and a CustomTkinter UI.

The application is not yet a suitable foundation for the target workstation architecture. `MainWindow` is simultaneously a composition root, application service, run coordinator, persistence coordinator, and UI controller. UI components call the database directly. Provider events are untyped dictionaries. Persistence is a two-table linear model created in application code. Credentials are duplicated in plaintext files. There is no provider interface, migration system, local API, test suite, CI, or real cancellation primitive.

The migration principle is therefore **preserve behavior, not architecture**:

- Preserve the current DeepSeek wire behavior and protocol parser.
- Preserve legacy data through an explicit importer.
- Keep the legacy Python app runnable until replacement parity is demonstrated.
- Build a Rust application core, normalized provider boundary, native MockProvider, SQLite migrations, and Tauri/React shell alongside the legacy app.
- Isolate the Python DeepSeek implementation as a provider sidecar instead of porting an undocumented protocol prematurely.

No legacy source was removed or modified during this audit.

## Audit method and limits

The audit covered every tracked source, configuration, dependency, asset, and startup file in the repository. It also inspected the wheel source for `p2d-deepseek==0.2.4`, which is the latest PyPI release visible on the audit date.

Third-party artifact inspected:

- Package: `p2d-deepseek==0.2.4`
- Wheel SHA-256: `913b6b4a35e964bfd866dc6b958b7f271b8751e1753e493697df0dd6630be54e`
- Upstream repository commit observed: `978603f4d1471d61fa30a0ba0244464a553e081b`
- Upstream repository: <https://github.com/pooraddyy/deepseek-free>

This was a static audit. No real user token was available, so no live DeepSeek request was captured. Fields that the dependency discards—especially search results and richer citation metadata—remain explicitly marked as unknown and require sanitized protocol fixtures before Phase 8.

---

## 1. Current architecture map

### 1.1 Runtime topology

```text
main.py
  ├─ ConfigManager ─────────────── config/settings.json
  ├─ DatabaseManager ───────────── data/chat_history.db
  ├─ AuthManager ──────────────── .env + data/auth_token.json
  └─ MainWindow (CustomTkinter)
       ├─ Topbar
       ├─ Sidebar ─────────────── DatabaseManager directly
       ├─ ChatFrame
       │    └─ MessageBubble ─── MarkdownRenderer + tkinterweb
       ├─ InputFrame
       ├─ SettingsDialog ─────── Auth/Config/Database/MainWindow directly
       ├─ ConversationManager ── in-memory local/remote IDs
       └─ StreamHandler
            └─ daemon Thread
                 └─ DeepSeekWebClient
                      └─ p2d-deepseek
                           ├─ session creation
                           ├─ PoW challenge + WASM solver
                           └─ chat.deepseek.com streaming endpoint
```

This is a monolith with informal layers rather than enforced boundaries. Imports mostly point in the intended direction, but runtime ownership is centralized in the Tk root and UI objects still perform persistence and authentication operations directly.

### 1.2 Startup flow

`main.py` performs the complete boot sequence:

1. Sets CustomTkinter dark appearance and blue theme.
2. Loads `.env` with `python-dotenv`.
3. Creates `ConfigManager`.
4. Opens `DatabaseManager` and initializes tables.
5. Creates `AuthManager` and loads the token.
6. If no token exists, creates a first-run `TokenLoginWindow` and writes the token.
7. Creates `MainWindow`, which creates the DeepSeek client and all UI components.
8. Enters the Tk event loop.
9. On close, the window saves geometry/settings, requests stream stop, closes SQLite, and destroys the root.

A failure at the outermost level is shown using optional `CTkMessagebox`, standard `tkinter.messagebox`, or stderr as a final fallback.

### 1.3 Application coordination

`app/ui/main_window.py::MainWindow` owns:

- `ConfigManager`
- `DatabaseManager`
- `AuthManager`
- `ThemeManager`
- `ConversationManager`
- `DeepSeekWebClient`
- `StreamHandler`
- the cross-thread queue
- current stream state
- token-count display state
- all major widgets

Its `on_send()` method performs domain and UI work in one method:

1. Creates a conversation when needed.
2. Updates the title.
3. Saves the user message.
4. Updates the sidebar.
5. Adds the user bubble.
6. Copies conversation IDs into the DeepSeek client.
7. Disables input and starts a daemon thread.
8. Polls dict events with `after()`.
9. Updates the streaming bubble.
10. Saves the assistant response and remote IDs.

This behavior is useful as a feature reference but must not become the new core API.

### 1.4 Source inventory

| Area | Files | Current responsibility |
| --- | --- | --- |
| Entry point | `main.py` | boot, first-run token UI, top-level errors |
| DeepSeek integration | `app/backend/deepseek_client.py` | p2d adapter, private SSE parser, session IDs, retries, errors |
| Streaming thread | `app/backend/stream_handler.py` | daemon thread and queue event production |
| Auth | `app/backend/auth_manager.py` | plaintext token load/save/delete/mask |
| Conversation state | `app/backend/conversation_manager.py` | selected local ID and ephemeral remote IDs |
| Persistence | `app/utils/database.py` | schema creation, CRUD, search, export |
| Config | `app/utils/config.py` | atomic JSON configuration |
| Rendering | `app/utils/markdown_renderer.py` | Markdown/Pygments HTML and plain text |
| Theme | `app/utils/theme_manager.py` | CTk appearance and color listeners |
| UI composition | `app/ui/main_window.py` | application coordinator and root layout |
| UI components | `app/ui/*.py` | sidebar, chat, bubbles, composer, settings, topbar, loading |
| Assets | `app/assets/**` | icons and JetBrains Mono TTF |

### 1.5 Current feature matrix

| Capability | Current status | Notes |
| --- | --- | --- |
| DeepSeek chat | Working | Existing web protocol through p2d |
| Answer streaming | Working | Final-answer chunks only |
| DeepThink | Partial | enabled by request flag; reasoning delivered after completion |
| Web search | Partial | request flag works; structured results are discarded |
| Multi-turn memory | Session-only | session and parent message IDs are in memory only |
| Local history | Working | SQLite text rows |
| History search | Basic | `%LIKE%` scan/join, no FTS |
| Markdown | Working with caveat | raw HTML is not sanitized |
| Code rendering | Working | custom CTk blocks; no modern semantic AST pipeline |
| Citations | Not preserved | citation markers are stripped |
| Attachments | Not exposed | p2d supports upload/fetch, app wrapper does not |
| Stop generation | Not user-facing / incomplete | cooperative stop only; cannot interrupt every blocked operation |
| Edit/regenerate/branch | Missing | linear schema and UI |
| Local API | Missing | no HTTP server |
| Provider abstraction | Missing | DeepSeek concrete type is wired into UI |
| Secure credential storage | Missing | plaintext `.env` and JSON |
| Structured logging | Missing | isolated standard logging only |
| Tests | Missing | no test files or fixtures |
| CI | Missing | no workflows |
| Native packaging | Missing | resource helpers exist, no packaging config |

---

## 2. Current DeepSeek protocol map

The complete static protocol audit is in [`../protocol/deepseek-existing.md`](../protocol/deepseek-existing.md).

Important summary:

- Base URL: `https://chat.deepseek.com/api/v0`
- Authentication: raw browser `userToken` in the `authorization` header; no paid API key
- Session creation: `POST /chat_session/create`
- PoW challenge: `POST /chat/create_pow_challenge`
- Completion: `POST /chat/completion`
- Transport: line-oriented SSE-like `event:`/`data:` records containing JSON patch objects
- Models: UI `deepseek-v4-flash` → wire `default`; UI `deepseek-v4-pro` → wire `expert`
- DeepThink: `thinking_enabled: bool`; response fragments switch to `THINK`/`THINKING`
- Search: `search_enabled: bool`; current parser only removes completion sentinels
- Continuation: `chat_session_id` plus `parent_message_id`
- Anti-abuse: challenge fields are solved with bundled WebAssembly and sent as base64 `x-ds-pow-response`; a transient `ds_session_id` cookie accompanies completion
- Current wrapper imports private `p2d-deepseek` modules to preserve streaming metadata

This integration is the highest-risk and highest-value behavior to preserve.

---

## 3. Dependency map

### 3.1 Direct Python dependencies

| Dependency | Current purpose | Architectural disposition |
| --- | --- | --- |
| `p2d-deepseek` (unpinned) | DeepSeek web protocol | preserve in isolated Python provider; pin exact tested version |
| `customtkinter>=5.2.0` | legacy desktop UI | retain only while legacy app coexists |
| `Pillow>=10.0.0` | icon/image loading | legacy-only initially; frontend uses web/Tauri assets |
| `markdown>=3.5.0` | Markdown-to-HTML | replace in new UI with sanitized React pipeline |
| `pygments>=2.16.0` | syntax CSS/legacy highlighting | replace new UI with Shiki; may remain in legacy |
| `tkinterweb>=3.23.0` | HTML inside Tk | discard after parity |
| `python-dotenv>=1.0.0` | token/config environment | legacy import compatibility only |
| `httpx>=0.25.0` | direct/transitive HTTP | provider sidecar only |
| `requests>=2.31.0` | declared but not used by repository code | remove after dependency verification |

### 3.2 Important p2d transitive dependencies

`p2d-deepseek==0.2.4` declares:

- `httpx>=0.28.1`
- `numpy>=1.24.0`
- `wasmtime>=28.0.0`

`wasmtime` executes the bundled `DeepSeekHashV1` PoW solver. `numpy` decodes the floating-point result written by the WebAssembly module.

### 3.3 Standard-library dependencies

- `sqlite3`: local history
- `threading`, `queue`: transport isolation and UI handoff
- `json`, `pathlib`, `os`, `stat`: storage/configuration
- `uuid`: stable local IDs
- `webbrowser`: external links
- `tkinter`: underlying GUI runtime and fallback dialogs

### 3.4 Tooling gaps

There is currently no:

- Python lockfile or `pyproject.toml`
- Rust workspace
- Node workspace or lockfile
- formatter/linter configuration committed to the repository
- test runner configuration
- pre-commit hook
- CI workflow
- reproducible build definition
- Tauri or PyInstaller manifest/spec

The unpinned p2d dependency is particularly risky because the application imports private modules whose compatibility is not guaranteed.

---

## 4. Current database and data model

### 4.1 Storage location and connection

- Default path: `data/chat_history.db`
- SQLite timeout: 10 seconds
- `check_same_thread=False`
- `PRAGMA foreign_keys = ON`
- `PRAGMA journal_mode = WAL`
- process-local `threading.RLock`

### 4.2 Schema

```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    model TEXT NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    thinking_content TEXT,
    token_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id) ON DELETE CASCADE
);
```

Indexes exist on conversation update time and `(conversation_id, timestamp)`.

### 4.3 Model characteristics

Strengths:

- UUID message and conversation identifiers are already stable.
- Foreign keys and cascade delete are enabled.
- Writes are transactional and roll back on errors.
- UTC timestamps are timezone-aware ISO strings.
- WAL mode is appropriate for eventual concurrent readers.

Limitations:

- The model is permanently linear; there is no parent-message graph or branch.
- Message content is an opaque text/Markdown blob.
- Reasoning is a single nullable column rather than a part stream.
- Citations, attachments, tools, run metadata, accounts, providers, and workspaces do not exist.
- Provider session/message IDs are not persisted.
- Search uses `LIKE '%query%'` across a join and cannot scale like FTS5.
- Schema creation is embedded in runtime code; there are no numbered migrations or schema version.
- `message_count` is denormalized and manually maintained.
- Approximate token count is `ceil(len(text)/4)`, not provider usage.

### 4.4 Other persisted data

| Path | Contents | Notes |
| --- | --- | --- |
| `config/settings.json` | theme, model, feature toggles, font/window settings | committed defaults and mutable runtime file share a path |
| `.env` | `DEEPSEEK_TOKEN` | plaintext secret, ignored by Git |
| `data/auth_token.json` | `{ "token": "..." }` | duplicate plaintext secret, ignored by Git |

### 4.5 Legacy migration requirement

The replacement database must import rather than overwrite this data:

- Preserve conversation IDs where valid.
- Create one `main` branch per legacy conversation.
- Preserve message IDs and timestamps.
- Convert `content` to a `text` message part.
- Convert `thinking_content` to a `reasoning` message part.
- Mark imported messages `completed`.
- Preserve model names and approximate token counts as legacy metadata.
- Record a migration/import marker so import is idempotent.

---

## 5. Reusable code and behavior

### Preserve directly or adapt

1. **DeepSeek protocol behavior** in `DeepSeekWebClient` and p2d 0.2.4.
2. **SSE patch parsing cases** in `_consume_stream_line()` and fragment helpers.
3. **Session and parent-message tracking** semantics.
4. **Model aliases** and capability flags.
5. **PoW flow**, delegated to p2d and its WASM artifact.
6. **Network retry rule**: one retry before visible output, avoiding duplicated streamed text.
7. **Token redaction concept** in translated exceptions.
8. **Stable UUIDs and UTC timestamp conventions**.
9. **Legacy SQLite reader and export behavior** for migration tooling.
10. **Atomic config writes** and default settings as migration inputs.
11. **Existing app icon and JetBrains Mono asset**, subject to license/package verification.
12. **Feature semantics**: DeepThink toggle, search toggle, model selection, local history, rename/delete/export.
13. **Current error copy** as a starting point for user-facing typed errors.

### Reuse as test fixtures, not production architecture

- Existing queue event examples (`token`, `thinking`, `done`, `error`).
- Existing Markdown samples and code-block parsing cases.
- Current SQLite schema and representative databases.
- Sanitized p2d SSE records captured during Phase 8.

---

## 6. Code and patterns to discard after parity

These should remain available during migration but should not be copied into the new core:

1. CustomTkinter application and widget hierarchy.
2. `MainWindow` as application/service/persistence coordinator.
3. Direct database access from `Sidebar` and `SettingsDialog`.
4. Mutable dicts as the streaming event contract.
5. Global in-memory `ConversationManager` as authoritative state.
6. Inline database schema creation.
7. Plaintext credential persistence as the normal path.
8. Unsanitized Markdown-to-HTML rendering.
9. Thread-plus-polling as the long-term execution engine.
10. String-matching as the primary typed-error system.
11. Hardcoded model list in UI files.
12. UI-owned token validation and provider replacement.
13. Runtime configuration stored in the same committed file used for defaults.
14. Approximate token counts presented as provider usage without provenance.

The legacy Python application itself should only be removed after the new Tauri application passes parity, migration, protocol fixture, and packaging gates.

---

## 7. Security issues

| ID | Severity | Finding | Recommended treatment |
| --- | --- | --- | --- |
| SEC-01 | High | DeepSeek token is duplicated in plaintext `.env` and `data/auth_token.json`. | Store secrets in OS keyring; keep only credential references in SQLite. |
| SEC-02 | High | The full token is loaded into UI variables and entry widget state. | UI should receive only account status and masked metadata; credential entry should be submitted directly to Rust auth service. |
| SEC-03 | High | Markdown permits raw HTML and is not sanitized before `tkinterweb` rendering. | Use `react-markdown`/remark-gfm plus strict `rehype-sanitize`; disable arbitrary raw HTML and remote resource loading by default. |
| SEC-04 | High | `p2d-deepseek` is unpinned while private package APIs are imported. | Pin package and artifact hash; add protocol contract tests and controlled upgrade process. |
| SEC-05 | Medium | Chat history and reasoning are stored unencrypted. | Document local-data sensitivity; consider optional encrypted database/profile and OS-protected backups. |
| SEC-06 | Medium | There is no centralized secret-redaction layer for logs/errors. | Introduce structured fields, secret wrappers, and redacting serializers. |
| SEC-07 | Medium | p2d globally replaces `socket.getaddrinfo` to force IPv4. | Confine dependency to a sidecar process so this global side effect cannot affect the Rust core or desktop runtime. |
| SEC-08 | Medium | No dependency lockfiles, vulnerability scanning, or secret scanning. | Add Cargo/pnpm/uv locks, Dependabot or Renovate, `cargo audit`, and secret scanning in CI. |
| SEC-09 | Low | External links are opened without an allowlist/confirmation policy. | Route links through a Tauri shell allowlist and validate schemes. |
| SEC-10 | Low | POSIX `0600` permissions are best-effort and do not provide equivalent Windows protection. | Use native credential stores instead of filesystem permissions. |

Positive observations:

- Secrets are ignored by Git.
- The wrapper attempts exact-token redaction from error text.
- Token fields are masked visually.
- SQL statements use parameters.
- No telemetry is present.

---

## 8. Concurrency issues

### Current behavior

- One daemon `Thread` is started per response.
- `DeepSeekWebClient` serializes sends with an `RLock`.
- A thread-safe unbounded `queue.Queue` crosses into the Tk main thread.
- Tk polls every 50ms and processes at most 100 events per tick.
- SQLite and configuration managers use process-local `RLock`s.
- Token validation uses a separate daemon thread and queue.

### Issues

1. **Cancellation is only cooperative.** `stop()` sets an event. The HTTP request is interrupted only when another chunk reaches the callback and raises, or when the underlying request returns. It cannot reliably interrupt session creation, PoW, DNS, connect, or a stalled read.
2. **No user-facing Stop control** currently invokes cancellation.
3. **No run ID in queue events.** Stale-event protection depends on prohibiting parallel runs and clearing the queue.
4. **The queue is unbounded.** A fast producer and blocked UI can grow memory.
5. **Daemon threads are not joined.** Shutdown may abandon work abruptly.
6. **Blocking `time.sleep` retry is acceptable only because it occurs off the UI thread**, but it is not cancellable during the sleep.
7. **String/dict events are not exhaustively handled** by a compiler or schema validator.
8. **Remote state is split** between `ConversationManager`, `DeepSeekWebClient`, and p2d's `last_message_id` map.
9. **SQLite is configured for cross-thread use**, but current UI operations mostly happen on the main thread; the relaxed setting can hide future ownership mistakes.
10. **No backpressure or persistence checkpoint policy** exists for long generations.

The Rust core should use Tokio tasks, bounded channels, per-run cancellation tokens, explicit run IDs, and deterministic task shutdown. The Python provider transport must expose or enforce actual socket/process cancellation.

---

## 9. UI architectural problems

The redesigned legacy UI is visually improved, but its architecture remains unsuitable for the target product:

- Widgets depend directly on concrete managers and the root window.
- State is distributed across widget fields without a testable reducer.
- Navigation, persistence, network lifecycle, and rendering are coupled.
- Conversation rendering creates one Tk/HTML widget tree per message; there is no virtualization.
- Model and capability choices are hardcoded in UI modules.
- Message actions are not represented as commands.
- There is no command palette or centralized shortcut registry.
- There is no right-side context/sources panel.
- Search, reasoning, and citations do not have normalized domain models.
- Rendering behavior cannot be tested without a native Tk environment.
- `tkinterweb` adds platform and packaging complexity.
- Error surfaces are UI-specific and receive generic strings.
- Loaded local conversations cannot reliably continue remote context because remote sessions are not restored and historical messages are not replayed.

The new UI should consume typed application snapshots/events and dispatch commands. It must not import provider, database, auth, filesystem, or HTTP implementation details.

---

## 10. Proposed target architecture

```text
React + TypeScript UI
  ├─ feature components
  ├─ command registry / keyboard shortcuts
  ├─ normalized chat reducer
  ├─ TanStack Query for query/cache lifecycle
  └─ Tauri command/event client
                │
                ▼
Tauri 2 shell (thin adapter)
                │
                ▼
Rust Application Core
  ├─ execution/run service
  ├─ conversation graph service
  ├─ provider registry
  ├─ typed errors
  ├─ cancellation and bounded event channels
  ├─ auth/credential abstraction
  ├─ SQLite repositories + migrations + FTS5
  ├─ structured tracing
  └─ shared engine used by desktop and Axum API
          │                         │
          ▼                         ▼
  MockProvider (Rust)       DeepSeekProvider adapter
                                  │ NDJSON IPC
                                  ▼
                           Python provider sidecar
                                  │
                                  ▼
                     Existing DeepSeek web protocol
```

Boundary rules:

1. UI depends only on Tauri command/event contracts and shared frontend types.
2. Tauri commands are adapters; business rules live in `crates/core`.
3. The core depends on provider/auth/database traits, not concrete adapters.
4. The local API calls the same execution service as Tauri commands.
5. Provider implementations emit normalized events and never mutate UI state.
6. Provider credentials are resolved by Rust auth immediately before execution.
7. SQLite stores durable domain state, not the complete live application state.
8. DeepSeek-specific session IDs and protocol details remain inside provider metadata/adapters.

See the focused architecture documents in this directory for details.

---

## 11. Proposed repository tree

Only create directories when a phase introduces real files.

```text
/
├── apps/
│   └── desktop/
│       ├── index.html
│       ├── package.json
│       ├── vite.config.ts
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   ├── features/
│       │   │   ├── chat/
│       │   │   ├── conversations/
│       │   │   ├── search/
│       │   │   ├── settings/
│       │   │   ├── models/
│       │   │   └── accounts/
│       │   ├── hooks/
│       │   ├── lib/
│       │   ├── state/
│       │   ├── types/
│       │   └── main.tsx
│       └── src-tauri/
│           ├── capabilities/
│           ├── src/
│           │   ├── commands/
│           │   ├── events/
│           │   ├── state/
│           │   ├── lib.rs
│           │   └── main.rs
│           ├── Cargo.toml
│           └── tauri.conf.json
├── crates/
│   ├── core/
│   ├── provider/
│   ├── database/
│   ├── auth/
│   ├── api/
│   ├── models/
│   └── common/
├── providers/
│   └── deepseek/
│       ├── pyproject.toml
│       ├── uv.lock
│       ├── adapter/
│       ├── protocol/
│       ├── worker/
│       └── tests/
├── migrations/
├── packages/
│   ├── types/
│   └── ui/
├── tests/
│   ├── integration/
│   ├── fixtures/
│   └── mock-provider/
├── docs/
│   ├── architecture/
│   │   └── adr/
│   ├── protocol/
│   ├── database/
│   └── development/
├── legacy/
│   └── python-desktop/          # move only after imports/builds are adjusted
├── scripts/
├── Cargo.toml
├── package.json
├── pnpm-workspace.yaml
└── README.md
```

During early phases, the current `main.py`, `app/`, `config/`, and `requirements.txt` stay in place. Moving them under `legacy/` is a later, explicit, reversible migration after the new workspace builds.

---

## 12. Migration plan

### Phase 1 — reconnaissance (this deliverable)

- Freeze and document current behavior.
- Record protocol dependency/version/hash.
- Identify boundaries, risks, reusable behavior, and legacy import needs.
- Make documentation-only changes.

### Phase 2 — architecture contracts

- Review and accept ADRs.
- Finalize provider event schema, typed errors, run state machine, and IPC envelope.
- Define compatibility gates for DeepSeek protocol fixtures.

### Phase 3 — workspace foundation

- Add Cargo and pnpm workspaces without moving legacy files.
- Add formatting, linting, typechecking, lockfiles, and basic CI.
- Keep `python main.py` runnable.

### Phase 4 — Rust core and provider interface

- Add domain IDs, requests, capabilities, events, errors, provider trait, run registry, bounded channels, and cancellation tokens.
- Implement mandatory native MockProvider with deterministic scenarios.

### Phase 5 — SQLite persistence

- Add numbered migrations and repositories.
- Add message graph/branches, structured parts, provider metadata, FTS5, and legacy importer.
- Test migrations up/down where feasible and idempotent legacy import.

### Phase 6 — Tauri/React shell

- Add minimal desktop shell with typed IPC and no DeepSeek dependency.
- Display mock conversations and settings from Rust.

### Phase 7 — normalized streaming pipeline

- Connect MockProvider → core → Tauri events → React reducer.
- Implement bounded buffering, event ordering, stop, retry semantics, and run resumption rules.

### Phase 8 — DeepSeek provider adapter

- Pin p2d and preserve current wire behavior in a Python sidecar.
- Add sanitized golden SSE fixtures and parser contract tests.
- Implement hard cancellation and credential handoff.
- Do not remove the legacy client.

### Phase 9 — chat UI

- Implement virtualized messages, secure Markdown, Shiki, composer, edit/regenerate/branch operations, and command registry.

### Phase 10 — search, reasoning, citations, attachments

- Preserve normalized reasoning deltas and source events.
- Capture unknown DeepSeek search/citation/attachment schemas before implementing adapters.

### Phase 11 — local API

- Add Axum endpoints over the same execution engine and provider registry.
- Stream normalized events as OpenAI-compatible SSE.

### Phase 12 — advanced UX

- Add right context panel, workspace/project navigation, command palette, accessibility, and performance work.

### Phase 13 — testing and CI

- Expand unit, contract, integration, frontend, provider, API, migration, and packaging tests.

### Phase 14 — packaging and legacy retirement

- Package Tauri plus the pinned Python sidecar/runtime.
- Run parity and migration tests on Windows, macOS, and Linux.
- Move/remove legacy code only after release criteria pass.

---

## 13. Risk register

| ID | Risk | Likelihood | Impact | Mitigation / gate |
| --- | --- | --- | --- | --- |
| R-01 | DeepSeek changes undocumented endpoint/header/PoW behavior. | High | Critical | Pin dependency, maintain sanitized fixtures, health diagnostics, versioned adapter, fast rollback. |
| R-02 | Private p2d imports break on package upgrade. | High | High | Pin 0.2.4 initially; vendor/patch only under review; contract tests before upgrades. |
| R-03 | Real cancellation cannot interrupt synchronous provider work. | High | High | Define cancellation gate before adapter completion; use cancellable response ownership or supervised per-run subprocess. |
| R-04 | Tauri sidecar packaging differs across three OSes. | Medium | High | Build packaging spike early; produce sidecar artifacts in CI matrix before UI feature expansion. |
| R-05 | OS keyring unavailable on some Linux environments. | Medium | High | Typed `CredentialUnavailable`; documented Secret Service requirement; secure opt-in fallback, never silent plaintext. |
| R-06 | Legacy DB migration loses history or ordering. | Medium | Critical | Read-only backup, idempotent importer, fixture databases, row-count/content checks, rollback. |
| R-07 | Search/citation schemas are currently discarded. | High | Medium | Capture sanitized live fixtures with consent before Phase 10; model unknown events losslessly. |
| R-08 | Dual legacy/new implementations drift. | Medium | High | Feature parity matrix, protocol contract suite shared by both, time-box coexistence. |
| R-09 | Local API exposes credentials/data beyond localhost. | Medium | Critical | Bind loopback by default, explicit enablement, generated auth token, CORS deny-by-default, rate limits. |
| R-10 | Frontend event ordering bugs corrupt displayed state. | Medium | High | Run IDs + sequence numbers, reducer invariants, property tests, replayable event logs without content by default. |
| R-11 | FTS and message graph schema become difficult to evolve. | Medium | Medium | ADR-reviewed migrations, repository layer, migration tests, no UI SQL. |
| R-12 | Raw model output creates XSS/resource-loading risk. | Medium | Critical | Sanitized Markdown allowlist; no raw HTML; controlled link/resource policy. |
| R-13 | Scope expands before a vertical slice works. | High | High | Milestone exit criteria; MockProvider-first vertical slice; defer advanced UX. |
| R-14 | PoW WASM or p2d licensing/artifact packaging is mishandled. | Low/Medium | High | Preserve license notices, verify artifact inclusion/hash, legal review before distribution. |
| R-15 | Reverse-engineered use violates upstream terms or account expectations. | Medium | High | Prominent disclaimer, user-owned credentials, rate moderation, no bypass beyond existing client behavior, legal/product review. |

---

## 14. First implementation milestones

### M0 — audit accepted

Exit criteria:

- Protocol document reviewed against p2d 0.2.4 source.
- Unknown search/citation fields are acknowledged rather than guessed.
- Target boundaries and ADRs are accepted.
- Legacy application remains unchanged and runnable.

### M1 — reproducible workspace

Deliverables:

- Root Cargo workspace and pnpm workspace.
- `rust-toolchain.toml`, Node/pnpm version policy, Python `pyproject.toml`/uv environment for provider tests.
- Lockfiles and baseline CI for formatting/typechecking/tests.
- Legacy app invocation documented and still operational.

Exit criteria:

- Empty/minimal Rust crates compile.
- Minimal React app typechecks and tests.
- Python provider test environment resolves the pinned p2d artifact.

### M2 — core/provider vertical slice

Deliverables:

- Typed IDs, requests, events, capabilities, errors, and provider trait.
- Run state machine with bounded event stream and cancellation token.
- Mandatory MockProvider scenarios: normal, slow, thinking, search, citation, error, cancellation.

Exit criteria:

- Rust tests prove event ordering and cancellation.
- No Tauri, database, or DeepSeek details leak into provider-domain types.

### M3 — migrated persistence

Deliverables:

- SQLite migrations and repository interfaces.
- Message graph/branching schema and FTS5.
- Legacy importer with fixture DBs.

Exit criteria:

- Existing histories import idempotently with stable IDs and content checks.
- Search and branch traversal tests pass.

### M4 — mock-powered desktop slice

Deliverables:

- Tauri shell and React three-panel layout.
- Typed commands/events.
- Conversation list, composer, streaming answer/reasoning, citations panel, and Stop powered only by MockProvider.

Exit criteria:

- MockProvider → Rust core → Tauri event → React reducer works end to end.
- No frontend import references provider protocol or SQL.

### M5 — DeepSeek adapter parity

Deliverables:

- Pinned Python sidecar.
- Existing session/PoW/completion behavior behind provider IPC.
- Golden protocol fixtures, error mapping, redaction, and hard cancellation.

Exit criteria:

- Sanitized contract tests cover normal, thinking, search flag, errors, continuation, and cancellation.
- Legacy and new adapter produce equivalent final answer/session behavior for approved manual test cases.
- The legacy implementation remains available for rollback.

## Phase 1 conclusion

The repository contains a valuable protocol implementation but not a reusable application core. The next safe change is **not UI work**. It is a small, reviewable workspace/contract foundation plus a mandatory MockProvider, while the legacy Python application remains untouched and runnable.
