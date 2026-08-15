# Phase 2 feature-to-network map

| Feature | UI trigger | Client state | Network activity | Response | Persistence | Desktop equivalent |
|---|---|---|---|---|---|---|
| New chat | PENDING B01 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | SQLite conversation service |
| Send/stream | PENDING B02/C01 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Rust provider stream coordinator |
| Attach file | PENDING E01–E08 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | local attachment vault + parser |
| Search | PENDING F01–F04 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | search connector + citation store |
| Share/export | PENDING G01–G03 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | local export / optional share service |

No “observed request” is recorded until a scenario evidence reference exists.
