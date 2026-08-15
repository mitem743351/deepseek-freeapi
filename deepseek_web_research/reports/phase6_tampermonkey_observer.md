# Phase 6 Tampermonkey observer

## Implemented capabilities
- Persistent, movable/minimizable Shadow-DOM dashboard with Overview, Requests, Streams, Files, Storage, Frontend, Scenarios, and Export tabs.
- Manual scenario selection, start/end markers, pause/resume/stop/clear controls, and local-only in-memory observation state.
- Passive wrappers for future `fetch` and XHR, plus XHR progressive-response and cloned-fetch stream metadata parsing. Original request arguments and original responses are forwarded unchanged.
- Storage metadata inspection, read-only IndexedDB store metadata, cache/service-worker metadata, file input/drop metadata, already-loaded performance/DOM resource inventory, and inline-script-only string correlation.
- Local summary/full JSON downloads and an uncompressed ZIP research package using browser-native `Blob` download; no GM APIs or external dependencies.
- Recursive redaction and credential-shaped-value validation before export. A local synthetic self-test exercises parser/redaction metadata only and creates no network traffic.

## Browser limitations
- This tool cannot force access to application-owned stream payloads. It records `NOT_OBSERVABLE`/empty event metadata rather than consuming a body or breaking the application.
- Cross-origin JavaScript bundle contents are not fetched, crawled, or exported. Resource metadata is observed through Performance/DOM and only inline script text is scanned.
- IndexedDB schema profiling is metadata-only in the main dashboard. Existing Phase 5 read-only companion observer remains the bounded record-field profiler.
- A request wrapper cannot see operations made before installation or calls using a pre-captured native function reference.

## Security properties
The userscript does not send data, invoke any discovered endpoint, replay/modify traffic, access cookies/authorization values, solve or alter security challenges, automate chat actions, or create a proxy. Exports omit private prompt/model-response content, file contents, authentication values, and external bundles.

## Test results
- `node --check` validates userscript syntax.
- JSON schemas parse successfully.
- The built-in `DeepSeekObserver.selfTest()` is local-only and verifies synthetic SSE schema parsing plus redaction logic without interacting with the application.
- The Phase 6 baseline capture was parsed completely; it confirms loaded frontend resource metadata but contains no `stream_observations` or IndexedDB record samples.
