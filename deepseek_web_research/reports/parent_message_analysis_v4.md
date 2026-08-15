# Parent-message field analysis v4

The observer retained type/length schemas, not IDs. “number” below means an observed numeric field type, not a retained identifier.

| Operation | parent_message_id | Prompt length | File refs | Thinking | Search | Time |
|---|---|---:|---:|---|---|---|
| OP-0008 | null | 2 | 0 | boolean value not captured | boolean value not captured | 06:22:43.216Z |
| OP-0017 | number | 35 | 0 | not captured | not captured | 06:22:53.936Z |
| OP-0037 | number | 18 | 1 | not captured | not captured | 06:23:15.953Z |
| OP-0048 | null | 2 | 0 | not captured | not captured | 06:23:31.312Z |
| OP-0060 | number | 30 | 0 | not captured | not captured | 06:23:41.619Z |
| OP-0072 | null | 2 | 0 | not captured | not captured | 06:24:22.822Z |
| OP-0082 | number | 19 | 0 | not captured | not captured | 06:24:28.656Z |
| OP-0092 | number | 35 | 0 | not captured | not captured | 06:24:38.631Z |
| OP-0100 | number | 10 | 0 | not captured | not captured | 06:24:51.497Z |
| OP-0118 | number | 23 | 1 | not captured | not captured | 06:25:05.766Z |
| OP-0130 | number | 12 | 0 | not captured | not captured | 06:25:22.566Z |

**Finding:** Null and numeric parent-reference forms are both observed, and numeric-form requests occur after null-form requests in the time series.
**Classification:** OBSERVED temporal/type pattern.

**Finding:** This supports—but does not prove—a message-tree/parent-child architecture. The export cannot test equality, changes, repeated same-parent regeneration, branches, or whether the number is a message ID.
**Classification:** INFERRED; remaining semantics UNKNOWN.
