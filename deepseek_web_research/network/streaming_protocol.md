# Streaming protocol

## Web chat conclusion
**Finding:** The web-chat streaming transport and frame schema are **UNKNOWN — NOT OBSERVABLE FROM AUTHORIZED CLIENT BEHAVIOR**.
**Evidence:** No authorized DevTools Network capture exists in this package.
**Confidence:** UNKNOWN.

## Official API reference (do not treat as a captured web trace)
**Finding:** The documented API uses an HTTPS completion request with `stream: true`; the response uses `text/event-stream`, data-only SSE partial-message deltas, and terminal `data: [DONE]`.
**Evidence:** [Official Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/).
**Confidence:** HIGH.

Conceptual, sanitized API framing from the documentation:
```text
data: {"id":"<completion-id>","object":"chat.completion.chunk",
       "choices":[{"index":0,"delta":{"content":"partial text"}}]}

data: {"id":"<completion-id>","object":"chat.completion.chunk",
       "choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```
The docs also specify an optional final usage-only chunk when `stream_options.include_usage` is enabled. Reasoning-mode deltas are documented in the API schema; whether consumer web displays or persists them is unknown.

## Safe client implementation requirements
1. Begin a request with an abort/cancellation handle.
2. Validate `Content-Type`; incrementally UTF-8 decode and split SSE records, not arbitrary TCP chunks.
3. Ignore non-data control/comment records; parse JSON only from complete `data:` payloads.
4. Append recognized delta fields immutably; render a temporary assistant message.
5. Treat terminal finish metadata and `[DONE]` as distinct signals; persist only after success policy is met.
6. On user stop, abort the app-owned request and mark the partial response as interrupted locally. Do not assume any particular remote cancellation endpoint.
7. Redact request/response logging by default.
