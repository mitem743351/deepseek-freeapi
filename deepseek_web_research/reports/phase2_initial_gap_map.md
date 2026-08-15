# Phase 2 initial gap map

**Evidence position:** this map follows a full Phase 1 package review. No authenticated browser capture is present in the repository as of 2026-08-15. Therefore Phase 2 cannot upgrade any web-runtime finding until an account owner supplies sanitized, normal DevTools evidence.

## Known
| Finding | Evidence | Confidence |
|---|---|---|
| A public DeepSeek chat sign-in surface exists. | Phase 1 public retrieval record. | HIGH |
| The separately documented developer API accepts JSON messages and documents optional data-only SSE terminated by `data: [DONE]`. | Official API documentation cited in Phase 1. | HIGH for API only |
| Phase 1 retained a public `robots.txt` artifact and no production client bundle. | `snapshots/resource_manifest.json`, `collection_log.md`. | HIGH |
| The research boundary forbids credential capture, control circumvention, request replay, and access to other users' data. | Phase 1 capture plan and mission. | HIGH |

## Partially known
| Topic | Existing evidence | Limitation | Confidence |
|---|---|---|---|
| File upload / web-search concepts | Official project material references prompt templates. | Does not show current web UI, routes, schemas, or processing. | MEDIUM contextual / UNKNOWN web runtime |
| Models/reasoning | Developer API docs list models and thinking controls. | Does not identify consumer web selections or UI state. | HIGH API / UNKNOWN web |
| Browser authentication | Sign-in UI exists. | Storage/cookie/session mechanism, values, and network sequence are not inspected. | HIGH UI / UNKNOWN protocol |

## Unknown
- Authenticated page-load/reload/sign-out network behavior and runtime assets.
- All web conversation/message IDs, ordering, edit/regenerate/stop/retry semantics, and persistence behavior.
- Web generation transport, framing, cancellation, completion/error events, and browser API used.
- Browser storage mechanisms, schemas, persistence, and service worker/cache behavior.
- File acceptance, preprocessing, upload sequence, attachment representation, and association.
- Search/research queries, source/citation schemas, sharing/export, feature flags, and telemetry.
- Client/server ownership boundaries apart from general product inference.

## Requires browser evidence
Every A01–G03 scenario worksheet in `network/scenarios/` requires normal account-owner DevTools evidence. See `docs/phase2_browser_capture_instructions.md`; no task should be marked observed without a scenario-specific sanitized record.

**Finding:** Current Phase 2 status is preparatory, not observational.
**Evidence:** No sanitized authenticated HAR, Network export, DevTools storage inventory, or scenario notes were present during repository review.
**Confidence:** HIGH.
