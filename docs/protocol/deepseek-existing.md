# Existing DeepSeek Web Protocol

**Status:** behavior-preservation reference

**Audit date:** 2026-08-16

**Application revision:** `19089165d0a0936c23b8e8666b4ab24efa66d4be`

**Third-party client audited:** `p2d-deepseek==0.2.4`

## Purpose

This document records how the current application reaches DeepSeek. It is a preservation contract for the future provider adapter; it is not a recommendation to expose protocol details to the UI or Rust domain model.

The endpoint is an undocumented web/mobile protocol and can change without notice. The new architecture must keep this implementation isolated, versioned, tested with sanitized fixtures, and replaceable behind a provider interface.

## Evidence and confidence

Sources inspected:

1. `app/backend/deepseek_client.py`
2. `app/backend/stream_handler.py`
3. `app/backend/conversation_manager.py`
4. `app/backend/auth_manager.py`
5. `p2d-deepseek==0.2.4` wheel source
6. Upstream `pooraddyy/deepseek-free` revision `978603f4d1471d61fa30a0ba0244464a553e081b`

Artifact identity:

```text
p2d_deepseek-0.2.4-py3-none-any.whl
SHA-256 913b6b4a35e964bfd866dc6b958b7f271b8751e1753e493697df0dd6630be54e
```

No live authenticated traffic was captured during the audit. Schemas below are based on code paths the existing dependency requires. Search-result and richer citation payloads are unknown because the current parser discards them.

## Dependency boundary

The application constructs:

```python
from deepseek import DeepSeekClient

client = DeepSeekClient(api_key=token)
```

The current wrapper also imports private package APIs:

```python
from deepseek.chat import send_message_stream
from deepseek.common.common import clean_response, is_junk
from deepseek.models import resolve_model
from deepseek.session import create_session
```

The private imports are used because p2d 0.2.4's public `chat_stream()` yields final-answer chunks but does not expose all stream metadata needed by the app. The application therefore parses the lower-level SSE-like stream itself to retain `session_id`, `message_id`, status, and thinking content.

This is a compatibility hazard. The migration must pin p2d 0.2.4 until provider contract tests approve an upgrade.

## Base URL and endpoint inventory

Base URL:

```text
https://chat.deepseek.com/api/v0
```

| Operation | Method | Path | Used by current app | Timeout in p2d |
| --- | --- | --- | --- | --- |
| Create chat session | POST | `/chat_session/create` | Yes | 30s |
| Create PoW challenge | POST | `/chat/create_pow_challenge` | Yes | 30s |
| Stream completion | POST | `/chat/completion` | Yes | 120s |
| Upload file | POST multipart | `/file/upload_file` | No, dependency supports it | 300s |
| Fetch file state | GET | `/file/fetch_files?file_ids=...` | No, dependency supports it | 30s |

All paths above are appended to the base URL.

## Authentication

### Token origin

The user obtains the `userToken` value from browser Local Storage for `https://chat.deepseek.com`, or equivalently the raw `authorization` request header observed in browser developer tools.

The p2d documentation says to copy the header value **without adding `Bearer `**. The current application does not transform the token; it passes the stripped value directly.

### Request header

Every p2d request receives:

```http
authorization: <raw userToken>
```

The token is not a paid DeepSeek API key. It represents the user's authenticated web session and must be treated as a secret.

### Current local storage

Loading priority in `AuthManager`:

1. `DEEPSEEK_TOKEN` in `.env`
2. external `DEEPSEEK_TOKEN` process environment
3. `data/auth_token.json` key `token`

Saving currently writes both `.env` and `data/auth_token.json`, applies POSIX `0600` where available, and mirrors the value into process environment. This plaintext mechanism is legacy behavior, not the target credential architecture.

## Common request headers

`p2d-deepseek==0.2.4` defines the following base headers:

```http
User-Agent: DeepSeek/2.1.8 iOS/26.5
Content-Type: application/json
x-client-version: 2.1.8
x-client-bundle-id: com.deepseek.chat
x-client-platform: ios
x-client-locale: en_US
x-client-timezone-offset: 19800
x-rangers-id: 7917485426619761413
x-hif-leim: Ql5a/yjz/zex3xnmbjeUY6lBkUvOXmdtHnbRo1X3NslowiVHjNlbI/E=.mkNG7LeTD8tIij8w
x-hif-dliq: 5Dbvz9zqqbD/LEc7fFVybn4c4IL1MiUn/jWIzuycURM33m1CwpC+7To=.d6U9AemELnLxNfir
accept-language: en-US,en;q=0.9
priority: u=3, i
authorization: <raw userToken>
```

