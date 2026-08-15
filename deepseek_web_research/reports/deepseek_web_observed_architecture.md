# DeepSeek web observed architecture — Phase 2 status

```text
Browser UI [OBSERVED: public sign-in surface]
 ├─ local storage / service worker / caches [UNKNOWN]
 ├─ UI state / client networking implementation [UNKNOWN]
 └─ normal browser requests [UNKNOWN: authenticated trace absent]
          ↓
Observed web-service boundary [INFERRED: browser service exists]
 ├─ account/sign-in [OBSERVED UI; protocol UNKNOWN]
 ├─ conversation operations [UNKNOWN]
 ├─ generation / streaming [UNKNOWN for web]
 ├─ attachments [UNKNOWN]
 ├─ search [UNKNOWN]
 └─ share/export/settings [UNKNOWN]

Separate documented developer API [OBSERVED DOCUMENTATION]
 └─ HTTPS JSON chat completion; optional SSE response
```

**Finding:** This diagram is intentionally sparse because no authenticated web runtime evidence is present.
**Evidence:** `reports/phase2_initial_gap_map.md`, pending scenario records.
**Confidence:** HIGH.
