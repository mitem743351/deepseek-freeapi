# Endpoint inventory — authenticated web evidence

No authenticated endpoint has been observed in repository evidence. Do not populate an endpoint from API documentation or guesses. Add rows only after a matching completed scenario names a sanitized evidence reference.

| ID | Method | Host | Path | Content Type | Purpose | Auth Required | Streaming | Evidence |
|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | No observed web endpoint | UNKNOWN | UNKNOWN | `reports/phase2_initial_gap_map.md` |

**Finding:** The inventory is empty rather than speculative.
**Evidence:** No Phase 2 authenticated scenario is complete.
**Confidence:** HIGH.

## Phase 3 status
No entry was added because no authenticated normal-browser request was captured. The indicated session material was intentionally not replayed or inspected. See `docs/phase3_execution_status.md`.

---

## Phase 4 supersession
A sanitized authenticated capture now exists. The authoritative Phase 4 raw-operation inventory is `network/endpoint_inventory_v4.md`. The prior empty inventory remains as historical Phase 2 status, not the current evidence state.
