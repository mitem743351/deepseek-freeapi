# Admission-control observation

**Finding:** The client made 13 observed JSON XHR POSTs to `/api/v0/chat/create_pow_challenge`.
**Evidence:** OP-0014, 0024, 0028, 0043, 0055, 0064, 0079, 0089, 0097, 0107, 0111, 0125, and 0135. Request schema is `{target_path: string}` (observed lengths 23 or 24). Response shape contains `challenge` with algorithm/challenge/salt/signature/difficulty/expiry/target-path fields.
**Classification:** OBSERVED.

**Finding:** Completion requests expose the safe header name `x-ds-pow-response`; its value is not retained.
**Evidence:** all 11 completion request header-name lists.
**Classification:** OBSERVED.

A challenge is temporally near each of several generations and both uploads, including a two-challenge sequence after each observed file upload. It is not safe to infer the exact target path, solve/verify algorithm, challenge consumption rule, frequency policy, or server-side enforcement from this capture. No challenge-solving or replay mechanism is implemented or described here.
