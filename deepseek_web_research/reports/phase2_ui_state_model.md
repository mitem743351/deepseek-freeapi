# Phase 2 UI state model

No client code or authenticated runtime state has been inspected, so this is an evidence collection model—not a claim about implementation.

```text
IDLE → DRAFTING → SUBMITTING → STREAMING → COMPLETE
                         ├──────────────→ ERROR → RETRYING
                         └──────────────→ STOP_REQUESTED → STOPPED
```

| Concept | Status | Evidence needed |
|---|---|---|
| Draft / selected conversation / attachment selection | UNKNOWN | Normal UI observation + storage inventory. |
| Submitting / streaming / completion | UNKNOWN | B02, C01/C02. |
| Stop/retry/regenerate/edit | UNKNOWN | C03–C06. |
| Search/model/settings state | UNKNOWN | D/F scenarios. |

The labels are proposed comparison vocabulary for the independent desktop application; they are not asserted DeepSeek internal state names.
