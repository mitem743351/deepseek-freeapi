# Phase 4 capture statistics

**Primary evidence:** `deepseek_web_research/captures/deepseek_observation_2026-08-15T06-26-16-686Z.json` (observer export timestamp `2026-08-15T06:26:16.635Z`). The entire JSON document was parsed programmatically before this report was written.

| Measure | Count | Notes |
|---|---:|---|
| Export endpoint-inventory rows | 8 | Normalized method/origin/path entries. |
| Unique method/origin/path tuples in raw operations | 8 | Matches the inventory row count. |
| Raw operations | 143 | All have transport `xhr`. |
| Actual `text/event-stream` operations | 11 | All are `POST /api/v0/chat/completion`. |
| Streaming candidates | 11 | Same 11 completion operations. |
| Captured stream-event objects | 0 | No raw SSE frame/event payloads were exported. |
| Attachment observations | 2 | One PNG (17,177 bytes), one JSON (98,997 bytes); names redacted. |
| Message/conversation candidate entries | 1,476 | **Not 1,476 independent requests**: observer lifecycle updates duplicated candidate records. |
| Candidate classifications | 991 observed / 485 possible | Derived observer heuristic; raw operation count is authoritative for requests. |
| Explicit scenario records | 0 | No `mark()`/`endScenario()` labels were used. |
| localStorage entry descriptors | 34 | Values are schema-only or redacted. |
| IndexedDB databases / stores | 2 / 3 | `deepseek-chat/history-message` is one store. |
| Cache Storage caches / Service Worker registrations | 0 / 0 | At inspection time. |

## Important measurement correction
**Finding:** `endpoint_inventory.observed_count` (for example, 975 for completion) is not a network-request count.
**Evidence:** The export contains only 11 raw completion operations; the observer updates inventory on lifecycle/status updates, inflating its counter.
**Classification:** OBSERVED observer-export behavior.
**Confidence:** HIGH.
