# Architecture assessment

## Observed boundary
```text
Public browser → chat.deepseek.com sign-in surface
Developer client → api.deepseek.com/chat/completions (documented API)
```

**Finding:** The documented developer API receives conversation messages and returns completion data, optionally streamed.
**Evidence:** [Official API docs](https://api-docs.deepseek.com/api/create-chat-completion/).
**Confidence:** HIGH.

**Finding:** Authentication, chat persistence, file handling, web search orchestration, telemetry, and web frontend component boundaries are unknown for the consumer service.
**Evidence:** No authorized session/network/static bundle trace.
**Confidence:** UNKNOWN.

The accompanying SVG deliberately labels unobserved services as unknown rather than presenting an invented proprietary architecture.
