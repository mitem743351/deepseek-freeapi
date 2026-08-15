# Differential follow-up analysis v5

Within each marked window, initial-looking completion shapes have `parent_message_id: null` plus non-null string `model_type`, while later-looking requests have numeric `parent_message_id` and null `model_type`. For example, SCENARIO-004 has OP-0066 (null parent, string model type) followed by OP-0075 and OP-0085 (numeric parent, null model type).

**Finding:** The capture repeats a null-parent/string-model shape followed by numeric-parent/null-model shapes.
**Classification:** OBSERVED.

**Finding:** Numeric parent form represents a follow-up to the preceding null-parent request.
**Classification:** INFERRED. Prompt content and parent values were not retained, and scenario labels do not identify S1/S4.

`action` is null in every captured completion shape and `preempt` is boolean with no retained values. No regenerate/edit/branch behavior is established.
