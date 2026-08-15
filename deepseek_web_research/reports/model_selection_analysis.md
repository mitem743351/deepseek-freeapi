# Model selection analysis

| Evidence location | Observed model-related data | Limitation |
|---|---|---|
| Completion body | `model_type` is nullable: string length 7 (1), string length 6 (2), null (8). | Actual strings redacted/not captured; no model identity claim. |
| File upload headers | `x-model-type` header name and `x-thinking-enabled` header name. | Values not captured. |
| localStorage | `debugModelChannel` and `debugLiteModelChannel` JSON descriptors, each holding a string value of length 7. | Values and purpose unknown; names suggest debug-oriented state only. |
| localStorage | `__ds_remote_feature_store_model` string descriptor (15,640 bytes). | Content was deliberately not parsed/exported. |

**Finding:** Model/type selection metadata is carried in at least completion shape and upload header names.
**Classification:** OBSERVED.

**Finding:** Mapping code lengths or debug-channel values to particular DeepSeek model identities is unsupported.
**Classification:** UNKNOWN.
