# Differential search analysis v5

All completion schemas contain `search_enabled: boolean`; values are absent. `GET https://hif-dliq.deepseek.com/query` occurs once in SCENARIO-003 and four times in SCENARIO-005, while no such request occurs in scenarios 001, 002, or 004.

**Finding:** The query operation is scenario-correlated with two marked windows.
**Classification:** OBSERVED temporal correlation.

**Finding:** It is a search backend operation or is caused by `search_enabled=true`.
**Classification:** UNKNOWN. The labels/settings values and response purpose are unavailable, and no source/citation stream payload was captured.

No search-specific citations or sources are established.
