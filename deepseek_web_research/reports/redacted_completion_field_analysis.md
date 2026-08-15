# Redacted completion-field analysis

**Finding:** The completion request contains one observer-redacted field in every observed request.
**Evidence:** all 11 completion request schemas include `<REDACTED_FIELD>`.
**Classification:** OBSERVED.

**Finding:** Its name and semantic role are **UNKNOWN — redacted by observer**.
**Evidence:** the export replaces sensitive field names before persistence; no safe public frontend-code evidence was captured in this phase to identify it.
**Classification:** UNKNOWN.

No attempt was made to recover the field name from credentials, request values, client memory, or service behavior. The same placeholder also occurs in other response schemas, so placeholder equality does not establish that it is the same original field.
