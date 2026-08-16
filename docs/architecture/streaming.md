# Streaming and Run Lifecycle

## Goals

Streaming is the primary execution model for both desktop and local API. The design must support incremental answer text, reasoning, search, citations, tools, usage, typed failure, persistence, and real cancellation without coupling consumers to DeepSeek patch records.

## Pipeline

```text
provider transport
  -> concrete provider parser
  -> normalized ProviderEvent stream
  -> Rust ExecutionService
  -> ordering + validation + persistence
  -> bounded broadcast
       ├─ Tauri event adapter -> React reducer
       └─ Axum SSE adapter    -> HTTP client
```

Neither Tauri nor Axum starts provider requests directly. Both call the same execution service.

## Run state machine

```text
Created
  ├─ validation failure -> Failed
  └─ start -> Running
               ├─ provider terminal success -> Completed
               ├─ cancellation requested ----> Cancelling
               │                                ├─ provider abort -> Cancelled
               │                                └─ abort timeout -> Failed(CancellationTimeout)
               └─ provider/core error --------> Failed
```

Terminal states are immutable.

Suggested durable statuses:

```text
pending
running
cancelling
completed
cancelled
failed
```

## Event ordering

A valid run follows these invariants:

1. `RunStarted` is first.
2. Sequence starts at 1 and increases by exactly 1 after core normalization.
3. A section starts before its deltas.
4. A section completes at most once.
5. Message deltas belong to a stable message/part ID.
6. Citations can refer to stable source IDs before or after a text marker, but references are reconciled before `RunCompleted`.
7. Exactly one terminal event is last.
8. No event is forwarded after terminal state.

Example thinking/search/answer run:

```text
RunStarted
ThinkingStarted
ThinkingDelta...
ThinkingCompleted
SearchStarted
SearchResult...
SearchCompleted
MessageStarted
MessageDelta...
CitationReceived...
MessageCompleted
UsageReceived (optional)
RunCompleted
```

Providers are not required to support every section. The core validates ordering according to reported capabilities.

## Event identity

Each envelope contains:

```text
schema_version
request_id
run_id
sequence
occurred_at
provider_id
conversation_id
branch_id
message_id (when applicable)
part_id (when applicable)
event payload
```

React and HTTP clients use `(run_id, sequence)` for deduplication and ordering. Clearing a queue is not a correctness mechanism.

## Core coordination

`ExecutionService` should:

1. validate request/capabilities
2. allocate stable run/message/part IDs
3. persist pending run and user message transactionally
4. register cancellation token and task handle
5. start provider stream
6. normalize/validate each event
7. update an in-memory run projection
8. persist durable deltas or checkpoints
9. forward bounded events
10. persist terminal metadata
11. unregister active run

## Persistence strategy

Writing one SQLite transaction per character is unacceptable. Recommended policy:

- buffer text/reasoning deltas in memory
- broadcast each normalized delta promptly
- checkpoint accumulated parts on a time/size threshold, such as 250ms or 8–32KiB
- flush immediately on section completion, cancellation, failure, or shutdown
- use one writer transaction per checkpoint
- record last persisted event sequence

After a crash, a running message can be recovered as `interrupted` with its last checkpointed content.

Exact thresholds must be benchmarked rather than hardcoded as architectural truth.

## Bounded channels and backpressure

Use bounded Tokio channels between provider and core. Policies:

- never drop terminal, error, citation, tool, or lifecycle events
- coalesce adjacent text/reasoning deltas when a consumer is slow
- cap per-run buffered bytes
- fail safely with a typed backpressure/protocol error if limits are exceeded
- disconnecting one subscriber must not cancel a run unless it owns the cancellation policy

Tauri and HTTP adapters may have separate subscriber buffers.

## React reducer

The frontend reducer is a pure function over normalized envelopes:

```text
(state, event) -> state
```

It tracks:

- last sequence per run
- run status
- active thinking part
- active answer part
- search/result map
- citation map
- tool-call map
- usage and timing
- typed failure

