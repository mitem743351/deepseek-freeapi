# Differential thinking analysis v5

All ten completion request shapes contain `thinking_enabled: boolean`, and localStorage exposes a boolean-wrapped `thinkingEnabled` key. The observer redacts values by design; the five scenario labels are all `B02_SEND_MESSAGE` rather than S1/S2.

| Comparison dimension | Result |
|---|---|
| Identifiable normal S1 versus thinking S2 | UNKNOWN |
| Request field presence | Same schema-level field observed |
| Boolean value comparison | NOT OBSERVED |
| Stream event/count comparison by mode | NOT OBSERVED; no stream records |
| Timing comparison by mode | UNKNOWN; scenarios cannot be assigned to settings |
| Hidden reasoning content | Not collected and not analyzed |
