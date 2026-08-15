# Generation timeline analysis

Times below are capture timestamps. Arrow notation is **TEMPORAL CORRELATION ONLY** unless an operation relationship is directly represented in a request schema.

| Sequence | Observed timeline | Interpretation | Confidence |
|---|---|---|---|
| Initial | 06:22:43.216 completion OP-0008 → 06:22:43.240 session create OP-0009 | Completion and session creation overlap; ordering disproves a simple “session always created before completion” claim. | HIGH timestamp / UNKNOWN semantics |
| Follow-up | 06:22:53.483 PoW OP-0014 → 06:22:53.936 completion OP-0017 | 453 ms request-start separation. | HIGH temporal only |
| PNG attachment | 06:23:07.656 file selected → 06:23:07.672 upload OP-0023 → 06:23:07.679 PoW OP-0024 → 06:23:08.130 PoW OP-0028 → 06:23:10.283 fetch OP-0032 → 06:23:13.536 fetch OP-0034 → 06:23:15.953 completion OP-0037 (one file-ref shape) | Strong temporal attachment sequence; redaction prevents proving upload ID equals completion ref. | OBSERVED/PARTIAL |
| Later generation | 06:23:25.977 PoW OP-0043 → 06:23:31.312 completion OP-0048 → 06:23:31.325 session create OP-0049 | Again completion begins before the observed create call finishes/starts. | HIGH timestamp / UNKNOWN semantics |
| JSON attachment | 06:25:01.777 selection → 06:25:01.786 upload OP-0106 → 06:25:01.792 PoW OP-0107 → 06:25:02.396 PoW OP-0111 → 06:25:03.613 fetch OP-0115 → 06:25:05.766 completion OP-0118 (one file-ref shape) | Strong temporal sequence; no raw ID equality. | OBSERVED/PARTIAL |
| Long generation | 06:25:19.112 PoW OP-0125 → 06:25:22.566 completion OP-0130 → duration 28,142 ms; 445 LOADING entries | Incremental XHR progress for a long response. | OBSERVED |

The capture contains no explicit scenario markers, UI events, completion event frames, stop action, regenerate action, or post-completion persistence operation. It therefore cannot establish generation termination semantics beyond XHR `DONE`.
