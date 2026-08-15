# Feature inventory

“Available?” means demonstrated in this study, not rumored or assumed.

| Category | Feature | Available? | Observed behavior / network / state | Confidence |
|---|---|---:|---|---|
| Chat | Create, edit, regenerate, stop, retry, delete, rename, history search | Not demonstrated | No authorized web interaction trace. | UNKNOWN |
| Reasoning | Thinking mode/model selection/generation controls/response state | Not demonstrated in web | API docs expose `thinking` and `reasoning_effort`; web mapping unknown. | HIGH API / UNKNOWN web |
| Files | Upload, document analysis, image handling | Not demonstrated in web | Official repository has a file-upload prompt template; protocol unknown. | MEDIUM contextual / UNKNOWN web |
| Search | Web search/research/citations/source UI | Not demonstrated in web | Official repository refers to web-search prompt design; current UI/protocol unknown. | MEDIUM contextual / UNKNOWN web |
| Sharing | Share, export, links | Not demonstrated | `robots.txt` disallows `/share/`, but this does not prove a sharing feature or semantics. | LOW |
| Account | Login | Public surface observed | Public sign-in page offers sign-up/log-in and Google/Apple options. Network/storage flow not observed. | HIGH UI surface / UNKNOWN protocol |
| Account | Settings, preferences, usage UI | Not demonstrated | No authorized session. | UNKNOWN |

## Interpretation
No feature is marked “available” solely because it is common in chat products. Product changes, account tiers, and regions may alter the visible UI.
