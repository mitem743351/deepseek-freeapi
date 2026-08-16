# ADR-0001: Tauri 2, React, and a Framework-Neutral Rust Core

- **Status:** Proposed
- **Date:** 2026-08-16

## Context

The legacy application is a single Python/CustomTkinter process. UI widgets coordinate persistence, auth, network streaming, and application state. The target must support a modern desktop UI, native packaging, a local API, strong concurrency/cancellation, and shared execution logic.

## Decision

Use:

- Tauri 2 as the desktop shell
- React/TypeScript/Vite as the frontend
- a framework-neutral Rust application core in workspace crates
- thin Tauri command/event adapters over the core
- Axum as a separate inbound adapter over the same core when local API work begins

The core may not depend on Tauri, React, or Axum types.

## Consequences

Positive:

- modern testable UI
- small native shell relative to Electron
- Rust owns lifecycle, persistence, cancellation, and local API reuse
- desktop and HTTP use one execution engine
- compile-time domain/error contracts

Costs:

- multi-language toolchain and packaging complexity
- Tauri/WebKit platform differences
- Python sidecar distribution remains necessary for DeepSeek initially
- typed IPC schemas require maintenance

## Alternatives considered

### Keep CustomTkinter

Rejected as target architecture. It cannot provide the desired web-grade rendering, state model, virtualization, or frontend test ecosystem without continuing the monolith.

### Electron

Viable UI ecosystem but higher runtime footprint and no reason to make Node the application core. Tauri better matches the Rust/local API direction.

### All-Python with a webview

Would reduce language count but retain weak process/cancellation/security boundaries around the provider and make the requested Rust core/local API direction harder.
