# Authentication and Credential Architecture

## Current state

The legacy application accepts the DeepSeek browser `userToken`, then duplicates it in:

- `.env` as `DEEPSEEK_TOKEN`
- `data/auth_token.json` as a plaintext JSON field
- process environment
- in-memory Python client fields
- settings UI variable/entry state

Files are Git-ignored and POSIX permissions are set to `0600` where supported, but this is not secure credential storage and has no equivalent guarantee on Windows.

## Target goals

- OS-native secure credential storage
- no credential value in SQLite
- no credential returned to React after submission
- no credential in process arguments, logs, crash reports, or Tauri events
- provider-neutral account model
- explicit authentication status and typed expiry handling
- controlled legacy credential import and deletion

## Trust boundaries

```text
React token entry
  -> Tauri command payload (single submission)
  -> Rust CredentialService
       ├─ validate with provider
       └─ OS secure credential store
             │ credential_ref only
             ▼
          SQLite account metadata

Run execution
  -> Rust resolves credential_ref
  -> scoped secret wrapper
  -> private sidecar stdin
  -> DeepSeek provider request
```

The frontend should retain the entered token only long enough to invoke the command, then clear the field and local state. Subsequent UI queries return:

```text
account_id
provider
label
status
masked_identifier (optional)
last_validated_at
capabilities
```

They do not return the token.

## Credential service interface

Conceptual Rust trait:

```rust
#[async_trait]
pub trait CredentialStore: Send + Sync {
    async fn put(
        &self,
        key: &CredentialKey,
        secret: &SecretString,
    ) -> Result<(), AuthError>;

    async fn get(
        &self,
        key: &CredentialKey,
    ) -> Result<SecretString, AuthError>;

    async fn delete(
        &self,
        key: &CredentialKey,
    ) -> Result<(), AuthError>;
}
```

Use a secrecy wrapper whose `Debug`/`Display` cannot reveal contents. Avoid converting to ordinary `String` except in the narrow provider handoff scope.

## OS storage

Initial adapter target:

- Windows Credential Manager
- macOS Keychain
- Linux Secret Service/libsecret

A Rust keyring abstraction is appropriate if it supports all packaging targets and errors are explicit.

Linux without a credential service must produce `CredentialStoreUnavailable`, with remediation. It must not silently fall back to plaintext.

An optional encrypted-file fallback may be designed later, but only if:

- explicitly enabled by the user
- backed by a user passphrase or OS-bound key
- uses reviewed authenticated encryption and KDF parameters
- never stores the decryption key beside ciphertext

## Provider account records

SQLite stores non-secret metadata:

```text
provider_account_id
provider_id
label
credential_ref
status
last_validated_at
created_at
updated_at
```

`credential_ref` is an opaque keyring lookup identifier. It should not encode the secret or a token hash.

## Authentication flow

### Add/update account

1. UI submits provider ID, label, and token once.
2. Tauri immediately moves payload into Rust secret wrapper.
3. Provider validates via its authentication method.
4. On success, Rust stores secret in OS keyring.
5. Rust transactionally creates/updates account metadata with credential reference.
6. Rust returns account summary only.
7. UI clears entry state.

Policy decision to finalize: whether users may save an unvalidated credential while offline. If supported, status must be `unverified`, not `ready`.

### Resolve for run

1. Core loads account metadata.
2. Credential service retrieves secret.
3. Secret is passed to provider adapter in memory.
4. For Python DeepSeek sidecar, secret is sent through private stdin frame.
5. Provider uses it in `authorization` header.
6. Secret wrapper is dropped promptly after request/session setup as implementation permits.

### Expiry

DeepSeek invalid-token conditions map to `AuthenticationExpired` with account ID. Core updates account status, cancels dependent queued runs, and emits a user-safe action requirement. The UI opens account remediation without showing the old token.

### Logout/delete

1. Stop or reject new runs for account.
2. Invoke provider logout hook if meaningful.
3. Delete keyring secret.
4. Update/delete account metadata.
5. Clear cached provider sessions.
6. Do not delete conversations automatically; detach account reference according to FK policy.

## Legacy credential import

The migration may discover `.env` and `data/auth_token.json`.

Safe import procedure:

1. Run only with explicit user consent.
2. Prefer `.env` according to current precedence, detect conflicting values, and never print either.
3. Validate/store in keyring.
4. Create provider account metadata.
5. Ask before deleting legacy plaintext files.
6. If deletion is accepted, remove token keys/files and verify absence.
7. Record a non-secret import marker.
8. Never copy token into new config or SQLite during migration.

Do not automatically import on developer/test machines without a user prompt.

## Sidecar handoff

Forbidden channels:

- command-line argument
- process title
- environment variable
- temporary plaintext file
- stdout event
- stderr log

Preferred channel: versioned command over already-open private stdin. The sidecar must reserve stdout for protocol frames and redact secrets from stderr.

For a per-run subprocess, Rust writes the secret after spawn. For a long-lived sidecar, scope credentials by account/run and provide an explicit forget/logout command; do not maintain an unbounded credential cache.

## Redaction

Create a centralized redaction policy for:

- structured tracing fields
- error source chains
- sidecar stderr ingestion
- panic/crash reports
- local API errors
- support diagnostics exports

Never log:

```text
authorization
token
cookie
ds_session_id
x-ds-pow-response
challenge/signature
raw HTTP headers
prompt/response/reasoning content by default
```

Do not log token prefixes, suffixes, or stable hashes as correlators. Use account IDs generated by the application.

## UI rules

- Account screen queries status, never secret.
- Token field starts empty for updates; a mask such as “credential stored” is metadata, not the real value in an input.
- “Show token” is not available after storage because UI does not possess it.
- Clipboard operations for credentials should be avoided.
- Validation progress and errors use typed safe messages.
- Password managers/paste remain usable in the one-time entry control.

## Local API authentication

The local API is separate from provider credentials.

Defaults:

- disabled unless user enables it
- bind loopback only
- generated local API bearer secret stored in keyring
- never reuse DeepSeek token as local API auth
- deny permissive CORS
- redact Authorization headers
- show listening address and status in UI

Remote bind requires an explicit advanced configuration and a stronger threat-model review.

## Typed auth errors

```text
AuthenticationRequired
AuthenticationExpired
CredentialStoreUnavailable
CredentialNotFound
CredentialWriteFailed
CredentialDeleteFailed
CredentialValidationFailed
AccountDisabled
ProviderUnavailable
SidecarCredentialTransferFailed
```

Each has stable code, safe user message, retry/action guidance, and redacted diagnostic source.

## Tests

- credential values never serialize into account DTOs
- `Debug`/`Display` of secret wrapper are redacted
- keyring adapter put/get/delete with platform mocks
- unavailable keyring does not create plaintext fallback
- legacy import precedence/conflict/idempotency
- expiry updates account status
- logout clears provider session metadata
- structured log snapshot contains no seeded secret
- sidecar command line/environment contain no secret
- local API credential is independent from provider token
