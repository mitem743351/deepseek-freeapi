# Observed web streaming protocol — Phase 2

## Current result
**Finding:** Normal consumer-web generation transport, content type, framing, event names, completion/error signals, and cancellation behavior remain **UNKNOWN — NOT OBSERVABLE FROM AUTHORIZED CLIENT BEHAVIOR** in this repository.
**Evidence:** C01–C06 scenario worksheets are all pending; no sanitized Network evidence exists.
**Confidence:** HIGH.

## Evidence required before making a protocol claim
- C01 and C02: request initiator, response MIME type, connection timing, and sanitized frame/response structural samples.
- C03: normal UI stop action and any observed request abort/follow-on operation; distinguish browser cancellation from server acknowledgment.
- C04/C06: whether visible state reuses or creates an observable message/conversation representation.
- C05: naturally surfaced retry sequence only.

Do not label fetch `ReadableStream`, EventSource/SSE, WebSocket, chunked HTTP, or any other mechanism without direct DevTools evidence. The Phase 1 API-only SSE reference remains separate in `network/streaming_protocol.md`.
