# Windows feature-parity roadmap

| Tier | Feature | Difficulty | Dependencies | Local/cloud | Complexity |
|---|---|---|---|---|---|
| 1 Core | Chat, Markdown, code, history | Easy–Moderate | React, SQLite | Local | 2–4 weeks |
| 1 Core | Streaming, stop, regenerate, model selection, reasoning UI | Moderate | Rust async/provider adapters | Local or cloud model | 4–8 weeks |
| 2 Documents | PDF/DOCX/XLSX/CSV/image intake and retrieval | Moderate–Difficult | parsers, OCR, vault, indexing | Local; optional model | 6–12 weeks |
| 3 Search | Web search, sources, citations, research workflow | Moderate | compliant search provider, provenance | Cloud retrieval required | 4–8 weeks |
| 4 Agent | tools, filesystem, terminal, browser, planning | Difficult | sandbox/policy/approval UI | Mixed | 12–24+ weeks |
| 5 Platform | projects, memory, plugins, manager, GPU/global assistant/automation | Difficult | permissions, updater, plugin model | Mixed | 16–36+ weeks |

Estimates are broad engineering complexity bands for a small experienced team, not delivery promises. Agent features require explicit user confirmation and sandboxing.
