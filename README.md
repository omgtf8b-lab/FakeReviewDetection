# Fake Review Detection

FastAPI backend, React web client and Flutter client for collecting and examining product reviews from Shopee, Lazada and TikTok Shop. The consumer workflow accepts a product URL or supplied review/media evidence. Administrative screens expose collection jobs, stored evidence and analysis.

## Source map

- `backend-api/backend/routers/product_links.py`: product-link API.
- `backend-api/backend/services/collection_strategy.py`: HTTP/browser collection selection.
- `backend-api/backend/services/marketplaces.py`: marketplace URL handling and HTTPX collection.
- `backend-api/backend/services/browser_collector.py`, `browser_proxy.py`: Selenium worker and controlled browser access.
- `backend-api/backend/services/crawl_pipeline.py`, `review_repository.py`: collection jobs, persistence and deduplication.
- `backend-api/backend/models.py`, `extended_models.py`, `schemas.py`: relational models and API schemas.
- `frontend-web/src/pages/ProductInspector.jsx`: React product inspection workflow.
- `frontend_mobile/lib/screens/product_inspector_screen.dart`: Flutter product inspection workflow.
- `browser-reader/`: user-assisted collection tools.

## Local setup

Use Python 3.11+ and a Node version supported by the pinned Vite dependency (Node 22.12+ is suitable). Flutter requires the Dart SDK version declared in `frontend_mobile/pubspec.yaml`.

In `backend-api/backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-browser.txt
Copy-Item .env.example .env
# Set a private SECRET_KEY and your own DATABASE_URL locally.
uvicorn main:app --host 127.0.0.1 --port 8001
```

The example configuration uses SQLite. PostgreSQL can be configured through `DATABASE_URL`; never copy production credentials into committed examples. `setup_postgres.py` is a migration tool and must only be run deliberately against an authorized local database. It is not needed to review source code or run isolated tests.

Install Chrome for Selenium. Driver discovery may require network access. Optional AI, media and external provider requirements are separated into their respective requirements files. Configure external services locally only.

In `frontend-web`:

```powershell
npm ci
npm run dev -- --host 127.0.0.1
```

In `frontend_mobile`:

```powershell
flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8001
```

Check client-specific READMEs for configuration options. Do not launch a second server on a port already occupied by an existing workspace.

## Model artifacts and limitations

The upgraded classifier artifact is deliberately not committed. See `backend-api/backend/ml/models/README.md` and `ARTIFACTS.json` for provisioning and integrity information. A fresh clone can inspect collection code without it, but model inference returns HTTP 503 until a trusted compatible model is supplied. The inherited research model under root `outputs/` is not automatically substituted for the calibrated API model.

Collection is best effort. Marketplace permissions, rate limits, network failures, login gates and layout changes can prevent access. The code does not guarantee every review or bypass CAPTCHA. A suspected review is not proof of fraud or of counterfeit merchandise. The current English OR/CG classifier has not been validated for Vietnamese, teencode, emojis, image authenticity or video authenticity.

See [synchronization and safe testing](docs/GITHUB_SYNC.md) for exclusions, testing isolation and remaining issues. Historical implementation notes are in [README_UPGRADE.md](README_UPGRADE.md); consult current source and tests when those notes disagree.
