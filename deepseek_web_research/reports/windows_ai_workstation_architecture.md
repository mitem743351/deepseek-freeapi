# Windows AI workstation architecture (independent design)

This is an implementation target derived from user-facing capability categories, not a clone of DeepSeek's client or service.

```text
React / TypeScript UI
        ↓ Tauri command/events
Rust application core
 ┌──────┼──────────────┬───────────────┐
 Chat   Context engine  Tools/jobs       Storage
  ↓       ↓               ↓               ↓
Provider manager       Agent policy     SQLite + FTS/vector index
 ├─ local C++/CUDA runtime
 ├─ supported DeepSeek API (user-configured credential)
 └─ other supported providers
```

## Components
- **React + TypeScript:** accessible composer, message renderer, sources, attachment progress, and explicit generation state.
- **Tauri:** signed Windows distribution, native filesystem/credential-store boundary, IPC permissions.
- **Rust core:** cancellation-safe jobs, provider abstraction, context budgeting, exports, schema migrations, telemetry opt-in only.
- **Local inference:** C++/CUDA runtime where model/provider license and GPU capabilities allow; isolate worker process.
- **Storage:** SQLite for conversations, revisions, FTS, citations, preferences; content-addressed attachment vault outside DB.
- **Retrieval:** SQLite FTS plus local vector index; explicit provenance and user-controlled indexing.
- **Python utilities:** optional isolated workers for document/OCR ecosystems; communicate through typed local IPC, never execute untrusted document macros.

## Security
Use Windows Credential Manager for user-provided provider credentials, scoped Tauri capabilities, encrypted attachment vault where chosen, and redacted diagnostics. The application must call only supported provider APIs; it must not automate or proxy a consumer web session.
