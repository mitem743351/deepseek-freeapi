# Phase 4 final protocol assessment

**Primary evidence:** the complete sanitized observer export at `captures/deepseek_observation_2026-08-15T06-26-16-686Z.json`. Phase 4 supersedes earlier “no authenticated capture” statements only for direct observations described below.

## Core answers
1. **Observed chat completion endpoint:** XHR `POST https://chat.deepseek.com/api/v0/chat/completion`, 11 raw observations.
2. **Established request fields:** redacted field, `parent_message_id`, `model_type`, `prompt`, `ref_file_ids`, `thinking_enabled`, `search_enabled`, `action`, and `preempt`; see `completion_request_analysis.md`.
3. **Generation transport:** HTTP `text/event-stream; charset=utf-8` on XHR with repeated LOADING states.
4. **Stream unknowns:** payload/event schema, event names, delta format, terminal marker, heartbeat/error and cancellation signal were not exported.
5. **Sessions:** `POST /api/v0/chat_session/create` observed three times with empty object request and wrapper response. Exact relationship to completion is unknown.
6. **Files:** multipart `POST /api/v0/file/upload_file` with field `file`, then `GET /api/v0/file/fetch_files` metadata calls were observed.
7. **File references:** two later completion shapes contained a one-string `ref_file_ids` array. Equality to uploaded IDs is not proven.
8. **Parentage:** nullable/number `parent_message_id` was observed. It supports a parent-reference concept, not a complete branch model.
9. **Reasoning:** thinking field/key/header presence observed; values/event differences unknown.
10. **Search:** search field/key presence observed; values, sources, citations, and backend workflow unknown.
11. **Browser storage:** local preference/config/auth-redacted descriptors, two IndexedDB databases, and `deepseek-chat/history-message` store observed.
12. **IndexedDB history:** store metadata only; records and record schema unknown.
13. **Auxiliary services:** gator event-envelope route observed; telemetry-like purpose inferred. One hif-leim query operation has unknown purpose.
14. **Remaining unknown:** exact SSE frames, stop/regenerate/edit, message IDs/assistant records, session semantics, server persistence, file processing, search execution, model identities, backend/model internals.

## Engineering answers
15. **Independent client components:** React UI, Rust session/generation/stream managers, message tree, attachment manager, local conversation store, settings/capabilities, optional search connector.
16. **Rust:** async streaming/cancellation, provider adapters, SQLite/migrations, file parsing jobs, secure key bridge, retrieval.
17. **TypeScript/React:** composer, message tree rendering, stream state UI, settings/model/reasoning/search controls, attachment interaction.
18. **Local inference:** optional local model runtime for generation/vision/embeddings; not required for UI/history.
19. **External services:** hosted model, current web search, optional sync/share/cloud OCR.
20. **Entirely local:** UI, SQLite history, FTS/vector storage, exports, attachment vault/extraction where supported, and local inference on capable hardware.

## Confidence table

| Component | Evidence Status | Confidence | Remaining Gap |
|---|---|---|---|
| `/chat/completion` | OBSERVED | HIGH | response event schema |
| SSE transport | OBSERVED | HIGH | event payload structure |
| Session creation | OBSERVED | HIGH | exact session semantics |
| PoW challenge | OBSERVED | HIGH | server-side enforcement |
| File upload | OBSERVED | HIGH | processing internals |
| File references | OBSERVED/PARTIAL | MEDIUM | ID equality/full lifecycle |
| Parent messages | OBSERVED/PARTIAL | MEDIUM | complete branch semantics |
| Search | PARTIAL | MEDIUM | values/backend workflow/citations |
| Thinking | PARTIAL | MEDIUM | values/event-level behavior |
| IndexedDB history | PARTIAL | HIGH | record schema |
| Telemetry | OBSERVED/PARTIAL | MEDIUM | exact purpose |
| Backend model | UNKNOWN | — | not directly observable |
