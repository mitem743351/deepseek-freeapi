# Search request comparison

`search_enabled` is present as a boolean field in all 11 completion request shapes, and localStorage contains `searchEnabled` plus `searchStateTriggerAppliedVersion` descriptors. The observer did not retain boolean values.

| Comparison question | Result |
|---|---|
| `search_enabled = true` requests count | UNKNOWN — values were not exported. |
| `search_enabled = false` requests count | UNKNOWN — values were not exported. |
| Request-field difference by value | UNKNOWN. |
| Search-specific endpoint | None identified among the 8 distinct raw operation tuples. |
| Search-specific source/citation response metadata | Not captured; completion event frames absent. |
| Search preference persistence | A boolean-shaped `searchEnabled` localStorage descriptor is OBSERVED; value/purpose remains PARTIAL. |

**Finding:** Search capability state is exposed in the request shape and browser preference descriptors, but the search backend protocol remains UNKNOWN.
**Evidence:** Phase 4 capture; no raw values or source event payloads.
**Classification:** PARTIAL.
