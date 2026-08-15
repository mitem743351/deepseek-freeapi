# DeepSeek Web Passive Research Observer (Tampermonkey)

A local-only, passive in-page research dashboard for an account owner's normal `https://chat.deepseek.com/*` session. It replaces the manual DevTools workflow with a persistent Shadow-DOM panel, while preserving the boundary: it observes only browser activity that the page itself initiates.

## Safety properties
- No `GM_*` APIs, no external libraries/CDNs, no remote logging, and no observer-created network requests.
- Never replays/changes requests, injects cookies, extracts credentials, solves PoW/CAPTCHA, automates the UI, or bypasses controls.
- Captures schemas/lengths and safe metadata—not private prompt text, model-response text, file contents, cookie values, authorization values, or tokens.
- Export stays local through a browser download after credential-pattern validation.

## Install
1. Install Tampermonkey in Chrome/Edge.
2. Create a new userscript.
3. Replace its contents with `deepseek_observer.user.js` and save.
4. Open DeepSeek normally. The panel appears in the top-right corner.

## Use
1. Select a scenario (`NORMAL_MESSAGE`, `THINKING_MESSAGE`, `SEARCH_MESSAGE`, `FOLLOWUP_MESSAGE`, `FILE_MESSAGE`, or `CANCELLATION`).
2. Click **Start** and **Mark action** before doing one normal UI action.
3. Use the UI normally; the observer never clicks/sends anything.
4. Click **Stop**, review the tabs, then use **Export** for summary JSON, full sanitized JSON, or an uncompressed local ZIP package.
5. Use `window.DeepSeekObserver.reset()` only when you want original browser API references restored.

`Capture synthetic test payloads` remains off by default; this version exposes it only through `window.DeepSeekObserver` configuration work in future revisions, so exports retain schema/lengths by default.

## Limits
- XHR progressive `responseText` may be safely visible; if not, streams are marked not observable instead of being consumed.
- Fetch bodies are inspected only through a clone. The original page response is returned untouched.
- Cross-origin bundles are **not fetched**. Frontend analysis inventories already-loaded resources and scans inline scripts only; external bundle source is reported as unavailable under normal same-origin policy.
- IndexedDB samples are read-only, bounded schema profiles. Private values are never exported.