The two `x-hif-*` values and client fingerprint headers are dependency-owned opaque constants. They are not user credentials, but they are protocol implementation details and must remain isolated inside the DeepSeek adapter.

### Global networking side effect

Importing `deepseek.common.common` replaces process-global `socket.getaddrinfo` with a wrapper that always requests `socket.AF_INET` (IPv4). This is a strong reason to keep p2d in a sidecar process: it must not alter DNS behavior for Tauri, the local API, or unrelated providers.

## API envelope and errors

Non-streaming JSON endpoints are expected to return a common envelope resembling:

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "biz_data": {}
  }
}
```

p2d considers a response invalid when:

- `code != 0`, or
- `data` is `null`/missing.

Authentication is classified by p2d when:

- `code == 40003`, or
- `msg` contains `invalid token`, or
- `msg` contains `authorization`.

HTTP status failures are reduced by p2d to `DeepSeek API error: <status>`. Connect and connect-timeout failures become `DeepSeekConnectionError`.

The application wrapper further classifies errors by exception type/name and message content:

| Condition | Application error |
| --- | --- |
| `429`, `rate limit`, `too many requests` | `DeepSeekRateLimitError` |
| `401`, `403`, invalid/expired token, authorization | `DeepSeekAuthenticationError` |
| p2d connection error or class name containing connection/timeout/network | `DeepSeekNetworkError` |
| other p2d API error | `DeepSeekClientError` |
| other exception | `DeepSeekClientError` |

Before exposing exception text, the wrapper replaces the exact in-memory auth token with `[redacted]`.

## Session creation

### Request

```http
POST /api/v0/chat_session/create
Content-Type: application/json
authorization: <raw userToken>

{}
```

### Expected response fields

```json
{
  "code": 0,
  "data": {
    "biz_data": {
      "chat_session": {
        "id": "<session-id>"
      },
      "ttl_seconds": 12345
    }
  }
}
```

p2d returns a normalized object:

```json
{
  "session_id": "<session-id>",
  "ttl_seconds": 12345
}
```

The current application retains `session_id` only in memory. Loading a persisted local conversation deliberately resets the remote session because remote session validity is not persisted or guaranteed.

## Proof-of-work challenge

A valid PoW response is required before chat completion and file upload.

### Challenge request

```http
POST /api/v0/chat/create_pow_challenge
Content-Type: application/json
authorization: <raw userToken>

