# Provider Architecture

## Objective

Treat DeepSeek as one provider implementation, not as the application. Core, database, Tauri, React, and local API code must operate on normalized provider contracts and typed errors.

## Provider responsibilities

A provider implementation owns:

- authentication validation and logout hooks
- provider health
- model discovery
- capability reporting
- provider conversation/session creation where needed
- request serialization
- streaming response parsing
- provider-specific retries
- provider-specific cancellation mechanics
- mapping wire errors to typed provider errors
- mapping wire events to normalized events

It does not own:

- UI state
- general conversation/branch persistence
- application settings
- Tauri events
- OpenAI HTTP response formatting
- user-facing error copy

## Stable identifiers

Use opaque stable newtypes in Rust:

```rust
ProviderId
ProviderAccountId
ModelId
WorkspaceId
ConversationId
BranchId
MessageId
MessagePartId
RunId
CitationId
AttachmentId
ToolCallId
```

Provider-specific IDs are never substituted for application IDs. DeepSeek `chat_session_id` and `message_id` belong in provider session/generation metadata.

## Conceptual Rust interface

Exact signatures should be finalized in Phase 2, but the boundary should resemble:

```rust
#[async_trait]
pub trait Provider: Send + Sync {
    fn id(&self) -> ProviderId;

    async fn authenticate(
        &self,
        context: AuthContext,
        credential: SecretCredential,
    ) -> Result<ProviderAccount, ProviderError>;

    async fn logout(
        &self,
        account: &ProviderAccount,
    ) -> Result<(), ProviderError>;

    async fn health(
        &self,
        account: Option<&ProviderAccount>,
    ) -> Result<ProviderHealth, ProviderError>;

    async fn list_models(
        &self,
        account: &ProviderAccount,
    ) -> Result<Vec<ModelDescriptor>, ProviderError>;

    fn capabilities(&self) -> ProviderCapabilities;

    async fn create_conversation(
        &self,
        request: ProviderConversationRequest,
        cancellation: CancellationToken,
    ) -> Result<ProviderConversation, ProviderError>;

    async fn stream_message(
        &self,
        request: ProviderRequest,
        cancellation: CancellationToken,
    ) -> Result<ProviderEventStream, ProviderError>;
}
```

`send_message()` need not duplicate `stream_message()`. A convenience method can collect the stream in a provider extension trait or core service. `cancel()` should normally be represented by a cancellation token and run handle; providers may additionally expose a provider-specific abort hook.

## Capabilities

Capabilities must be data, not UI assumptions:

```rust
pub struct ProviderCapabilities {
    pub streaming: bool,
    pub reasoning: bool,
    pub web_search: bool,
    pub citations: bool,
    pub attachments: AttachmentCapabilities,
    pub tools: bool,
    pub native_conversations: bool,
    pub continuation: ContinuationMode,
    pub hard_cancellation: bool,
}
```

The UI renders controls from capabilities. For example, attachment controls stay disabled until the DeepSeek adapter has fixture-backed upload support even though p2d contains file APIs.

## Normalized request

```rust
pub struct ProviderRequest {
    pub request_id: RequestId,
    pub run_id: RunId,
    pub provider_id: ProviderId,
    pub account_id: ProviderAccountId,
    pub model_id: ModelId,
    pub conversation_id: ConversationId,
    pub branch_id: BranchId,
    pub parent_message_id: Option<MessageId>,
    pub messages: Vec<ProviderMessage>,
    pub reasoning: ReasoningMode,
    pub web_search: bool,
    pub attachments: Vec<ProviderAttachment>,
    pub metadata: ProviderRequestMetadata,
}
```

Provider messages contain normalized parts; they are not OpenAI request JSON and not DeepSeek completion payloads.

## Normalized events

Every event carries a common envelope:

```rust
pub struct EventEnvelope {
    pub schema_version: u16,
    pub request_id: RequestId,
    pub run_id: RunId,
    pub sequence: u64,
    pub occurred_at: DateTime<Utc>,
    pub provider_id: ProviderId,
    pub event: ProviderEvent,
}
```

Event variants:

```text
RunStarted
ThinkingStarted
ThinkingDelta
ThinkingCompleted
SearchStarted
SearchResult
SearchCompleted
MessageStarted
MessageDelta
MessageCompleted
CitationReceived
AttachmentProcessed
ToolCallStarted
ToolCallDelta
ToolCallCompleted
UsageReceived
ProviderMetadata
RunCompleted
RunCancelled
RunFailed
```

Rules:

1. Sequence numbers are assigned or validated by the Rust core.
2. Exactly one terminal event (`RunCompleted`, `RunCancelled`, `RunFailed`) occurs.
3. Deltas precede their corresponding completed event.
4. Unknown provider wire events are logged as metadata diagnostics and can be retained in sanitized fixtures; they are never silently reinterpreted.
5. Event payloads do not contain credentials, cookies, PoW responses, or raw headers.
6. Provider metadata is namespaced and cannot become a frontend dependency.

## Typed provider errors

```text
AuthenticationRequired
AuthenticationExpired
ProviderUnavailable
RateLimited { retry_after }
NetworkError { retryable }
ProtocolError { stage, safe_detail }
InvalidRequest
CapabilityUnsupported
RequestCancelled
SidecarUnavailable
SidecarProtocolMismatch
UnknownProviderError
```

