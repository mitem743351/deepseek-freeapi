# Public snapshot collection log

**Date:** 2026-08-15 UTC
**Scope:** unauthenticated, public browser resources only.

| Target | Result | Notes |
|---|---|---|
| `https://chat.deepseek.com/` | Redirected to sign-in by the public retrieval client | No page HTML, bundle URL, source map, manifest, stylesheet, font, or image URL was captured. No retry or protection bypass was attempted. |
| `https://chat.deepseek.com/robots.txt` | 200 | Captured verbatim; listed in `resource_manifest.json`. |

The available automated environment could not establish a normal browser session or DevTools capture. This package therefore intentionally does **not** make claims about the current production bundle, framework, endpoint paths, browser storage, or web-chat wire protocol. The provided collection script may be used manually in a permitted Windows browser research session with an explicit public URL allowlist; it neither sends cookies nor follows an authenticated workflow.