{
  "target_path": "/api/v0/chat/completion"
}
```

For file upload, `target_path` is `/api/v0/file/upload_file`.

### Expected challenge fields

```json
{
  "code": 0,
  "data": {
    "biz_data": {
      "challenge": {
        "algorithm": "<server value>",
        "challenge": "<opaque value>",
        "salt": "<opaque value>",
        "signature": "<opaque value>",
        "difficulty": 123,
        "expire_at": 1234567890,
        "expire_after": 123,
        "target_path": "/api/v0/chat/completion"
      }
    }
  }
}
```

The challenge response also sets a transient `ds_session_id` cookie. p2d first reads the cookie jar and then falls back to parsing `Set-Cookie`.

### Solver

p2d loads bundled WebAssembly:

```text
deepseek/pow/wasm/sha3_wasm_bg.7b9ca65ddd.wasm
```

Observed WASM artifact SHA-256:

```text
b3fca8cc072c1defbd60c02266a8e48bd307a1804aaff4314900aea720e72f7d
```

The solver:

1. Builds prefix `<salt>_<expire_at>_`.
2. Calls the WASM export `wasm_solve(challenge, prefix, difficulty)`.
3. Reads a floating-point answer from WASM memory and converts it to integer.
4. Builds compact JSON:

```json
{
  "algorithm": "DeepSeekHashV1",
  "challenge": "<challenge>",
  "salt": "<salt>",
  "answer": 123456,
  "signature": "<signature>",
  "target_path": "/api/v0/chat/completion"
}
```

5. Base64-encodes the compact JSON. The result is sent as `x-ds-pow-response`.

Do not reimplement this solver in Rust during early migration. Preserve the known-working p2d behavior in the Python provider until fixture and parity tests justify a port.

## Model selection

Public model names and wire aliases:

| Application model | Wire `model_type` |
| --- | --- |
| `deepseek-v4-flash` | `default` |
| `deepseek-v4-pro` | `expert` |
| request with attached file IDs | `vision` |

The current desktop app exposes only the two text model names. Although p2d supports file IDs and `vision`, `DeepSeekWebClient.send_message()` currently passes `ref_file_ids=None`, so attachments are not available in the UI.

## Completion request

### Request

```http
POST /api/v0/chat/completion
Content-Type: application/json
authorization: <raw userToken>
x-ds-pow-response: <base64 compact PoW JSON>
Cookie: ds_session_id=<cookie returned with challenge>
```

Body:

```json
{
  "prompt": "user text",
  "search_enabled": false,
  "chat_session_id": "<session-id>",
  "preempt": false,
  "action": null,
  "model_type": "default",
  "parent_message_id": null,
  "audio_id": null,
  "ref_file_ids": [],
  "thinking_enabled": false
}
```

Fields changed by the current UI:

- `prompt`
- `search_enabled`
- `chat_session_id`
- `model_type`
- `parent_message_id`
- `thinking_enabled`

The rest remain the values shown above.

### Session continuation

First turn:

- Create a remote session.
- Send `parent_message_id: null`.
- Capture returned `response.message_id`.

Following turn:

- Reuse `chat_session_id`.
- Send the previous returned `message_id` as `parent_message_id`.

The app stores current remote IDs in both `ConversationManager` and `DeepSeekWebClient`; the p2d client also has `last_message_id[session_id]`. The wrapper synchronizes these maps.

Remote IDs are not persisted in SQLite. Restarting the app or loading historical chat starts a fresh remote session, and old local messages are not replayed to DeepSeek.

## Streaming transport

### Framing

The response is consumed with `httpx.Client.stream()` and `iter_lines()`. The parser treats it as SSE-like framing:

```text
event: <event-name>
data: <JSON object>
```

Current behavior:

- blank lines are ignored
- every `event:` line is ignored
- non-`data:` lines are ignored
- invalid JSON is ignored

The application does not verify response `Content-Type`.

### Patch object

Data records use compact keys:

```json
{
  "p": "response/fragments/0/content",
  "o": "APPEND",
  "v": "text delta"
}
```

Observed meanings from the parser:

- `p`: response path
- `o`: operation; defaults to `APPEND`
- `v`: value

### Initial/full response form

A record without `p` can contain:

```json
{
  "v": {
    "response": {
      "message_id": 123,
      "status": "WIP",
      "fragments": [
        {"type": "THINK", "content": "..."},
        {"type": "RESPONSE", "content": "..."}
      ]
    }
  }
}
```

A no-path string value is appended according to the current fragment type.

### Supported patch paths

| Path/pattern | Meaning |
| --- | --- |
| `response/fragments` with `APPEND` | append one fragment or a fragment list |
| `response/fragments/<n>/type` | switch current fragment type |
| `response/fragments/<n>/content` | append content to current type |
| `response/fragments/-<n>/content` | also accepted by current regex |
| `response/status` | update status |
| `response/message_id` | capture remote parent ID |

Fragment types recognized:

- `THINK`
- `THINKING`
- `RESPONSE`

Unknown types are not normalized explicitly.

### Current output behavior

The application wrapper accumulates:

- `state.answer[]` for final response
- `state.thinking[]` for reasoning
- `state.message_id`
- `state.status`

Final-answer chunks invoke the UI callback immediately. Thinking chunks are accumulated but are **not** emitted incrementally; `StreamHandler` sends one complete `thinking` event after `send_message()` returns.

Current queue event examples:

```json
{"type":"token","content":"answer delta"}
{"type":"thinking","content":"complete reasoning"}
{"type":"done","content":"answer","session_id":"...","message_id":123,"thinking_content":"..."}
{"type":"error","message":"safe message"}
```

These are legacy UI events, not the target provider contract.

## DeepThink behavior

Request:

```json
{"thinking_enabled": true}
```

Response:

- stream fragments identify reasoning with `type: THINK` or `type: THINKING`
- final answer resumes with `type: RESPONSE`

The current app stores cleaned reasoning in `messages.thinking_content` and can display it after completion. It does not stream reasoning to the UI token-by-token.

The target adapter should translate reasoning to:

```text
ThinkingStarted
ThinkingDelta*
ThinkingCompleted
```

without changing wire behavior.

## Web search behavior

Request:

```json
{"search_enabled": true}
```

The current p2d parser defines the following control strings as junk and drops them:

```text
FINISHEDSEARCH
FINSEARCH
SEARCH_DONE
```

The current parser does not expose:

- search-start payloads
- individual search results
- source titles/URLs/snippets
- search completion metadata

Those schemas must not be guessed. Before implementing `SearchResult` or `CitationReceived` for the real provider, Phase 8 must capture sanitized stream fixtures from an account owner's explicit test session and preserve unknown records losslessly.

## Citations

`clean_response()` removes textual markers matching:

```regex
\[citation:\d+\]
```

This means the legacy final text intentionally loses citation marker identity. No structured citation table exists. The new adapter must inspect raw sanitized fixtures before cleaning and map citation/source records to normalized events and database rows.

## Response cleanup

Both p2d and the application fallback perform cleanup:

1. HTML entity unescape
2. `<br>` → newline
3. remove all other HTML tags
4. remove `[citation:<number>]`
5. collapse 3+ newlines to 2
6. trim

This is lossy. The provider adapter should retain raw normalized parts needed for citations while exposing safe display text separately.

## Search-control sentinels

The following exact strings are suppressed from answer and thinking text:

```text
FINISHEDSEARCH
FINSEARCH
SEARCH_DONE
```

Matching uses `value.strip()`.

## Retry behavior

The application attempts at most two sends (initial plus one retry).

Retry conditions:

- translated error is `DeepSeekNetworkError`
- this is the first attempt
- no visible final-answer chunk has been emitted

Retry delay:

```text
1.0 second
```

If any answer content was emitted, the wrapper does not retry because replay could duplicate visible text.

There is no exponential backoff, `Retry-After` support, jitter, or retry for generic p2d API errors.

## Cancellation behavior

`StreamHandler.stop()` sets a `threading.Event`.

The event is checked inside the final-answer callback. On the next answer chunk, the callback raises `_StreamCancelled`, unwinding the generator and normally closing the `httpx` stream context.

Limitations:

- no current Stop button calls it during a run
- it cannot immediately interrupt DNS, connect, session creation, PoW solving, or a stalled read
- it is not checked during thinking chunks because those do not invoke the callback
- there is no cancellation token in the p2d API
- the daemon worker is not joined

The target architecture's “real cancellation” requirement is not met by the current implementation.

## File and attachment protocol available in p2d

The desktop wrapper does not expose attachments, but p2d 0.2.4 contains working-looking paths that must be evaluated rather than reinvented.

### Upload PoW

Challenge target:

```text
/api/v0/file/upload_file
```

### Upload request

```http
POST /api/v0/file/upload_file
Content-Type: <removed; multipart generated by httpx>
authorization: <raw userToken>
x-file-size: <bytes>
Upload-Draft-Interop-Version: 6
Upload-Complete: ?1
x-thinking-enabled: 0|1
x-model-type: vision
X-DS-PoW-Response: <base64 PoW JSON>
Cookie: ds_session_id=<challenge cookie>
```

Multipart field:

```text
file = (<base filename>, <binary stream>, <guessed MIME type>)
```

The expected normalized upload result contains at least `id`.

### File status request

```http
GET /api/v0/file/fetch_files?file_ids=<comma-separated IDs>
authorization: <raw userToken>
```

The p2d client polls and accepts statuses:

- `SUCCESS`
- `DONE`
- `READY`
- `COMPLETED`

It fails on `FAILED`, `ERROR`, or a parse error code. The source checks several possible status/error field names.

### Completion attachment fields

When using p2d's public client:

```json
{
  "model_type": "vision",
  "ref_file_ids": ["<file-id>"]
}
```

This path is not integrated into `DeepSeekWebClient` today and needs separate protocol fixtures and security limits before exposure.

## Current provider capability truth table

| Capability | Wire/dependency | Current app wrapper | Target-adapter work |
| --- | --- | --- | --- |
| Text chat | Supported | Supported | normalize |
| Answer streaming | Supported | Supported | preserve incremental events |
| Thinking request | Supported | Supported | preserve incremental reasoning |
| Search request | Supported | Flag supported | discover/normalize results |
| Citations | Evidence in raw text | stripped | discover before cleaning |
| Multi-turn session | Supported | active-process only | provider session metadata policy |
| Models | default/expert | exposed as flash/pro | registry/capabilities |
| File upload | p2d supports | not exposed | fixture/security/UX work |
| Vision completion | p2d supports | not exposed | fixture/capability work |
| Cancellation | no explicit API | cooperative/partial | hard cancellation design |
| Health/auth check | session creation | token validation supported | normalized health/auth result |

## Compatibility constraints for the new adapter

The first DeepSeek provider adapter must preserve all of the following unless a fixture-backed change is explicitly reviewed:

1. Raw token in `authorization` header, without adding `Bearer`.
2. Base URL and endpoint paths.
3. Session creation before first message.
4. PoW challenge target and WASM solver behavior.
5. `ds_session_id` cookie propagation from challenge to completion.
6. Completion body field names and default/null values.
7. Model alias mapping.
8. `thinking_enabled` and `search_enabled` booleans.
9. `chat_session_id` plus previous `message_id` continuation.
10. SSE line framing and all currently recognized patch forms.
11. Search sentinel suppression.
12. One safe pre-output network retry.
13. Token redaction from errors/logs.

## Required Phase 8 protocol fixtures

Sanitized fixtures must contain no token, cookie, user prompt, personal response, or opaque credential-derived header values. Capture/construct fixtures for:

1. session-create success
2. invalid/expired token envelope
3. PoW challenge success
4. initial completion response object
5. answer fragment append
6. thinking-to-response transition
7. status and message-ID patches
8. search-enabled stream including every unknown record
9. citation-bearing stream before cleanup
10. rate limit
11. network interruption before output
12. network interruption after output
13. file upload and polling, if attachments enter scope
14. cancellation while thinking and while awaiting answer

Store unknown records losslessly in fixtures. Tests should assert normalized known events while also detecting silently dropped unknown event shapes.

## Provider normalization mapping

Initial mapping proposal:

| Existing condition | Normalized event |
| --- | --- |
| run accepted by core | `RunStarted` |
| first `THINK`/`THINKING` fragment | `ThinkingStarted` |
| reasoning content | `ThinkingDelta` |
| transition to `RESPONSE` | `ThinkingCompleted`, then `MessageStarted` |
| answer content | `MessageDelta` |
| response status complete | `MessageCompleted` |
| raw source record | `SearchResult` / `CitationReceived` after fixture validation |
| successful terminal state | `RunCompleted` |
| cancellation | `RunCancelled` |
| mapped provider error | `RunFailed` with typed code |

Wire fragments must not leak past the adapter.

## Observability constraints

Safe structured fields:

- request/run/conversation IDs generated by the core
- provider name and pinned adapter version
- endpoint operation name, not full URL query if it contains IDs
- model alias
- thinking/search booleans
- HTTP status
- p2d error category
- duration and retry count
- event type and sequence number

Never log:

- `authorization`
- raw token or last four characters as a correlator
- `Cookie` / `ds_session_id`
- `x-ds-pow-response`
- raw challenge/signature
- opaque anti-abuse headers
- prompts, responses, reasoning, search snippets, or attachment bytes by default

## Upgrade policy

Because `requirements.txt` currently leaves `p2d-deepseek` unpinned, environment recreation can change protocol behavior without a repository diff. The provider migration must:

1. Pin `p2d-deepseek==0.2.4` and lock hashes initially.
2. Record the bundled WASM hash.
3. Run provider serialization/parser fixtures on every change.
4. Treat private-import breakage as a controlled adapter upgrade.
5. Keep a known-good packaged sidecar available for rollback.
6. Never substitute the paid DeepSeek API or a guessed web implementation merely to make an upgrade compile.
