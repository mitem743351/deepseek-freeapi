# DeepSeek Web Research

This repository contains an evidence-bounded technical architecture study intended to inform an **independent** Windows AI workstation. It does not clone DeepSeek, reuse private protocols, collect credentials, or bypass security controls.

## Phase 1
`deepseek_web_research/` contains public-resource and official-documentation research. It established a public sign-in surface and documented API context while correctly keeping consumer-web runtime behavior unknown.

## Phase 2 purpose
Phase 2 provides the safe, human-assisted capture framework required to observe normal authenticated browser behavior under the account owner's control. It does **not** yet contain an authenticated capture. See:
- `deepseek_web_research/reports/phase2_initial_gap_map.md`
- `deepseek_web_research/docs/phase2_browser_capture_instructions.md`
- `deepseek_web_research/docs/phase2_capture_matrix.md`
- `deepseek_web_research/network/scenarios/`

## Evidence methodology
Evidence first, inference second, implementation third. Reports distinguish **OBSERVED**, **INFERRED**, and **UNKNOWN**. No endpoint, schema, or protocol may be added without a completed, scenario-specific, sanitized normal-browser capture.

## Redaction policy
Never commit passwords, cookies, bearer/API/CSRF/session tokens, account IDs, personal prompts, private documents, credential-bearing URLs, or original HAR files. Keep originals outside the checkout; preferably record a manual sanitized structural summary. The capture instructions list mandatory substitutions and a pre-commit review process.

## Layout
```text
deepseek_web_research/
├── docs/       capture procedures and matrix
├── network/    scenario worksheets, endpoint/stream inventories
├── reports/    evidence assessments and independent app designs
├── schemas/    sanitized conceptual local schemas
├── snapshots/  public collection evidence
└── scripts/    public-only collection helper
```

## Known limitations
This environment cannot create a normal account-owner browser session. Until the owner completes the Phase 2 capture matrix, authenticated web flows, storage, streaming, files, search, and client/server boundaries remain unknown—not guessed.

## Phase 3 status
Phase 3 did not obtain authenticated runtime evidence because a normal account-owner browser session was not safely available in this environment. The indicated credential-bearing attachment was not read, copied, or used. No cookie replay or automated authenticated traffic was created. `deepseek_web_research/docs/phase3_execution_status.md` documents the decision; Phase 3 deliverables preserve UNKNOWN rather than fabricate browser behavior.

**Captured scenarios:** none.
**Evidence coverage:** public Phase 1 evidence and developer API documentation only; no consumer-web authenticated network/storage/event evidence.
**Remaining unknowns:** authenticated operations, conversation lifecycle, streaming, browser storage, uploads, search, sharing, and client/server boundaries.

## Phase 4 status
A sanitized authenticated observer export is now preserved at `deepseek_web_research/captures/deepseek_observation_2026-08-15T06-26-16-686Z.json`. Phase 4 reports use this as their primary evidence source. It establishes observed XHR completion, SSE content type, session/admission/file operations, and storage metadata while keeping SSE event payloads, stop/regenerate behavior, history-record schemas, and backend internals explicitly unknown. See `reports/phase4_final_protocol_assessment.md`.

## Phase 5 status
The Phase 5 baseline capture is preserved at `deepseek_web_research/captures/deepseek_observation_2026-08-15T06-42-36-498Z.json`. It corroborates XHR/SSE transport and adds five marked request windows, but `stream_observations` remains empty and IndexedDB records were not sampled. Phase 5 reports therefore classify actual SSE event framing and `history-message` record structure as **NOT OBSERVABLE in this capture**, with read-only follow-up observers supplied in `devtools_observer/`.

## Phase 6 status
`tampermonkey_observer/` contains a local-only, no-grant Tampermonkey userscript with a persistent Shadow-DOM dashboard, scenario markers, passive network/storage/file/resource metadata observation, and sanitized JSON/ZIP exports. The Phase 6 baseline capture is preserved under `deepseek_web_research/captures/`. The tool deliberately reports stream payloads and cross-origin bundle bodies as not observable when safe browser access is unavailable.
