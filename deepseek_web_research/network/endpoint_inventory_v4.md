# Endpoint inventory v4 — raw-operation basis

Primary evidence is the Phase 4 capture. Counts below use the 143 raw operations, not the observer’s lifecycle-inflated endpoint-inventory counter.

| ID | Method / host / path | Raw count | Content type | Request schema | Response schema | Streaming | Likely role | Confidence |
|---|---|---:|---|---|---|---|---|---|
| EP-001 | POST `gator.volces.com/list` | 107 | JSON charset | event/user/header envelope | object `Type,e,message,sc,server_time,tc` | No | auxiliary event service | OBSERVED route/schema; purpose INFERRED |
| EP-002 | GET `chat.deepseek.com/api/v0/client/settings` | 3 | JSON | none | code/msg/data/settings wrapper | No | client settings retrieval | OBSERVED |
| EP-003 | GET `hif-leim.deepseek.com/query` | 1 | JSON | none | code/msg/data/value wrapper | No | unknown auxiliary operation | OBSERVED route; UNKNOWN role |
| EP-004 | POST `chat.deepseek.com/api/v0/chat/completion` | 11 | `text/event-stream; charset=utf-8` | completion object (see report) | not captured | Yes, XHR LOADING | chat generation operation | OBSERVED/PARTIAL |
| EP-005 | POST `chat.deepseek.com/api/v0/chat_session/create` | 3 | JSON | empty object | wrapper, redacted field, ttl_seconds | No | session-create operation | OBSERVED/PARTIAL |
| EP-006 | POST `chat.deepseek.com/api/v0/chat/create_pow_challenge` | 13 | JSON | target_path string | challenge wrapper | No | admission-challenge operation | OBSERVED |
| EP-007 | POST `chat.deepseek.com/api/v0/file/upload_file` | 2 | JSON | multipart field `file` | file metadata wrapper | No | file upload operation | OBSERVED |
| EP-008 | GET `chat.deepseek.com/api/v0/file/fetch_files` | 3 | JSON | none | files metadata wrapper | No | file metadata retrieval | OBSERVED |

These are **observed web service requests**, not a claim that they are public/developer APIs.
