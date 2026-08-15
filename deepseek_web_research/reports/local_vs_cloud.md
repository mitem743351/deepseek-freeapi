# Local vs. cloud requirements

| Capability | Local? | Offline? | Model? | Web/external service? | Storage | Notes |
|---|---:|---:|---:|---:|---|---|
| Composer, Markdown, code highlighting | Yes | Yes | No | No | Local | Standard UI functionality. |
| Conversation history/search | Yes | Yes | No | No | SQLite + optional file store | Encrypt at rest where appropriate. |
| Text generation | Yes, with local runtime | Yes | Yes | No | Local model files | Hardware/model license determine feasibility. |
| Hosted generation | Client can run locally | No | Cloud model | Yes | Provider server + local cache | Use supported provider API and user-owned key. |
| File text extraction | Yes | Yes | No | No | Local attachment vault | PDF/DOCX/XLSX handling may need native libraries. |
| Image OCR/vision | Yes with local model | Yes | Yes | No | Local | Quality/compute trade-off. |
| Web search | Partly | No | No | Usually yes | Local cache + provider | Requires a compliant search provider. |
| Citations | Yes after source retrieval | No for live sources | No | Yes for retrieval | Local cache | Preserve URL/time/snippet provenance. |
| Share links/cross-device sync | Client code yes | No | No | Yes | External storage/service | Optional; use end-to-end encryption design. |
| DeepSeek consumer-account behavior | No independent implementation | No | Proprietary backend | Yes | Proprietary | Unknown and out of scope; do not depend on it. |

**Finding:** Local-first architecture can cover UI, persistence, document processing, and optionally generation; fresh search and account sync require external services.
**Evidence:** Capability decomposition above, independent of web implementation.
**Confidence:** HIGH.
