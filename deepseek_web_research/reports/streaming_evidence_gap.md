# Streaming evidence gap

## What is established
**Finding:** Normal generation uses XHR in this capture, with `text/event-stream; charset=utf-8` responses from `/api/v0/chat/completion`.
**Evidence:** 11 raw completion operations, all HTTP 200, all with that content type and repeated `LOADING` lifecycle entries.
**Classification:** OBSERVED.

## What is not established
The export has `stream_observations: []`, completion `response_schema: null`, and no raw frame bodies. Searches across the parsed data for stream/event/delta/data/done/finish/error-related keys found observer metadata and route names, not exported SSE payloads.

> **SSE transport observed. SSE event payload schema NOT captured.**

There is no evidence of event names, `data:` record contents, JSON shape, terminal sentinel, heartbeat, tool/status event, or server cancellation event. Repeated XHR `LOADING` states are not an event schema.

## Safe upgrade
`devtools_observer/phase4_stream_observer.js` passively observes *future* XHR progress deltas. It does not change request arguments or headers, consume a fetch body, send data, or persist raw response text. It derives only byte/character deltas, SSE-like framing presence, event/data line counts, and parsed JSON **shape** where possible. If `responseText` is inaccessible, it records `NOT_ACCESSIBLE` rather than interfering with the application.
