# Desktop and Frontend Architecture

## Stack

- Tauri 2 desktop shell
- React + TypeScript
- Vite
- Tailwind CSS
- a restrained accessible component system (Radix primitives are a candidate)
- TanStack Query for durable backend queries/mutations
- a small predictable client store such as Zustand for UI selection/layout
- reducer-driven active run state
- TanStack Virtual for long timelines/lists where measurement supports it
- `react-markdown` + `remark-gfm` + strict `rehype-sanitize`
- Shiki for syntax highlighting
- Vitest + Testing Library

Final library choices should be recorded in package-level decisions and kept minimal.

## Desktop shell boundary

`apps/desktop/src-tauri` is an adapter over the Rust core. It owns:

- Tauri builder/plugins/capabilities
- application state construction
- typed command handlers
- mapping core streams to Tauri channels/events
- native window/menu/dialog integration
- safe shell/open-link policy
- sidecar resource path resolution and packaging

It does not own provider protocol, SQL, run state machine, or branch rules.

## Frontend feature structure

```text
src/
├── app/
│   ├── App.tsx
│   ├── routes.tsx
│   ├── providers.tsx
│   └── command-registry.ts
├── components/
│   ├── layout/
│   ├── markdown/
│   ├── code/
│   └── primitives/
├── features/
│   ├── chat/
│   │   ├── components/
│   │   ├── reducer/
│   │   ├── commands/
│   │   └── api/
│   ├── conversations/
│   ├── search/
│   ├── settings/
│   ├── models/
│   └── accounts/
├── hooks/
├── lib/
│   ├── tauri.ts
│   ├── markdown.ts
│   └── shortcuts.ts
├── state/
├── types/
└── main.tsx
```

Keep generic primitives in `packages/ui` only when there is a second real consumer or a clear packaging boundary; avoid premature package extraction.

## Primary layout

```text
┌────────────────┬──────────────────────────────────┬──────────────────┐
│ Navigation     │ Conversation                     │ Context          │
│                │                                  │                  │
│ workspace      │ header/model/run status          │ sources          │
│ new chat       │ virtualized message graph path   │ citations        │
│ search         │ reasoning + answer parts         │ attachments      │
│ conversations  │                                  │ run metadata     │
│ projects       │ composer / stop                  │ details          │
└────────────────┴──────────────────────────────────┴──────────────────┘
```

The right panel is collapsible and remembers width/open state as a UI preference. On smaller windows it becomes an overlay/drawer.

## Design language

- dark-first neutral surfaces
- dense but readable information hierarchy
- restrained 4–8px radii for most controls
- subtle one-pixel borders
- typography and whitespace rather than cards for grouping
- no decorative gradients by default
- semantic color used sparingly for status/actions
- keyboard focus visible everywhere
- resizing down to documented minimum without clipped critical actions

The current CTk palette can inform visual continuity, but the React design tokens become the source of truth for the new desktop app.

## Tauri command surface

Initial commands should be narrow and typed:

```text
get_bootstrap_state
list_workspaces
list_conversations
get_conversation
create_conversation
rename_conversation
archive_conversation
delete_conversation
search_conversations
list_providers
list_models
list_accounts
save_provider_credential
validate_provider_account
logout_provider_account
start_run
stop_run
retry_run
regenerate_message
edit_message
select_branch
update_settings
export_conversation
```

Commands return DTOs or typed command errors, not database rows or provider payloads.

## Event surface

Prefer run-scoped Tauri channels where possible. If global events are used, every envelope carries schema version and `run_id`.

Frontend subscription lifecycle:

1. prepare reducer
2. invoke `start_run`
3. atomically receive channel/run ID
4. apply initial snapshot
5. process monotonic events
6. unsubscribe on terminal event/unmount
7. query durable state to reconcile when needed

## Message rendering

Message UI renders structured parts:

```text
text         -> sanitized Markdown
reasoning    -> collapsible reasoning viewer
code         -> Shiki code block + copy
image        -> controlled asset URL
attachment   -> file card
citation     -> inline reference + context panel source
 tool_call    -> structured call card
 tool_result  -> structured result card
```

Raw provider HTML is never mounted.

### Markdown security

