# SSE protocol v5

## Observed state machine
```text
REQUESTED
  → XHR HEADERS_RECEIVED
  → XHR LOADING (5–271 notifications observed)
  → XHR DONE
```

This is an XHR lifecycle state machine, not an SSE application-event state machine. All ten generation operations returned HTTP 200 with `text/event-stream; charset=utf-8`.

| Proposed category | Phase 5 result | Evidence |
|---|---|---|
| Stream requested | OBSERVED | 10 completion XHR operations. |
| Stream started | PARTIALLY OBSERVED | headers + first LOADING are browser-level evidence; no payload frame. |
| Text generation event | NOT OBSERVED | no event payload captured. |
| Reasoning event | NOT OBSERVED | no event payload captured. |
| Search/source event | NOT OBSERVED | no event payload captured. |
| Tool event | NOT OBSERVED | no event payload captured. |
| Completion event | NOT OBSERVED | only XHR DONE, no application marker. |
| Error/cancel event | NOT OBSERVED | no event payload/abort. |

**Outcome:** PARTIAL_OBSERVATION. The safe observer can establish transport and incremental XHR activity but this export did not include its stream observer’s event metadata. `phase5_stream_observer.js` is provided for a future normal-browser capture.
