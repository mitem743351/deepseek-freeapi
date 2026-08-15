# Gap analysis: independent Windows workstation

| Observed/claimed web capability | Independent desktop feature | Classification | Notes |
|---|---|---|---|
| Browser chat product (observed public surface) | Native chat composer/history | Easy | Local React UI + SQLite. |
| API-style streaming (official API) | Provider streaming adapter | Moderate; requires cloud model | SSE parser, cancellation, retries, backpressure. |
| Account-synced web history | Local-first encrypted SQLite history | Moderate | Different feature; optional opt-in sync service. |
| File-upload prompt context (official repo context) | Local extraction, chunking, attachment store | Moderate | PDF/DOCX/XLSX parsers, OCR are separate dependencies. |
| Web search prompt context (official repo context) | Search-provider abstraction | Requires third-party service | Respect provider terms, citations, cache policy. |
| Thinking controls (official API) | Provider capability controls | Moderate; requires cloud/local model | Do not presume all providers expose reasoning traces. |
| Web sharing/export | Markdown/JSON/PDF export | Easy | Offline export; signed sharing link requires a service. |
| Proprietary web account/service behavior | Exact behavioral compatibility | Not reproducible independently | Do not clone private protocol or backend. |

**Finding:** A functionally comparable desktop workflow can be independently implemented without reproducing web internals.
**Evidence:** Proposed components use standard local storage, document parsers, provider SDK/HTTP adapters, and explicit user configuration.
**Confidence:** HIGH.
