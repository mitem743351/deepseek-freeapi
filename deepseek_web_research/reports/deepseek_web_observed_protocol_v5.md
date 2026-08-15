# DeepSeek Web observed protocol v5

```text
Browser UI [OBSERVED]
 ├─ localStorage and IndexedDB metadata [OBSERVED]
 │    └─ history-message record schema [UNKNOWN]
 ├─ session-create operation [OBSERVED; semantics PARTIAL]
 ├─ admission challenge operation [OBSERVED]
 ├─ generation request [OBSERVED]
 │    └─ XHR text/event-stream [OBSERVED]
 │         ├─ XHR incremental LOADING [OBSERVED]
 │         ├─ SSE payload events [NOT OBSERVED]
 │         ├─ completion event [NOT OBSERVED]
 │         └─ cancellation event [NOT OBSERVED]
 ├─ file upload/reference shape [OBSERVED/PARTIAL]
 ├─ search/thinking boolean field presence [OBSERVED]
 │    └─ values/behavior [UNKNOWN]
 └─ auxiliary event service [OBSERVED route; INFERRED telemetry-like role]
```

The Phase 5 baseline adds scenario-correlated raw operations, but not the required stream-event or IndexedDB-record payload evidence. It therefore strengthens transport/action correlation while retaining the two primary gaps.
