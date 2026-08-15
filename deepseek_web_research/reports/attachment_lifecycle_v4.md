# Attachment lifecycle v4

## Observed variants

| Selection time | MIME / size | Upload operation | Fetch operation(s) | Completion reference shape |
|---|---|---|---|---|
| 06:23:07.656Z | `image/png`, 17,177 bytes | OP-0023 at 06:23:07.672Z, multipart field `file` | OP-0032 / OP-0034 | OP-0037: `ref_file_ids` array length 1, string item length 41 |
| 06:25:01.777Z | `application/json`, 98,997 bytes | OP-0106 at 06:25:01.786Z, multipart field `file` | OP-0115 | OP-0118: `ref_file_ids` array length 1, string item length 41 |

## Metadata shape
Upload and fetch response schemas share an object with `id`, `status`, `file_name`, `from_share`, `file_size`, `model_kind`, a redacted field, `error_code`, `inserted_at`, `updated_at`, `is_image`, and `audit_result`. Later fetch observations additionally show a `signed_path` string field (length 411/413); its value was not retained and must be treated as sensitive/private-path-adjacent.

**Finding:** File choice → multipart upload → metadata fetch → later completion with a one-element file-reference shape is temporally supported twice.
**Classification:** OBSERVED/PARTIAL.

The capture does not establish that a given uploaded `id` equals the later reference (both values were not retained), server extraction/vision processing, acceptance for PDF/DOCX/TXT/XLSX, or attachment persistence semantics.
