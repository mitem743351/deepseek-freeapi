# ADR-0005: OS Secure Storage for Provider Credentials

- **Status:** Proposed
- **Date:** 2026-08-16

## Context

The legacy app writes the DeepSeek browser token to two plaintext files and process environment. File permissions are best-effort and inconsistent across platforms. The new frontend must not receive stored secrets, and SQLite must not contain them.

## Decision

Store provider credentials through a Rust credential abstraction backed by the operating system credential service:

- Windows Credential Manager
- macOS Keychain
- Linux Secret Service

SQLite stores only an opaque `credential_ref` and account metadata. The UI submits a token once and subsequently receives only account status/masked metadata. DeepSeek sidecar handoff uses private stdin IPC.

If secure storage is unavailable, return a typed actionable error. Do not silently fall back to plaintext.

## Consequences

Positive:

- materially improves secret-at-rest protection
- removes token from normal UI/database/config state
- centralizes redaction and account lifecycle
- provider-neutral account model

Costs:

- platform-specific behavior and test mocks
- Linux desktop service dependency
- migration flow for existing plaintext credentials
- packaging/permissions diagnostics

## Alternatives considered

### Keep `.env` with `0600`

Rejected as the default because it is plaintext, duplicated, and weak on Windows.

### Encrypt a file with a bundled application key

Rejected because a key stored with ciphertext does not provide meaningful protection.

### Store in SQLite

Rejected because database backups/exports would carry credentials and database encryption is not otherwise guaranteed.
