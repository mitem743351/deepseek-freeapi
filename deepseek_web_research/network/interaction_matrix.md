# Interaction matrix

No action below was executed in an authenticated browser session. Accordingly, an endpoint is never invented from an API analogue. “Not observed” is a result, not a missing value to guess.

| User action | Frontend event | Network operation | Request type | Response type | Streaming | UI state change |
|---|---|---|---|---|---|---|
| Login | Not observed | UNKNOWN — NOT OBSERVABLE FROM AUTHORIZED CLIENT BEHAVIOR | Unknown | Unknown | Unknown | Unknown |
| New chat | Not observed | Unknown | Unknown | Unknown | Unknown | Unknown |
| Send message | Not observed | Unknown for web; API analogue is documented separately | Unknown | Unknown | Unknown for web |
| Receive response | Not observed | Unknown for web | Unknown | Unknown | Unknown |
| Stop generation | Not observed | Unknown | Unknown | Unknown | Unknown | Unknown |
| Regenerate | Not observed | Unknown | Unknown | Unknown | Unknown | Unknown |
| Edit message | Not observed | Unknown | Unknown | Unknown | Unknown | Unknown |
| Delete/rename chat | Not observed | Unknown | Unknown | Unknown | N/A | Unknown |
| Upload file | Not observed | Unknown | Unknown | Unknown | Unknown | Unknown |
| Search/research | Not observed | Unknown | Unknown | Unknown | Unknown | Unknown |
| Change model/settings | Not observed | Unknown | Unknown | Unknown | N/A | Unknown |
| Share/export | Not observed | Unknown | Unknown | Unknown | N/A | Unknown |

## API-only reference (not a web trace)
**Finding:** `POST https://api.deepseek.com/chat/completions` accepts JSON `messages` and `model`; `stream: true` yields SSE partial deltas.
**Evidence:** [Official API documentation](https://api-docs.deepseek.com/api/create-chat-completion/).
**Confidence:** HIGH for API, UNKNOWN for web.
