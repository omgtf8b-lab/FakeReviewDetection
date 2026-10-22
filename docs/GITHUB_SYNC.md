# Safe source synchronization

This branch was prepared from local `main` at `d779bd9304d1c43d101d226468f357950c54b488`. The separately running upgraded workspace was only read. No running server was restarted and no live PostgreSQL connection or migration was used during synchronization.

## Exclusions

Runtime `.env` files, credentials, cookies, browser profiles, local SQLite databases, PostgreSQL data, backups, browser captures, screenshots, collected personal reviews, caches, dependency directories and newly trained binary models are excluded. Only empty or illustrative `.env.example` templates are tracked. Demo account creation requires an explicit local `DEMO_PASSWORD`; no working demo password is published.

The original commit already contains research datasets and research outputs under root `data/` and `outputs/`. Those tracked files are preserved byte-for-byte. New runtime data is not copied into them. Ignore rules do not remove inherited tracked content from history.

The upgraded SVM artifact and optional DistilBERT weights remain outside Git. Their names, sizes and SHA-256 digests are recorded in `backend-api/backend/ml/models/ARTIFACTS.json`. The large optional checkpoint also exceeds GitHub's normal per-file limit. Never load untrusted pickle/joblib artifacts.

## Isolated verification

Backend tests must use a new disposable SQLite file, not the application's PostgreSQL URL. `tests/test_api.py` honors `TEST_DATABASE_PATH` and rejects an existing file instead of deleting it. The API suite needs a trusted compatible model through `MODEL_PATH`. Configure temporary directories outside the running workspace and disable optional external service URLs. Run from `backend-api/backend`:

```powershell
# Use a NEW directory/file on every run; never select an existing application DB.
$env:TEST_DATABASE_PATH = Join-Path $env:TEMP ("fake-review-" + [guid]::NewGuid() + ".db")
$env:APP_ENV = "test"
$env:REDIS_URL = ""
$env:ELASTICSEARCH_URL = ""
$env:FIREBASE_PROJECT_ID = ""
$env:SMTP_HOST = ""
# Set MODEL_PATH to your own trusted calibrated model before the full API suite.
python -m pytest tests -q
```

The synchronized tests use reserved example.com email addresses. Selenium strategy tests cover failure handling using controlled fixtures; passing them does not demonstrate that every marketplace can be scraped live.

React verification: `npm ci --ignore-scripts`, then `npm run build`.
Flutter verification: `flutter pub get`, `flutter analyze`, `flutter test`.

Verification performed on 2026-10-22 in the target copy:

- Backend: 61 tests passed using disposable SQLite and the trusted local calibrated SVM artifact read without copying it into Git. One Starlette/httpx deprecation warning remains.
- Imports/OpenAPI: 18 direct/library/module imports succeeded; 96 OpenAPI paths generated; missing model correctly raised HTTP 503; backend-relative model path resolved correctly. No live database startup was performed in this separate check.
- Python syntax: all tracked/candidate Python files parsed successfully.
- React: clean `npm ci --ignore-scripts --no-audit --no-fund` and production build passed. Large-bundle warning remains.
- Flutter: offline dependency resolution, `dart analyze lib test` (no issues) and 24 Flutter tests passed. Flutter tool update checks stalled in this environment; tests succeeded with `--no-version-check --no-pub --concurrency=1`.
- Safety: 217 source candidate hashes remained unchanged; inherited research data/output files had no diff. No new file exceeded 5 MB. No detected live credential or secret token in the scanned candidate/tracked text files. Pattern scanning cannot prove the absence of every possible secret.

These are isolated regression checks, not a fresh validation of live scraping, PostgreSQL migration, optional provider integrations or optional DistilBERT inference.

## Known operational issues

- `http: network_error` aggregates transport failures. DNS, connection and timeout diagnostics still need a safe, more detailed error report.
- `selenium: browser_start_failed` covers browser startup exceptions. Chrome/driver availability, process permissions and sandbox/runtime restrictions need to be checked on the deployment machine; current reporting does not reliably distinguish those causes.
- Platform blocking and bounded pagination mean collection may be partial or unavailable. Product-wide conclusions must display the actual sample size and missing evidence.
- PostgreSQL connectivity and live marketplace collection are intentionally not exercised by this source-sync verification.
- Web production bundling can warn about large chunks; this is a performance issue, not a build failure.
- Model metrics currently refer to English review classification. Vietnamese and multimodal accuracy require separately evaluated artifacts and datasets.

## Target-only safety adjustments

The running source is preserved. This branch adds secret/runtime ignore rules and model manifests, removes the live demo password from documentation/seeding, makes test database selection non-destructive, declares directly imported dotenv/Pillow dependencies, and corrects invalid pnpm build-policy values. These adjustments should be reviewed before backporting to any running workspace.
