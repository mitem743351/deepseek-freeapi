# Conversation state model

## Observed
- No consumer web conversation object, message identifier, parent/branch relation, timestamp field, or persistence operation was captured.

## Inferred (product-neutral only)
A useful desktop conversation needs stable IDs, ordered messages, attachments, generation state, and optional branches. This is an implementation recommendation, not a claim about DeepSeek's schema.

```text
Conversation
├── id, title, created_at, updated_at, provider_profile
├── settings snapshot
├── messages[]
│   ├── id, role, content parts, created_at
│   ├── parent_id? / branch_id?
│   ├── attachments[]
│   └── generation metadata / status
└── attachments[] (content-addressed local records)
```

## Unknown
All web-server ownership boundaries, IDs, message edit/regenerate representation, branch semantics, retention, and export/share representation are **UNKNOWN — NOT OBSERVABLE FROM AUTHORIZED CLIENT BEHAVIOR**.

**Finding:** The official API accepts an ordered `messages` array with system, user, assistant, and tool roles.
**Evidence:** [Official API schema](https://api-docs.deepseek.com/api/create-chat-completion/).
**Confidence:** HIGH for API; UNKNOWN for web persistence.

---

## Phase 2 status — 2026-08-15

No authenticated conversation capture exists. The Phase 1 conceptual desktop model is retained and is **not** promoted to an observed web schema.

| Field/concept | Status | Evidence |
|---|---|---|
| Conversation ID | Unknown | B01–B08 pending. |
| Message ID | Unknown | B02/B03 pending. |
| Parent/branch relation | Unknown | C04/C06 pending. |
| Ordering/timestamps | Unknown | B02–B05 pending. |
| Model/generation metadata | Unknown | C01/D01–D04 pending. |
| Attachments/search sources/tool status | Unknown | E/F scenarios pending. |

**Finding:** No observable consumer-web field can be added without a completed sanitized scenario.
**Evidence:** Phase 2 scenario records are pending.
**Confidence:** HIGH.
