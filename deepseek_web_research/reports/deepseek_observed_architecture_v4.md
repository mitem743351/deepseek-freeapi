# DeepSeek observed architecture v4

```text
Browser UI [OBSERVED product surface]
 ├─ localStorage [OBSERVED: preferences, feature-state descriptors, redacted auth-related values]
 ├─ IndexedDB [OBSERVED: deepseek-chat/history-message schema metadata]
 ├─ client settings request [OBSERVED]
 ├─ session-create operation [OBSERVED; semantics PARTIAL]
 ├─ admission challenge [OBSERVED]
 ├─ file subsystem [OBSERVED]
 │    ├─ multipart upload_file
 │    └─ fetch_files metadata
 ├─ completion operation [OBSERVED]
 │    └─ XHR text/event-stream + LOADING progress [OBSERVED]
 │       └─ payload event schema [UNKNOWN]
 ├─ search/reasoning request fields + preferences [OBSERVED]
 │    └─ true/false behavior and backend workflow [UNKNOWN]
 └─ auxiliary event service [OBSERVED route; purpose INFERRED]

Server internals / model implementation / persistence authority [UNKNOWN]
```

The diagram describes externally observable browser operations, never proprietary server components.
