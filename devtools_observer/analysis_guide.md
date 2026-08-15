# Analysis guide for sanitized observer exports

## Evidence hierarchy
1. **OBSERVED:** an operation, stream field, storage mechanism, or DOM file event captured by the browser observer.
2. **CORROBORATED:** the same result appears in independent scenario captures or is supported by a publicly delivered frontend resource.
3. **INFERRED:** a clearly marked implementation interpretation; never use it to create an endpoint claim.
4. **UNKNOWN:** absent, opaque, unavailable, or ambiguous evidence.

## Recommended workflow
1. Capture one scenario with `mark()` / `endScenario()`.
2. Review exported JSON locally. Reject an export if it contains private content, a URL query value, a name/path that should be private, or anything credential-like.
3. Save only the reviewed JSON as `deepseek_web_research/captures/<scenario>_sanitized.json`.
4. Create/update the corresponding `network/scenarios/<scenario>.md`; cite the capture filename and observation IDs.
5. Add endpoint rows only from `endpoint_inventory` fields: method, origin, path, safe MIME categories, stream status, and scenario evidence.
6. For a claim about generation, require a B02/C01 operation plus its matching `stream_observations` record. Record `UNKNOWN` when the stream clone was not available.
7. For cancellation, require C03 browser evidence. A browser-side abort does not prove server cancellation.
8. For lifecycle/branching/persistence, require repeated B/C scenario evidence and, separately, metadata-only storage evidence. Do not derive database fields from filenames or UI text.

## What the exported fields mean
- `operations`: calls naturally issued **after observer installation**. They are browser observations, not a complete network trace.
- `endpoint_inventory`: deduplicated `method + origin + path`; query values are intentionally never retained.
- `stream_observations`: clone-based metadata/schema analysis. `SSE_LIKE_OBSERVED` means content type or framing was observed; it does not identify an application protocol name.
- `message_conversation_candidates`: a heuristic classification. It identifies a candidate from path/payload/stream evidence and must not be treated as a semantic fact without scenario context.
- `storage_schema`: keys/categories and store metadata only. Sensitive values are redacted and IndexedDB records are not read.
- `attachment_observations`: file-input/drop metadata only; it does not prove an upload until correlated with a natural subsequent request.

## Suggested report wording
```text
Finding: A POST web service request to <origin><path> was observed during B02.
Evidence: OP-0004 in B02_SEND_MESSAGE_sanitized.json; application/json request shape; response content type ...
Classification: OBSERVED.
Confidence: HIGH for the browser request; UNKNOWN for server-side semantics.
```

Never put full prompts, generated text, raw HTTP headers, cookies, bearer values, tokens, session IDs, account identifiers, original HARs, or file contents into reports or Git.