- do not enable arbitrary raw HTML
- sanitize links and protocols
- block remote images by default or proxy with explicit policy
- add `rel="noopener noreferrer"`
- route external opening through Tauri allowlist
- cap nesting/document size
- render unknown nodes as text

### Code rendering

- Shiki worker or cached highlighter
- language label and copy button
- horizontal scrolling
- line wrapping toggle where useful
- avoid re-highlighting unchanged blocks on every text delta
- during streaming, render lightweight plain code; highlight on fenced block completion/debounce

## Virtualization

Use virtualization for:

- conversation list
- global search results
- long message timelines when performance measurements justify it

Variable-height Markdown and expanding streams require measurement-aware virtualization. Keep the actively streaming item mounted and anchor scroll behavior explicitly.

## Chat composer

Capabilities:

- multiline input
- Ctrl/Cmd+Enter send
- configurable Enter behavior if desired
- DeepThink toggle from provider capability
- web search toggle from provider capability
- model/account selector
- attachment picker only when capability is enabled
- Stop replaces Send during active generation
- draft persistence per conversation/branch
- token/size warnings based on known limits, not fabricated exact usage

No credential values or provider HTTP details belong in composer state.

## Message actions

Actions dispatch commands:

- copy text
- copy code
- edit user message
- regenerate assistant response
- retry failed run
- branch from message
- compare sibling answers
- export

Edit/regenerate never mutate prior graph nodes in place.

## Command palette

Define commands in a central registry:

```ts
type AppCommand = {
  id: string;
  title: string;
  keywords: string[];
  shortcut?: Shortcut;
  isEnabled(ctx: CommandContext): boolean;
  execute(ctx: CommandContext): Promise<void> | void;
};
```

Initial shortcuts:

| Shortcut | Command |
| --- | --- |
| Ctrl/Cmd+K | global search |
| Ctrl/Cmd+N | new conversation |
| Ctrl/Cmd+P | command palette |
| Ctrl/Cmd+F | search current conversation |
| Ctrl/Cmd+Enter | send |
| Escape | stop active generation / close overlay by priority |

Use platform-aware labels and avoid feature components registering conflicting global handlers independently.

## Query and state model

### TanStack Query

Use for:

- workspaces
- conversation summaries
- conversation snapshots
- provider/accounts/models
- settings
- search

Mutations invalidate or update precise query keys.

### Client store

Use for:

- selected workspace/conversation/branch
- sidebar and context-panel state
- command palette
- active draft identifiers
- non-durable layout preferences before persistence

### Run reducer

Use for ordered deltas/lifecycle. Do not append provider tokens directly into TanStack Query cache on every character. Reconcile durable query data at checkpoints/terminal events.

## Accessibility

- semantic buttons/navigation/main/aside regions
- full keyboard navigation
- visible focus rings
- ARIA labels for icon controls
- status announcements for run start/completion/error without reading every token
- prefers-reduced-motion support
- contrast verification
- resizable text without unusable clipping
- shortcuts discoverable and configurable later

## Error UX

Typed errors map to:

- inline message/run status for generation failures
- account remediation for auth expiry
- retry-after indicator for rate limits
- persistent banner for database/provider unavailable
- details action containing request/run ID, not secret diagnostics

Do not show raw Rust/Python exception strings.

## Packaging

Tauri bundle configuration must explicitly include:

- sidecar executable/runtime per target triple
- p2d Python package and WASM
- migrations
- frontend assets
- icons and license notices

Required CI targets:

- Windows x86_64
- macOS arm64 and x86_64 strategy
- Linux x86_64 with documented WebKit/Secret Service requirements

Sidecar discovery uses Tauri resource APIs, never current working directory assumptions.

## Frontend tests

- reducer fixtures for all MockProvider scenarios
- composer keyboard behavior
- Stop transition/cancellation command
- conversation list search/selection
- edit/regenerate/branch command dispatch
- Markdown sanitization and unsafe-link tests
- code copy/highlighting
- citations/right-panel synchronization
- command registry and shortcut priority
- accessibility checks for core flows

## Tauri integration tests

Use mock core/provider adapters where possible. A full end-to-end test should exercise:

```text
MockProvider -> Rust core -> Tauri channel -> React reducer -> visible output
```

No frontend test requires a real DeepSeek account.
