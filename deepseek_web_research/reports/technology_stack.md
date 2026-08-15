# Technology stack assessment

| Area | Finding | Evidence | Confidence |
|---|---|---|---|
| Web framework/language/bundler/routing | UNKNOWN — NOT OBSERVABLE FROM AUTHORIZED CLIENT BEHAVIOR | No JS/CSS bundle was publicly captured in this study. | UNKNOWN |
| Component/UI/CSS/Markdown/syntax libraries | UNKNOWN — NOT OBSERVABLE FROM AUTHORIZED CLIENT BEHAVIOR | No bundle/static analysis was performed. | UNKNOWN |
| Web networking client | UNKNOWN for web | No authorized browser network trace. | UNKNOWN |
| API transport | JSON over HTTPS, with optional SSE response | [Official API docs](https://api-docs.deepseek.com/api/create-chat-completion/). | HIGH |
| API stream parser requirement | Must parse SSE `data:` frames and `[DONE]`; should tolerate empty/metadata chunks | Official API docs describe partial deltas and optional usage chunk. | HIGH |
| API models documented today | `deepseek-v4-flash`, `deepseek-v4-pro` | Official API reference enumerates them. | HIGH |
| Service worker, workers, WebSocket/EventSource/fetch streaming | UNKNOWN for web | No DevTools Application/Network observation. | UNKNOWN |
| Analytics/telemetry | UNKNOWN for web | No bundle/network observation. | UNKNOWN |

## Public static-code inspection
No downloadable application bundle was captured, so there are no asserted route strings, flags, schemas, model identifiers from web code, or inferred libraries. This is deliberate: resemblance-based attribution is not evidence.

## Evidence register
- `snapshots/collection_log.md` — exact acquisition limitation.
- [Sign-in page](https://chat.deepseek.com/sign_in) — public login surface observed through ordinary retrieval.
- [Official API reference](https://api-docs.deepseek.com/api/create-chat-completion/) — API-only contract; do not conflate with the browser service.
