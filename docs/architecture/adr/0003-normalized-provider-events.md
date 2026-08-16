# ADR-0003: Versioned Normalized Provider Events

- **Status:** Proposed
- **Date:** 2026-08-16

## Context

The legacy UI consumes untyped dictionaries such as `token`, `thinking`, `done`, and `error`. DeepSeek transport details are partially lost: thinking is batched, search events are discarded, and citations are stripped. Tauri, React, persistence, and the local API need one provider-neutral stream contract.

## Decision

Define a versioned, typed normalized event enum with a common envelope containing request ID, run ID, monotonic sequence, timestamp, provider ID, and relevant domain IDs.

Required lifecycle families include run, thinking, search, message, citation, attachment, tool, usage, completion, cancellation, and failure.

The Rust core validates ordering and guarantees exactly one terminal event. Tauri and Axum translate from this same stream.

## Consequences

Positive:

- UI and API do not understand DeepSeek patches
- replayable deterministic reducer and integration tests
- explicit search/reasoning/citation support
- stale/duplicate/out-of-order events can be detected
- providers can be added without rewriting core consumers

Costs:

- adapter mapping work
- schema versioning and compatibility policy
- some provider metadata must remain in a namespaced extension
- event persistence/checkpoint policy must avoid excessive writes

## Alternatives considered

### Pass provider JSON through the core

Rejected because it makes the UI/local API provider-specific and prevents typed ordering guarantees.

### Stream only text

Rejected because it cannot represent reasoning, search, citations, tools, status, or cancellation correctly.

### One final response object

Rejected because streaming is a first-class requirement.
