# Authorized browser capture plan (human-operated)

Use this only with the researcher's own authorized account and ordinary UI interactions. Do not circumvent a CAPTCHA, WAF, login, quota, or rate limit; do not replay authenticated requests outside normal interaction.

1. Start a clean browser profile, sign in normally, accept/reject cookies explicitly, and open DevTools Network + Application.
2. Record only request metadata and **sanitized structural samples** for one action at a time: login, new chat, send, stream, stop, regenerate, edit, rename/delete, synthetic-file upload, search, model settings, share/export.
3. In Application, record names/types/counts of localStorage, sessionStorage, IndexedDB databases/object stores, Cache Storage, service-worker registration, and cookie attributes. Never export values for tokens/cookies/account IDs; write “authentication-related storage exists.”
4. Export a HAR only after removing Cookie, Authorization, CSRF/session headers, query tokens, response bodies containing private content, names, account IDs, file contents, and signed URLs. Do not commit the original HAR.
5. For resources actually fetched by the browser, add normalized URL/type/status/content type/size/SHA-256 to the manifest. Deduplicate by SHA-256. Save only public assets.
6. Update each report with `Finding`, `Evidence`, and confidence, distinguishing direct observation from inference. If a UI feature is not visible, state `UNKNOWN — NOT OBSERVABLE FROM AUTHORIZED CLIENT BEHAVIOR`.
