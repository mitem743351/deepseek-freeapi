# Independent Windows application recommendations

## Proposed architecture
```text
React desktop UI (Tauri WebView)
  └─ Rust application core
      ├─ Conversation engine (SQLite, migrations, branch graph)
      ├─ Context engine (attachments, extraction, retrieval budget)
      ├─ Provider layer (local / supported cloud providers)
      ├─ Stream coordinator (SSE, cancellation, retry policy)
      ├─ Search connector (explicit provider + citation provenance)
      └─ Rust job manager (parse/OCR/index/export)
```

| Web capability category | Independent desktop equivalent |
|---|---|
| Streaming response | Rust async stream coordinator; provider-specific adapter |
| Conversation history | SQLite + full-text index + encrypted attachment vault |
| File analysis | Local document pipeline (Tika-like extraction alternatives, OCR, chunker) |
| Search/research | Search-provider abstraction with cited result records |
| Model switching | Provider manager with capability discovery |
| UI state | React reducer/query cache; persisted preferences separated from data |
| Background work | Rust job manager with cancellation/progress events |
| Sharing/export | Local Markdown/JSON/PDF export; optional separately designed sync service |

## Engineering controls
- Never embed cloud-provider credentials in shipped binaries. Use Windows Credential Manager or an encrypted local secret store.
- Store attachments by content hash and retain original MIME/name separately; scan and size-limit before parsing.
- Make generation cancellation local and provider-aware; never emulate unknown proprietary endpoints.
- Version local schemas, events, and exports. Keep an audit-free/redacted diagnostics mode by default.
- Treat provider capabilities as negotiated metadata, not hard-coded assumptions.

**Finding:** Tauri/Rust + React is a reasonable Windows implementation choice, not an observation about DeepSeek.
**Evidence:** It supports a native shell, async I/O, secure local integrations, and a mature UI ecosystem.
**Confidence:** MEDIUM (technology recommendation).
