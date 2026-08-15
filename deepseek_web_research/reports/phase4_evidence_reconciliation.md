# Phase 4 evidence reconciliation

The sanitized Phase 4 capture is primary evidence for runtime claims. Phase 1–3 correctly marked authenticated runtime behavior unknown; those reports are superseded only where the capture directly observes a fact.

| Finding | Previous repository state | New attached evidence | Final status |
|---|---|---|---|
| Consumer chat completion operation | UNKNOWN | 11 XHR POSTs to `https://chat.deepseek.com/api/v0/chat/completion` | OBSERVED |
| Generation transport | UNKNOWN for web | HTTP 200, `text/event-stream; charset=utf-8`, repeated XHR `LOADING` states | OBSERVED transport; event schema UNKNOWN |
| Session creation | UNKNOWN | 3 XHR POSTs to `/api/v0/chat_session/create`, JSON response shape | OBSERVED operation; semantics PARTIAL |
| Admission challenge | UNKNOWN | 13 XHR POSTs to `/api/v0/chat/create_pow_challenge`; completion header name `x-ds-pow-response` observed | OBSERVED admission layer; enforcement UNKNOWN |
| File subsystem | UNKNOWN | 2 multipart `upload_file` calls; 3 `fetch_files` calls; completion file-reference array type | OBSERVED/PARTIAL |
| Browser storage | UNKNOWN | localStorage descriptors, 2 IndexedDB DBs, `deepseek-chat/history-message` store | OBSERVED/PARTIAL |
| Message parent relation | UNKNOWN | completion request field `parent_message_id`: null in 3, number in 8 | OBSERVED field; tree semantics INFERRED |
| Search/thinking values | UNKNOWN | Boolean fields and local preference keys observed, but values not retained | PARTIAL |
| Telemetry distinction | UNKNOWN | 107 XHR POSTs to `gator.volces.com/list` with event-envelope shape | OBSERVED auxiliary service; purpose PARTIAL |

**Discrepancy:** earlier reports stated no authenticated evidence existed. That was accurate at the time; it is now obsolete for the rows above. No Phase 4 capture supports an SSE payload schema, stop behavior, response event names, conversation-record schema, or hidden backend implementation.
