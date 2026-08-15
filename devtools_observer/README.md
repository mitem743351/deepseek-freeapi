# DeepSeek Web Passive Observer

A **local-only passive DevTools observer** for an account owner's normal browser session. It instruments future browser calls to collect sanitized metadata and schema shapes for later architecture research. It is not an API client, proxy, recorder of credentials, or automation tool.

## Safety guarantees
- Never sends observations to any server; data stays in browser memory until you explicitly export/download it.
- Never replays, creates, changes, blocks, or retries requests.
- Never reads/exports cookie values, authorization values, bearer tokens, CSRF values, session values, passwords, API keys, full private messages, or file contents.
- Uses wrappers only to observe **future** `fetch`, XHR, EventSource, and WebSocket calls and immediately forwards the original arguments unchanged.
- Does not solve CAPTCHAs, evade anti-bot/rate controls, scan endpoints, inject cookies, or automate UI actions.

> A DevTools observer can affect timing slightly. Use one synthetic action at a time, do not use it for sensitive chats, and call `reset()` when done.

## Use in Chrome or Edge
1. Open DeepSeek Web normally in your own authorized session.
2. Open **DevTools → Console** and paste all of `deepseek_observer.js` (Chrome may require typing `allow pasting`; that is a browser self-XSS safeguard, not something this toolkit bypasses).
3. Confirm `DeepSeekObserver.status()` returns `RUNNING`.
4. Start one scenario: `DeepSeekObserver.mark("B02_SEND_MESSAGE")`.
5. Perform exactly one normal UI action using synthetic data, then run `DeepSeekObserver.endScenario()`.
6. Inspect `DeepSeekObserver.summary()` and `DeepSeekObserver.export()`.
7. Download sanitized JSON only when reviewed: `DeepSeekObserver.download()`.
8. Run `DeepSeekObserver.reset()` when finished; it restores browser API references and clears only observer memory.

Useful scenario labels: `A02_AUTHENTICATED_LOAD`, `B01_NEW_CONVERSATION`, `B02_SEND_MESSAGE`, `C01_GENERATION`, `C03_STOP`, `C04_REGENERATE`, `E01_TXT_UPLOAD`, `F01_SEARCH`.

## Commands
```js
DeepSeekObserver.start();    DeepSeekObserver.stop();
DeepSeekObserver.pause();    DeepSeekObserver.resume();
DeepSeekObserver.clear();    DeepSeekObserver.reset();
DeepSeekObserver.status();   DeepSeekObserver.summary();
DeepSeekObserver.export();   DeepSeekObserver.download();
DeepSeekObserver.help();
DeepSeekObserver.mark("B02_SEND_MESSAGE");
DeepSeekObserver.endScenario();
DeepSeekObserver.config({ captureTestPayloads: true }); // only CAPTURE_TEST/capture_test strings
```

`captureTestPayloads` defaults to `false`; when enabled it preserves only values visibly marked `CAPTURE_TEST` or `capture_test`, and still redacts sensitive fields.

## Output and redaction
The export follows `observer_schema.json`; `output_example.json` is synthetic. Before placing a downloaded file in `deepseek_web_research/captures/`, inspect it for accidental private data. Keep original HAR files outside Git. The observer itself redacts sensitive field names/query values and long credential-like strings, but human review is mandatory.

## Files
- `deepseek_observer.js` — readable standalone DevTools artifact.
- `deepseek_observer_min.js` — compact distribution generated from the same source; behavior is identical.
- `analysis_guide.md` — how to map export evidence into scenario reports.
- `observer_schema.json` / `output_example.json` — export contract and fully synthetic example.
- `../tests/demo.html` — local non-DeepSeek smoke-demo page.

## Limitations
Response streams are inspected through a cloned response only. The application's original response is never consumed. If cloning/inspection is unavailable, the observer records `NOT_CAPTURED`. Service-worker/cache/IndexedDB inspection is metadata-only; it does not export records or cached response bodies. Browser security policy, opaque responses, and the app's own use of preexisting API references can limit coverage—report those as `UNKNOWN`.
