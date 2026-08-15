# Thinking-mode protocol

`thinking_enabled` is present as a boolean field in every observed completion request. A localStorage key `thinkingEnabled` has a JSON wrapper whose `value` is boolean. Upload request header names also include `x-thinking-enabled`.

**Observed:** field/header/key presence and boolean type.
**Not observed:** boolean values, any mode-specific request variant, stream event distinction, timing comparison by mode, or hidden reasoning content.

No chain-of-thought content was collected or reconstructed. The mode is therefore a user-visible protocol control candidate, not a proven model-internal behavior.