Reducer behavior:

- duplicate sequence: ignore and report diagnostic
- gap: request snapshot/reconciliation or mark stream desynchronized
- wrong run ID: route to corresponding run, never current-selection state implicitly
- post-terminal event: reject and report
- late UI mount: load durable snapshot then subscribe from known sequence if supported

Reducer tests should replay complete fixture streams.

## Tauri event delivery

Recommended event channel naming:

```text
run://<run_id>
```

Or use Tauri channels returned by `start_run` if Tauri 2 channel semantics fit packaging targets better.

Commands:

```text
start_run(request) -> { run_id, initial_snapshot }
stop_run(run_id)
get_run(run_id)
retry_run(run_id)
regenerate(message_id, options)
```

The frontend subscribes before or atomically with run start to avoid missing early events.

## Local API SSE translation

The Axum adapter consumes the same normalized stream.

For OpenAI-compatible `POST /v1/chat/completions`:

- translate `MessageDelta` to `chat.completion.chunk`
- translate reasoning only through an explicitly documented extension field
- map terminal success to finish reason and `[DONE]`
- map cancellation/client disconnect to core cancellation policy
- map typed errors to HTTP status before headers, or terminal SSE error after streaming begins

The API adapter never calls the DeepSeek sidecar itself.

## Real cancellation

### Desktop flow

```text
Stop button / Escape
  -> stop_run(run_id)
  -> RunRegistry cancellation token
  -> provider cancellation path
  -> active HTTP operation/process is closed
  -> provider emits/returns cancellation
  -> core flushes partial state
  -> RunCancelled terminal event
```

### Requirements

- cancellation is idempotent
- provider network/sidecar work actually stops
- cancellation has a bounded deadline
- partial text can be retained with `cancelled` status
- no automatic retry after cancellation
- no events after terminal cancel
- UI remains able to start another run after cleanup
- process shutdown cancels and awaits active runs within a deadline

### DeepSeek constraint

The current Python callback only notices cancellation on answer deltas. The new adapter must own a cancellable transport handle or terminate a supervised per-run process. This is a release gate, not a later polish item.

## Retry and regeneration

Distinguish:

- **transport retry:** provider-internal, same run, only before visible output
- **retry failed run:** new run linked to failed run metadata
- **regenerate assistant:** new branch/run from the same parent user message
- **edit user message:** new branch from the edited message's parent

Never erase the original failure/answer to make a retry appear linear.

## Search, citation, and tool events

Search and tool activity should stream independently from answer text. The right context panel can render them without parsing Markdown.

A citation event should include:

```text
citation_id
source_id
url
title
snippet (optional)
provider_rank (optional)
message_id / part_id association
provider_metadata (opaque, backend-only)
```

Raw DeepSeek schemas remain unknown until fixture capture. Unknown records must be retained in adapter diagnostics rather than silently discarded.

## Structured logging

Per-run spans:

```text
request_id
run_id
conversation_id
branch_id
provider
model
event
sequence
duration_ms
retry_count
error_code
```

Do not log event text, reasoning, URLs with sensitive query parameters, credentials, cookies, PoW values, or attachments by default.

## Test matrix

### Core

- valid normal ordering
- thinking/search/citation ordering
- duplicate/gap/post-terminal rejection
- bounded channel coalescing
- cancellation before start, during think, during answer, during retry delay
- failure before and after partial output
- persistence checkpoint and recovery
- exactly one terminal event under races

### Frontend

- reducer replay for every MockProvider scenario
- switching conversations during a run
- late/duplicate/out-of-order event handling
- Stop state and optimistic UI
- partial cancelled/failed message rendering

### API

- streaming and non-streaming translation
- disconnect cancellation
- pre-stream and mid-stream typed errors
- `[DONE]` exactly once

### DeepSeek adapter

- sanitized SSE fixtures
- session/message ID capture
- thinking transition
- search/citation unknown-record detection
- pre-output retry
- hard cancellation deadline
