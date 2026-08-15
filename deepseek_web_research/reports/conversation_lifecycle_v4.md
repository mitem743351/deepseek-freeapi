# Conversation lifecycle v4

| Operation family | Raw operation IDs | Observed schema/evidence | Supported lifecycle conclusion |
|---|---|---|---|
| Completion | 0008, 0017, 0037, 0048, 0060, 0072, 0082, 0092, 0100, 0118, 0130 | `parent_message_id`, prompt, mode booleans, file-reference array; SSE content type | Message submission/generation operation OBSERVED. |
| Session create | 0009, 0049, 0073 | Empty object request; response contains one redacted field plus `ttl_seconds` | A session-create operation exists; relationship to completion UNKNOWN. |
| File fetch | 0032, 0034, 0115 | JSON file metadata array | File metadata retrieval OBSERVED. |
| Edit/regenerate/continue/resume/delete/switch/history reload | none identified | `action` was null in all completions; no scenario labels | UNKNOWN. |

**Parentage:** three completion shapes contain `parent_message_id: null`; eight contain `parent_message_id: number`. This supports a **conceptual parent reference** in client-to-service generation requests. It does not establish whether the value identifies a message, a branch, a server record, or a database parent; its values/equality are unavailable.

**Conceptual graph (INFERRED):**
```text
Generation request
├── parent reference: null | number (observed shape)
├── prompt (observed)
├── optional file references (observed shape)
└── streamed response (observed transport)
```
No browser-visible evidence establishes an assistant message object, child identifier, branches, edits, or a full tree.
