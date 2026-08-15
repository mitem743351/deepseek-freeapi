# Completion request analysis

**Evidence:** the 11 raw `POST /api/v0/chat/completion` operations in the Phase 4 capture. Request values were intentionally not retained; this report describes observed field names, types, and shape-level variation only.

| Field | Observed types / counts | Nullability / variation | Feature correlation supported? | Status |
|---|---|---|---|---|
| `<REDACTED_FIELD>` | redacted in all 11 | Unknown | UNKNOWN — redacted by observer | UNKNOWN |
| `parent_message_id` | null: 3; number: 8 | Nullable | Numeric form appears after initial null-form requests, but identity/equality was not captured | OBSERVED field; INFERRED parent relation |
| `model_type` | string length 7: 1; string length 6: 2; null: 8 | Nullable | Null form co-occurs with numeric parent form in this capture; values are unavailable | OBSERVED shape; UNKNOWN model identity |
| `prompt` | string, lengths 2, 10, 12, 18, 19, 23, 30, 35 | Non-null in captured requests | No prompt content retained | OBSERVED |
| `ref_file_ids` | array length 0: 9; array length 1 of string length 41: 2 | Non-null array | The two non-empty arrays temporally follow uploads/fetches; exact ID equality was redacted | OBSERVED/PARTIAL |
| `thinking_enabled` | boolean: 11 | Value not retained | Cannot compare true/false groups | OBSERVED field; UNKNOWN value behavior |
| `search_enabled` | boolean: 11 | Value not retained | Cannot compare true/false groups | OBSERVED field; UNKNOWN value behavior |
| `action` | null: 11 | Null in this capture | No regenerate/edit action value observed | OBSERVED/PARTIAL |
| `preempt` | boolean: 11 | Value not retained | No stop correlation available | OBSERVED field; UNKNOWN behavior |

Completion response observations: all 11 were XHR HTTP 200 with `text/event-stream; charset=utf-8`; each had XHR `LOADING` before `DONE`. Completion elapsed durations ranged from 705 ms to 28,142 ms and LOADING counts ranged from 5 to 445. Those counts demonstrate incremental browser-level progress notifications, not event framing.

Observed safe request-header *names* include `x-ds-pow-response`, `x-hif-leim`, client bundle/platform/version/locale/timezone names, `content-type`, and `accept`. Header values were not captured.
