# Web-to-Windows mapping

| Observed Web capability | Evidence | Independent Windows design |
|---|---|---|
| Public browser sign-in surface | Phase 1 public retrieval | Desktop onboarding + provider configuration; do not reuse web authentication. |
| API-style streamed completion (developer API only) | Official API docs, not web trace | Rust async provider stream + explicit cancellation reducer. |
| Web conversation persistence | Not observed | SQLite conversation/message revision store. |
| Web attachments | Not observed | local attachment manager, content-hash vault, parser jobs. |
| Web search | Not observed | search-provider abstraction + citation provenance. |
| Web generation state | Not observed | typed Rust event/state machine bridged to React. |

**Finding:** No authenticated web capability can be mapped as observed in Phase 3.
**Evidence:** `docs/phase3_execution_status.md`.
**Confidence:** HIGH.
