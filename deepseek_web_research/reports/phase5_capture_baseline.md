# Phase 5 capture baseline

**Primary baseline evidence:** `deepseek_web_research/captures/deepseek_observation_2026-08-15T06-42-36-498Z.json`, parsed in full before this report. It supersedes older captures only where it directly observes newer facts.

| Measure | Result |
|---|---:|
| Distinct raw method/origin/path tuples | 7 |
| Raw operations | 152, all XHR |
| Completion calls | 10 `POST /api/v0/chat/completion` |
| Session-create calls | 4 `POST /api/v0/chat_session/create` |
| Admission challenge calls | 11 `POST /api/v0/chat/create_pow_challenge` |
| File operations | 1 multipart upload; no `fetch_files` operation in this capture |
| Explicit scenarios | 5, all label `B02_SEND_MESSAGE` |
| Streaming candidates / SSE responses | 10 / 10 |
| `stream_observations` records | 0 |
| IndexedDB record samples | 0; schema metadata only |
| Attachment observations | 1, PNG, 17,177 bytes, filename redacted |

## Current evidence gaps
- Actual SSE payload/frame schema, event names, terminal marker, and stream error/cancel event remain unobserved.
- Although five scenario markers exist, all share the same label; they do not safely identify S1–S5 or settings values.
- Boolean values for thinking/search and `preempt` were not retained.
- `history-message` record keys/fields/contents were not sampled.
- No visible Stop/cancellation-specific operation is identified.

The earlier Phase 4 capture had 11 completion calls and two file uploads; this baseline has 10 completion calls and one upload. These are separate observation windows, not a contradiction about product capability.
