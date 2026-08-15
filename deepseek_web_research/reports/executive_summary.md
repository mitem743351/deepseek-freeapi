# Executive summary

## Scope and evidence status
This is a safety-bounded architecture study of DeepSeek's **web product**, dated 2026-08-15 UTC. It uses public pages and official public API documentation; it does not inspect an authenticated session, replay requests, collect cookies, or bypass any control. The public root redirected the retrieval client to sign-in, so no production JavaScript/CSS asset inventory or DevTools trace was available. `snapshots/collection_log.md` and `snapshots/resource_manifest.json` are the complete reproducible snapshot record.

**Finding:** DeepSeek publicly operates a browser chat product at `chat.deepseek.com`, and separately documents an API chat-completion product at `api.deepseek.com`.
**Evidence:** Public sign-in page and [official Chat Completions documentation](https://api-docs.deepseek.com/api/create-chat-completion/).
**Confidence:** HIGH.

**Finding:** The API streaming contract is data-only Server-Sent Events (SSE), ending in `data: [DONE]`. This does not establish that the consumer web app uses the identical endpoint or framing.
**Evidence:** Official API documentation explicitly states this behavior.
**Confidence:** HIGH for API; UNKNOWN for web app.

**Finding:** Public DeepSeek material describes web/app file upload and web-search prompting, but the web UI's current feature gates and protocol were not observed.
**Evidence:** [official DeepSeek-R1 repository](https://github.com/deepseek-ai/DeepSeek-R1) describes dedicated prompts for file upload and web search.
**Confidence:** MEDIUM for feature existence in the cited release context; UNKNOWN for current web behavior.

## Decision for an independent Windows product
Build an independent, provider-neutral workstation rather than depending on the web product: Tauri (Rust) + React, SQLite-backed conversation data, a streaming provider adapter, local document extraction, and a pluggable search connector. This reproduces user-facing categories without copying web code, protocols, branding, private APIs, or proprietary backend behavior. Details: `implementation_recommendations.md`, `gap_analysis.md`, and `local_vs_cloud.md`.

## Important unknowns
Current web frontend stack/bundles, routes, account/session schema, storage keys, conversation IDs, upload endpoints, stop/regenerate/edit semantics, sharing/export details, telemetry, and web-chat stream event schema are **UNKNOWN — NOT OBSERVABLE FROM AUTHORIZED CLIENT BEHAVIOR in this study**. The companion capture plan states exactly how an authorized human can fill those gaps.
