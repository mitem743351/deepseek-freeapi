# Independent reimplementation matrix

| User-visible capability | Technical components necessary | Independent implementation? | Local strategy | External services/model capability |
|---|---|---|---|---|
| Chat composer + Markdown/code display | React UI, renderer, syntax highlighter | Yes | React/TypeScript + local preferences | None |
| Streaming answer | Async provider adapter, delta reducer, cancellation | Yes | Rust async event bridge | Local model or supported cloud model |
| Conversation history | Schema/migrations/full-text search | Yes | SQLite + FTS5 | None |
| Regenerate/edit/branches | Message graph + immutable revision records | Yes | SQLite transaction model | Model for new generation |
| Reasoning UI | Capability flags + separate status/content channels | Yes | Provider-agnostic events | A provider/model that exposes suitable metadata; exact traces optional |
| Documents | Attachment vault, extractors, chunk/context engine | Yes | Windows files + Rust/Python worker | Optional local OCR/vision/model |
| Images | Preview + vision/OCR provider | Yes | Local image pipeline | Vision-capable local/cloud model |
| Search + citations | Search connector, fetch policy, provenance store | Yes | SQLite citation records | Compliant search/retrieval service |
| Share/export | Markdown/JSON/PDF exporter | Yes | Local export | Optional backend for share links |
| Exact DeepSeek web behavior/protocol | Proprietary service and private implementation | No / out of scope | Implement independent UX contracts | Not applicable |

**Finding:** Comparable user-facing categories can be built independently without copying DeepSeek code or private service protocol.
**Evidence:** Each row maps to standard local software components and optional supported model/search providers.
**Confidence:** HIGH.
