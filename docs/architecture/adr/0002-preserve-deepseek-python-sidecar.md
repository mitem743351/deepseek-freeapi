# ADR-0002: Preserve the DeepSeek Protocol in an Isolated Python Sidecar

- **Status:** Proposed
- **Date:** 2026-08-16

## Context

The working DeepSeek connection relies on `p2d-deepseek`, undocumented endpoint behavior, mobile-client headers, transient cookies, a PoW challenge, and a bundled WebAssembly solver. Rewriting this in Rust before fixture coverage would risk breaking the repository's key behavior.

The dependency also mutates process-global DNS resolution to IPv4 and uses private APIs that should not contaminate the new core.

## Decision

Keep the initial DeepSeek provider implementation in Python, pinned to the audited p2d artifact, and run it as a supervised sidecar behind a Rust provider adapter.

Use versioned NDJSON over private stdin/stdout for commands and normalized events. Provider secrets are transferred over stdin, never command-line arguments or normal environment configuration. Rust enforces lifecycle and cancellation.

Do not change DeepSeek wire behavior without sanitized fixtures and parity tests.

## Consequences

Positive:

- preserves known-working endpoint/PoW behavior
- confines Python dependency and global socket side effect
- allows Rust core/UI development against MockProvider
- enables adapter rollback and independent upgrades

Costs:

- sidecar packaging for three operating systems
- IPC schema and supervision complexity
- Python/NumPy/Wasmtime bundle size
- hard cancellation may require a per-run subprocess

## Alternatives considered

### Port protocol to Rust immediately

Rejected. There are no captured fixtures for all search/citation/error cases, and PoW behavior is dependency-specific.

### Embed Python in the Rust process

Rejected initially. It weakens failure/global-state isolation and complicates packaging and cancellation.

### Call a paid DeepSeek API instead

Rejected. It violates the behavior-preservation requirement and changes authentication/product semantics.