Errors include a stable code and safe message. Diagnostic source chains remain in structured logs under redaction. The frontend receives no raw exception string by default.

## DeepSeek adapter composition

```text
DeepSeekProvider (Rust)
  ├─ capability/model mapping
  ├─ credential resolution request
  ├─ sidecar lifecycle supervision
  ├─ NDJSON command/event codec
  ├─ normalized error/event mapping
  └─ cancellation enforcement
          │
          ▼
Python sidecar supervisor
  ├─ pinned p2d-deepseek
  ├─ current request serializer
  ├─ current SSE patch parser
  ├─ session/parent ID handling
  ├─ PoW/WASM behavior
  └─ per-run cancellable execution unit
```

The Python adapter is an anti-corruption layer. No Python class or p2d dictionary crosses into core types.

## Sidecar IPC

Preferred initial transport: versioned newline-delimited JSON over stdin/stdout.

Reasons:

- no listening port
- simple supervision by Tauri/Rust
- easy fixture/replay tests
- language-neutral
- stdout can be reserved for protocol; stderr for redacted logs

Command envelope example:

```json
{
  "version": 1,
  "kind": "start_run",
  "request_id": "...",
  "run_id": "...",
  "payload": {}
}
```

Event envelope example:

```json
{
  "version": 1,
  "kind": "provider_event",
  "request_id": "...",
  "run_id": "...",
  "sequence": 12,
  "payload": {
    "type": "message_delta",
    "text": "hello"
  }
}
```

Control commands:

```text
hello / protocol negotiation
health
validate_credential
start_run
cancel_run
shutdown
```

IPC requirements:

- bounded maximum frame size
- strict schema validation
- explicit protocol version negotiation
- no token on process command line
- no token in environment when avoidable
- no logs on stdout
- heartbeat and startup timeout
- crash maps to `SidecarUnavailable`
- malformed frame terminates or quarantines the sidecar

## Credential handoff

Rust retrieves the secret from OS secure storage immediately before provider use. It sends the secret through the private stdin pipe in a scoped command, not through:

- CLI arguments
- environment variables
- SQLite
- Tauri events
- frontend state
- log fields

The Python worker holds it only for the required account/run lifetime and must redact it from exception strings before returning errors.

## DeepSeek session strategy

The application graph remains provider-neutral. A DeepSeek provider session record may contain:

```text
provider_account_id
conversation_id / branch_id
remote_session_id
remote_parent_message_id
expires_at (if known)
adapter_version
```

Policy:

- Reuse valid remote session and parent ID for active continuation.
- Start a fresh remote session if metadata is absent/expired.
- Do not pretend local history was supplied to DeepSeek when it was not.
- If replay is supported later, make it explicit and bounded by provider capabilities.
- Editing/regeneration creates branch-specific provider continuation metadata.

## Cancellation requirement

The existing synchronous generator is not reliably interruptible at every stage. The adapter is not complete until cancellation closes the active network operation.

Candidate implementation order:

1. Try an owned response/client handle that a control thread can close safely and prove it with tests.
2. If httpx/p2d ownership cannot guarantee interruption, use a supervised per-run child process and terminate it on cancellation.
3. Preserve session/parent IDs in request/response envelopes so per-run process isolation does not lose continuation.
4. Measure PoW/WASM cold-start cost and consider a long-lived supervisor with isolated run workers.

“Stop rendering” is not an accepted implementation.

## Retry ownership

Provider adapter owns protocol retries; core owns user/application retry commands.

For DeepSeek initial parity:

- one retry for retryable network failure
- retry only before visible output
- cancellation interrupts retry delay
- emit retry diagnostics to tracing, not an extra user message
- honor `Retry-After` if a future fixture proves it exists

Core-level “Retry” creates a new run and durable generation metadata; it does not hide a failed run.

## Mandatory MockProvider

MockProvider is a first-class native Rust provider and must land before real DeepSeek integration.

Deterministic scenarios:

| Scenario | Behavior |
| --- | --- |
| normal | message start, multiple deltas, complete |
| slow | configurable inter-delta delay |
| thinking | thinking lifecycle before answer |
| search | search start, results, complete, answer citations |
| citations | multiple structured source events |
| error-before-output | typed retryable/non-retryable failure |
| error-after-output | partial answer then failure |
| cancellation | blocks until token is cancelled, then terminal cancel |
| malformed-order test double | invalid event sequence for core validation tests |

Scenario selection belongs in test/development metadata, not production UI conditionals.

## Provider contract tests

Every provider implementation must pass shared tests for:

- stable identity and capability reporting
- event envelope/run ID correctness
- monotonic sequence
- exactly one terminal event
- cancellation deadline
- no post-terminal event
- safe error mapping
- no secret fields in serialized events
- unsupported capability behavior
- continuation metadata round-trip

DeepSeek adds fixture tests for request body, headers (with secrets replaced), PoW envelope shape, stream patch parsing, model aliases, thinking transitions, and error mapping.

## Versioning

Version independently:

- Rust provider trait contract
- normalized event schema
- sidecar IPC schema
- DeepSeek adapter implementation
- p2d dependency/artifact
- protocol fixtures

A p2d update does not automatically imply a normalized event schema change. Adapter compatibility code absorbs provider-specific differences.
