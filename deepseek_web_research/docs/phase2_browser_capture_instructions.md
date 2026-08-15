# Phase 2 authorized browser capture instructions

## Purpose and boundary
This procedure obtains **only normal, account-owner browser evidence** needed to fill Phase 1 gaps. It is not a request-replay, scraping, anti-bot evasion, or security-testing procedure. Do not bypass CAPTCHA, WAF, MFA, login, access controls, quotas, or rate limits. Do not provide passwords, cookies, API keys, bearer tokens, or session values to this repository or to a researcher.

## Before capture
1. Use Chrome or Microsoft Edge and your own authorized DeepSeek account. Do not use shared accounts.
2. Use only synthetic prompts (for example, `PHASE2_SYNTHETIC_ALPHA`) and synthetic attachments. Do not use personal, confidential, regulated, or customer content.
3. Create a local folder outside this Git checkout for **original** HAR files. Original HAR files often contain secrets and must never be committed, sent, or copied into this repository.
4. Read the relevant worksheet in `network/scenarios/` before each action. Complete exactly one scenario per capture.

## Network capture steps (repeat independently for each scenario)
1. Open the normal DeepSeek web application and sign in through its ordinary UI.
2. Open DevTools: `F12` or `Ctrl+Shift+I`. Select **Network**.
3. Turn on **Preserve log** and ensure the red record button is enabled. Optionally enable “Disable cache” only while DevTools is open and note that choice in the worksheet.
4. Clear prior entries using the clear button.
5. Perform only the worksheet's one normal UI action. For generation, wait for complete/stop/error as applicable.
6. Stop and inspect the sequence. Record only method, host, path, broad header categories, MIME type, status, initiator category, timing, ordering, and redacted structural field names in the worksheet.
7. Save an **original** HAR locally only if you need it for personal review. Do not upload or commit it.
8. Close/clear DevTools before the next scenario. Use a new clear capture for every scenario.

## Application/storage inventory (once after A02; repeat after A04 if useful)
In DevTools **Application** (Chrome) or **Application/Storage** (Edge), inspect only names, types, and approximate schema:
- Local Storage and Session Storage: key names and value *category*, never values.
- IndexedDB: database/object-store/index names and record count bands, never records.
- Cache Storage: cache names and entry counts, never private response bodies.
- Service Workers: registration scope/status only.
- Cookies: host, name category, expiry/SameSite/Secure/HttpOnly attributes only; never values.

For a sensitive item write exactly: **Authentication-related value present — redacted.** Do not screenshot token values.

## Mandatory sanitization before any evidence leaves the owner’s machine
Best option: create a short manual evidence summary in the matching scenario worksheet, not a HAR. If a sanitized HAR/equivalent is approved for storage, make a copy and remove or replace all of the following from **requests, responses, headers, cookies, query strings, URLs, bodies, stack traces, and screenshots**:

| Remove/redact | Replacement |
|---|---|
| `Cookie`, `Set-Cookie` and cookie values | `<COOKIE_REDACTED>` |
| `Authorization`, `Bearer`, API keys | `<TOKEN_REDACTED>` |
| CSRF/XSRF values | `<CSRF_REDACTED>` |
| Session identifiers | `<SESSION_REDACTED>` |
| Account/user identifiers, email, phone | `<ACCOUNT_ID_REDACTED>` |
| Personal message text | `<MESSAGE_REDACTED>` (retain only field names/type) |
| Uploaded file bytes/name/path/content | `<FILE_REDACTED>` |
| Signed/private URLs and credential-bearing query parameters | `<PRIVATE_URL_REDACTED>` |

Then search the proposed artifact case-insensitively for: `authorization`, `bearer`, `cookie`, `set-cookie`, `csrf`, `xsrf`, `token`, `session`, `password`, `api_key`, `secret`, `@`, and your synthetic marker. Inspect every match. A filename being “sanitized” is not evidence that it is safe.

## Scenario rules
- **C05 retry after failure:** capture only a naturally occurring UI failure/retry affordance. Do not induce failures via malformed requests, devtools blocking, quota exhaustion, or network manipulation.
- **E01–E08:** use no-sensitive synthetic fixtures; capture only types that the visible UI accepts. Record unsupported types as “UI rejected/not exposed,” not as a failure to work around.
- **F/G scenarios:** use only visible UI controls. Do not open private service routes or publish a share link. Do not copy a share URL into Git.

## Completion handoff
For each completed scenario, populate its worksheet with a local evidence reference and sanitized observations. Keep originals private. A researcher can then update inventories and reports without ever receiving secrets.
