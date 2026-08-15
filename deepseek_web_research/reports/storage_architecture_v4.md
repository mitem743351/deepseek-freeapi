# Storage architecture v4

| Category | Observed descriptors | Assessment |
|---|---|---|
| UI preference | `__appKit_@deepseek/chat_themePreference`, locale preference, banner settings | OBSERVED key/schema; UI purpose strongly suggested by names. |
| Search/reasoning feature state | `searchEnabled`, `searchStateTriggerAppliedVersion`, `thinkingEnabled` | OBSERVED boolean/value-wrapper shapes; exact behavior/value unknown. |
| Feature/config | `__ds_remote_feature_store_model`, `client/settings` operation, refresh prompt/config keys | OBSERVED storage/operation; semantic mapping partial. |
| Conversation/history | `deepseek-chat/history-message`; redacted conversation-like local key | OBSERVED store/key category; records unknown. |
| Telemetry/diagnostics | `applog_sdk_event_store_20006317`, `APMPLUS__cache__server__config__675113`, `__tea_cache_first_20006317` | OBSERVED; exact product role partial. |
| Authentication-related | Several `auth-related-key` entries and redacted sessionStorage | Authentication-related value present — REDACTED. Mechanism/schema beyond that is unknown. |
| Service worker/cache | Empty cache list and no registrations at inspection | OBSERVED at that instant; not a general absence claim. |

The observer’s own redactor replaces sensitive key names with `auth-related-key`; that label is not an original key name.
