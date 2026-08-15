# Endpoint inventory v5

Counts use 152 raw operations in the Phase 5 baseline—not derived lifecycle states.

| Method / origin / path | Count | Scenarios | Request / response | Streaming | Role | Confidence |
|---|---:|---|---|---|---|---|
| POST `gator.volces.com/list` | 118 | 001–005 | event envelope / JSON status object | No | auxiliary event service | OBSERVED route; purpose INFERRED |
| GET `hif-dliq.deepseek.com/query` | 5 | 003, 005 | no schema retained / unknown | Unknown | unknown query operation | OBSERVED route; UNKNOWN role |
| POST `chat.deepseek.com/api/v0/chat/completion` | 10 | 001–005 | completion shape / no frame schema | XHR SSE | generation | OBSERVED/PARTIAL |
| POST `chat.deepseek.com/api/v0/chat_session/create` | 4 | 001, 004, 005 | empty object / wrapper + ttl | No | session creation | OBSERVED/PARTIAL |
| POST `chat.deepseek.com/api/v0/chat/create_pow_challenge` | 11 | 001, 002, 004, 005 | target_path string / challenge wrapper | No | admission challenge | OBSERVED |
| POST `chat.deepseek.com/api/v0/file/upload_file` | 1 | 005 | multipart `file` / file metadata | No | file upload | OBSERVED |
| GET `chat.deepseek.com/api/v0/client/settings` | 3 | unmarked | none / settings wrapper | No | settings retrieval | OBSERVED |
