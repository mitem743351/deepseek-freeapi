# Network-to-IndexedDB mapping v5

Completion requests have a nullable/numeric `parent_message_id` request shape and browser storage exposes `deepseek-chat/history-message`. The Phase 5 capture provides no record samples, no matching IDs, and no post-completion IndexedDB timing observation.

```text
network completion → history-message store
```

is therefore **INFERRED as a possible local-history relationship**, not observed equivalence. The authoritative/replica/cache role of IndexedDB remains UNKNOWN.
