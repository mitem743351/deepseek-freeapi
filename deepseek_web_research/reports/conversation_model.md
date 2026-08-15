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
