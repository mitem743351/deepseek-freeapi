# Phase 6 frontend analysis plan

## Available primary resource metadata
The Phase 6 baseline observed loaded public resources including `fe-static.deepseek.com` main/vendor JS, CSS, KaTeX assets, and `manifest.json`; it also records client/API resource timings. This metadata is sufficient to identify which resources were browser-delivered, but not to export/reproduce bundle contents.

## Next safe workflow
1. Use the Tampermonkey Frontend tab to export only already-loaded resource origin/path/type/size/initiator metadata.
2. Correlate route strings observed in network exports with the resource inventory.
3. Scan inline scripts locally for predefined route/feature strings. Treat a match as corroboration only, never as a hidden-endpoint discovery method.
4. If a browser already exposes a same-origin/public script body safely, record match category and approximate location only; do not export the bundle.
5. Combine resource metadata with explicitly marked scenario timelines, not with request replay or crawling.

## Current limitations
The Phase 6 capture lists `default-vendors.80d8928a1a.js`, `main.69ea66451d.js`, and related assets, but no safe source-body matches. Static resource analysis therefore remains PARTIAL until a normal browser exposes safe local textual evidence.
