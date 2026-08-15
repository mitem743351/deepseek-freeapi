# Capability decomposition for independent design

This is a product-capability decomposition, not an assertion about DeepSeek backend implementation.

| Capability | Primary classification | Independent implementation components | Evidence classification |
|---|---|---|---|
| Markdown/code rendering | CLIENT APPLICATION | React renderer + highlighter | INFERRED (standard desktop design) |
| Token generation | MODEL | Local runtime or supported hosted provider | INFERRED |
| Stream consumption | MIXED | Provider transport adapter + Rust event reducer | INFERRED; DeepSeek web transport UNKNOWN |
| Conversation history | CLIENT APPLICATION + SERVER OR SERVICE | SQLite locally; optional sync service | INFERRED; DeepSeek web persistence UNKNOWN |
| Files/document retrieval | MIXED | local vault, parsers, OCR, retrieval, model context | INFERRED; web upload behavior UNKNOWN |
| Web search/citations | EXTERNAL TOOL + CLIENT APPLICATION + MODEL | compliant search provider, provenance store, prompt/context builder | INFERRED; web search behavior UNKNOWN |
| Share links | SERVER OR SERVICE | optional sharing service | INFERRED; web sharing behavior UNKNOWN |
| Browser authentication/storage | UNKNOWN | independent app uses Windows Credential Manager | UNKNOWN for DeepSeek web |

**Finding:** The table decomposes independently reproducible user-visible capabilities and deliberately does not identify proprietary service internals.
**Evidence:** Phase 1/2 independent implementation recommendations; no authenticated Phase 3 trace.
**Confidence:** MEDIUM for desktop design, UNKNOWN for web ownership.
