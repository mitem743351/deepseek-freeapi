# Phase 2 message lifecycle

## Observed lifecycle
No authenticated web message lifecycle has been observed. B02/B03 and C01–C06 are pending.

## Evidence-driven lifecycle template
```text
Draft input [unknown client persistence]
  → submit [unknown]
  → request creation [unknown]
  → initial server response [unknown]
  → streamed/incremental delivery [unknown]
  → incremental UI rendering [unknown]
  → completion/error/stop [unknown]
  → conversation persistence [unknown]
```

| Transition | Current classification | Required evidence |
|---|---|---|
| Draft editing | UNKNOWN | DevTools storage/UI observation without content capture. |
| Submit | UNKNOWN | B02 structural network trace. |
| Server processing / message creation | UNKNOWN | B02 + response sequence. |
| Incremental rendering | UNKNOWN | C01/C02 timing and visible UI notes. |
| Stop / regenerate / edit | UNKNOWN | C03/C04/C06. |
| Persistent conversation update | UNKNOWN | B04/B05 plus storage inventory. |

**Finding:** Phase 1’s API message array cannot establish the consumer web lifecycle.
**Evidence:** It is separately documented API behavior rather than a web trace.
**Confidence:** HIGH.
