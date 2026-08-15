# Final web architecture assessment — Phase 2 evidence status

## A. How does the DeepSeek web client appear to work?
It appears to be a browser-delivered chat product with a public sign-in surface. Its authenticated runtime behavior has not been captured here. A separately documented developer API supports JSON chat completions and optional SSE; that is not evidence that the web client uses the same contract.

## B. What is directly observed?
A public sign-in surface, public `robots.txt`, and official developer API documentation. The repository contains no authenticated HAR, storage inventory, client bundle, or user-action trace.

## C. What is inferred?
A browser UI necessarily renders interaction state and communicates with a service; model inference is service-backed in the hosted product. These are high-level product inferences only. Proposed desktop modules are engineering recommendations.

## D. What remains unknown?
All authenticated routes, methods, payloads, identifiers, web stream protocol, cancellation behavior, persistence schema, storage mechanisms, attachment/search protocols, sharing, telemetry, and client/server operation ownership. See `reports/phase2_delta.md`.

## E. What capabilities are model-dependent?
Text generation, reasoning quality/metadata, vision/OCR quality where model based, tool choice, and context limits. The UI can operate independently of a particular model but cannot generate meaningful answers without one.

## F. What capabilities are application-dependent?
Conversation persistence, revision/regeneration UX, Markdown/code rendering, attachment import/indexing, citation display, exports, permission UX, provider management, and job cancellation.

## G. What can be implemented locally?
UI, SQLite history/FTS, local documents and retrieval, Markdown/export, local-model inference where hardware/licenses allow, and a local attachment vault.

## H. What requires an external service?
Hosted model access, current web search/retrieval, signed sharing/cross-device sync, and any cloud OCR/vision selected by the user. Use supported APIs and user-owned credentials.

## I. What is the minimum architecture required for feature parity?
React/TypeScript UI; Tauri shell; Rust conversation/context/stream core; SQLite + FTS; provider adapter; Markdown renderer; attachment parser; and a local or hosted model. Search and sharing are optional external connectors.

## J. What should the Windows application's final architecture be?
Use the architecture in `windows_ai_workstation_architecture.md`: React/TypeScript → Tauri → Rust core, with conversation/context/tools/storage components; provider manager for local C++/CUDA or supported cloud APIs; SQLite/FTS/vector retrieval; optional isolated Python document utilities.

## Final conclusion
The evidence supports designing an independent workstation around standard, auditable client components. It does **not** support a specification of DeepSeek consumer web internals yet. Completing the normal human-operated capture matrix is the required next step before treating any web behavior as observed.
