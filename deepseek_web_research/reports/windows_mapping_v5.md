# Windows mapping v5

| Observed web concept | Independent Windows component | Design rule |
|---|---|---|
| session-create operation | `SessionManager` | Local conversation/session lifecycle; never reuse consumer-web session protocol. |
| completion XHR/SSE | Rust `GenerationManager` + `StreamManager` | Provider-supported streaming with typed local events. |
| nullable/numeric parent reference | `MessageTree` | Local opaque parent IDs and revisions; do not assume server branch semantics. |
| file upload/reference array | `AttachmentManager` | Content-hash local vault and local attachment references. |
| thinking/search booleans | `ReasoningMode` / `SearchMode` | Capability flags; do not require hidden reasoning traces. |
| history-message store metadata | `LocalHistoryStore` | SQLite schema owned by desktop app, not copied from unknown IndexedDB records. |
| client settings | `RemoteConfig` / `FeatureConfig` | Explicit local/provider capability contracts. |
| admission challenge | no equivalent web clone | Respect supported provider auth/rate policy; never implement/bypass web admission mechanisms. |
