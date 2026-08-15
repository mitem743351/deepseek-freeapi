# IndexedDB history analysis

**Finding:** IndexedDB database `deepseek-chat`, version 1, contains store `history-message`. The store has `keyPath: null`, `autoIncrement: false`, and no reported indexes.
**Evidence:** Phase 4 storage schema.
**Classification:** OBSERVED.

The export intentionally reports `approximate_record_count: NOT_READ` and no record values/field names. Therefore the history-message record schema, count, contents, relation to server messages, and whether it is cache versus authoritative history are **UNKNOWN**.

`devtools_observer/phase4_indexeddb_observer.js` provides a bounded, read-only future/manual inspection path: it records store metadata, count, and sanitized field names/types from at most 25 records, without exporting record values or writing/deleting anything.
