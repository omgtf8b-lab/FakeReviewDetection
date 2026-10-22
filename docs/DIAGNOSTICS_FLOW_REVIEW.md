# Diagnostics propagation review — 2026-10-22

Base: `963422c647a127f4cc91a2b63c36da116bdf41cd`, branch `fix/collector-diagnostics`. No changes were applied to the running outputs copy, its environment, backend port 8001, PostgreSQL or main.

## Findings and changes

| Boundary | Previous gap | Current behavior |
|---|---|---|
| Browser execution | Unexpected profile/proxy/cleanup failures became a generic result without diagnostics | `execute_payload` returns an allowlisted worker execution error, without raw exception text |
| Browser worker JSON | Valid JSON could carry arbitrary extra diagnostic fields | Worker transport filters diagnostic slots before returning |
| Collection strategy | HTTP fallback retained only the code; structured stage/evidence/configuration was lost | Each Selenium attempt retains full allowlisted diagnostics, even if HTTP metadata/reviews are selected |
| Outer strategy process | Spawn failure escaped the try block; nonzero exit was unchecked; timeout cleanup could obscure the original failure | Structured collection-stage spawn/exit/invalid-output/I/O/timeout codes; no stdout/stderr details returned |
| Snapshot write | Entire diagnostic dictionaries were stored | Filter before encoding/checksum; no schema migration needed |
| Snapshot read/export | Historical arbitrary diagnostic fields could be returned | Verify immutable source checksum first, then filter the public export view; do not rewrite stored rows |
| Analysis failure | Saved source had diagnostics, but the failed job returned only a generic message/snapshot ID | Re-read the owner's verified saved evidence and retain safe attempts/diagnostics in the failed result |
| API detail/history | Stored legacy diagnostic blobs were returned unfiltered | Apply the same public schema at response construction |
| React/Flutter | Neither showed the diagnostic code | Both show known-code labels and optional numeric observed versions on failed and completed results |

When HTTP fallback succeeds, the browser failure remains a **failed attempt**, not a claim that the entire collection failed. UI wording makes this distinction and does not infer platform blocking or fraudulent reviews.

## Public contract

`diagnostics` contains an allowlisted `stage` and `code`, with optional allowlisted exception type, evidence categories, bounded integer return code, numeric version observations and boolean configuration flags. Unknown keys, malformed types, arbitrary messages/logs/paths and nonnumeric versions are dropped. Configuration values are never exported as paths. Malformed top-level collection/job values fail closed.

`attempts` is a bounded list of known collector identities and machine statuses. An entry can include both the legacy `diagnostic_code` and the structured `diagnostics`. Old code-only attempts remain displayable. Both frontend implementations use their own known-code label map; they never render JSON diagnostic blobs, exception messages, profile paths or log tails.

Example after an HTTP fallback (review/product data omitted here):

```json
{
  "attempts": [
    {
      "collector": "selenium",
      "status": "browser_start_failed",
      "diagnostic_code": "chrome_crashpad_failed",
      "diagnostics": {
        "stage": "startup",
        "code": "chrome_crashpad_failed",
        "exception_type": "SessionNotCreatedException",
        "evidence": ["crashpad_self_termination"],
        "driver_version_from_log": "156.0.8078.47"
      }
    },
    {"collector": "http", "status": "reviews_collected"}
  ]
}
```

Snapshot `sha256` remains the digest of the verified original stored payload. New `dataset_sha256` is the digest of the canonical public dataset exported by the endpoint (UTF-8 JSON, sorted keys, no extra whitespace). For a historical row containing diagnostic fields now removed, the two digests can differ. Stored payload/hash remain unchanged; tests explicitly assert this.

The sanitizer targets diagnostic slots and known historical debug fields, not review text/media evidence. Existing owner-only access checks remain in force. This is not a general-purpose PII redactor for user-submitted review content.

## Verification actually executed

| Check | Latest result |
|---|---|
| Full backend `pytest tests -q -p no:cacheprovider` | **107 PASS, 0 FAIL, 0 skipped/deselected**, 65.61 s |
| Node tests for diagnostic presentation | **4 PASS, 0 FAIL** |
| Flutter tests | **26 PASS, 0 FAIL** |
| Dart analyze lib/test | **No issues found** |
| React production build | **PASS**; existing large-chunk warning remains |

The full backend run used a new disposable SQLite path and in-memory API fixtures. The trusted SVM artifact was read from its existing local location without copying/modifying it. External service URLs were disabled. Browser startup failures and subprocess output were controlled fixtures, not real marketplace requests. Tests cover the worker failure payload, transport filtering, HTTP-first/fallback branches, API detail/history, saved snapshot, failed analysis, legacy immutable evidence and owner isolation. UI tests cover safe labels, fallback/code-only compatibility, deduplication, invalid versions and hostile extra fields.

One existing Starlette/httpx deprecation warning remains. Earlier environment-blocked runs from preceding work are not represented as passing runs; this review's latest full pytest, web and Flutter commands all completed with exit 0. There are no environment-blocked tests in this latest verification set.

## Not exercised and limits

- No production restart, live configuration update, schema migration, real PostgreSQL connection or real review collection was performed.
- No real Chrome launch or public HTTPS proxy tunnelling was rerun; the existing native smoke/matrix/worker evidence is separate from these fixture regression tests.
- UI coverage is unit/widget/static analysis/build coverage, not a live browser end-to-end deployment test.
- A process killed before it produces a valid payload can only yield the safe parent timeout/exit code; the patch does not fabricate missing Chrome evidence. An expired/cancelled job before evidence is associated with its result can still have only a generic status; this review guarantees propagation when the structured result or owned verified snapshot is available, not recovery of an unlinked interrupted job.
- Raw diagnostic data already present in historical stored payloads are not deleted. They are filtered from the reviewed public detail/history/snapshot/export routes; direct database operators retain access to their existing data.
