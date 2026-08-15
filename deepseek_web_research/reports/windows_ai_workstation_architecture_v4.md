# Windows AI workstation architecture v4

| Observed web capability | Independent desktop component | Implementation boundary |
|---|---|---|
| Session-create operation | `SessionManager` | Rust local/session lifecycle; no DeepSeek-web session reuse |
| Completion request + incremental XHR/SSE | `GenerationManager` + `StreamManager` | Rust async provider adapter and typed event reducer |
| Nullable parent reference | `MessageTree` | SQLite message/revision graph; parent ID is a local opaque ID |
| File metadata/reference array | `AttachmentManager` | content-hash vault, parser jobs, local attachment IDs |
| thinking/search controls | `ReasoningMode` / `SearchMode` | React controls + provider capability abstraction |
| local history store | `LocalConversationStore` | SQLite + FTS; do not copy IndexedDB schema |
| remote settings | `LocalSettings` + optional provider capability config | React/Rust settings contract |
| admission layer | none to clone | Use supported provider authentication/rate limits; never reproduce/bypass web PoW |

## Recommended split
- **Rust:** provider/network adapter, cancellation, stream parsing, SQLite/migrations, attachment jobs, secure secret-store bridge, indexing.
- **React/TypeScript:** composer, message tree UI, file selection/progress, search/citation panels, reasoning/model controls, state visualization.
- **Local inference:** optional C++/CUDA/llama-style runtime behind the same provider interface.
- **External services:** hosted model inference, live search, optional sync/share and cloud OCR/vision.
- **Entirely local:** UI, history, FTS/vector index, exports, document extraction where local libraries support the format, and local model inference where hardware permits.
