# Architecture Decision Records

ADRs capture consequential decisions before implementation locks them in.

| ADR | Status | Decision |
| --- | --- | --- |
| [0001](0001-tauri-react-rust-core.md) | Proposed | Tauri 2 + React with a framework-neutral Rust core |
| [0002](0002-preserve-deepseek-python-sidecar.md) | Proposed | Preserve current DeepSeek protocol in an isolated Python sidecar |
| [0003](0003-normalized-provider-events.md) | Proposed | Versioned normalized provider events |
| [0004](0004-sqlite-message-graph-and-fts.md) | Proposed | SQLite message graph, structured parts, and FTS5 |
| [0005](0005-os-keyring-credentials.md) | Proposed | OS secure storage for provider credentials |

## Lifecycle

```text
Proposed -> Accepted -> Superseded
                    \-> Rejected
```

Accepted ADRs are immutable. A later decision supersedes an ADR by adding a new record and linking both documents.
