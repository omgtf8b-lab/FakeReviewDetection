# Read-only runtime findings and proposed deployment plan

Observed on 2026-10-22. This document is a proposal; no live `.env`, launcher, process, PostgreSQL data, review data or Windows configuration was changed.

## Evidence

1. Original native Chrome smoke test: two successful runs with Chrome/ChromeDriver 156.0.8078.47.
2. Native cumulative matrix: 14/14 browser cases PASS, plus the expected proxy rejection control PASS. Includes collector options, eager, preferences, PublicProxy configuration and backend profile location.
3. Native shared parent→worker diagnostic: PASS with matching parent Python, backend cwd and local NO_PROXY; Python 3.12.14; Chrome/driver 156.0.8078.47. This uses the same driver factory and browser-worker launcher as the diagnostic branch, with explicit binaries and separate profiles/cache. It does not test the outer collection strategy process or public HTTPS tunnelling.
4. `GET /health` on local port 8001: HTTP 200, status ok, API version 3.0.0. No database endpoint was called.
5. Two native read-only process reports agreed: listener PID 25232, Python from the Codex runtime, cwd `outputs/FakeReviewDetection/backend-api/backend`, uvicorn/main:app, port 8001, reload false, parent cmd.exe. The executable path being a Codex runtime does not prove the process has a Codex-restricted security token.

### Actual backend versus successful native worker

| Item | Running backend snapshot | Successful native worker |
|---|---|---|
| Python executable | Codex bundled Python | Same bundled Python, 3.12.14 |
| Working code directory | Running outputs copy | Separate Git checkout |
| BROWSER_BINARY | Absent | Explicit installed Chrome 156 |
| BROWSER_DRIVER_PATH | Absent | Explicit tested driver 156 |
| SE_CHROMEDRIVER | Absent | No conflicting override observed in successful run |
| SE_CACHE_PATH | work/selenium-cache | Isolated diagnostic cache |
| Installed cache executable | ChromeDriver 155.0.8059.84 | Explicit driver 156.0.8078.47 |
| Active ChromeDriver child | None at snapshot time | Successful capabilities report driver 156 |
| Parent NO_PROXY loopback | Not present | Present |
| Worker NO_PROXY loopback | Forced by the existing collector code | Forced by shared worker launcher |
| PYTHONPATH | browserdeps; aideps; pythondeps | Diagnostic browserdeps; pythondeps |

The source launcher `outputs/RUN_LOCAL_API.cmd` sets PYTHONPATH, BROWSER_TEMP_DIR and SE_CACHE_PATH and invokes uvicorn on 8001. It does not set the two binary paths. This matches the snapshot, but the snapshot's redacted parent argv does not independently prove that this exact batch file launched PID 25232.

### Selenium Manager

The running cache's executable inventory contains driver 155, while its metadata includes a driver 156.0.8078.47 record. Metadata is not proof that the corresponding executable was downloaded or selected.

A separate Selenium Manager 0.4.51 run used a copied cache, installed Chrome 156 explicitly, offline mode, disabled statistics/browser downloads and ignored PATH drivers. It returned driver 155.0.8059.84 from that isolated cache with a cache-fallback warning, exit 0. Hashes of the original cache's driver and metadata remained unchanged.

This demonstrates a fallback risk when online resolution is unavailable. **It does not prove the live backend selected driver 155.** The actual backend requests automatic discovery, may resolve/download 156 online, and had no active driver child at inspection. No product collection was triggered to force a selection.

### NO_PROXY

The existing running collector sets both NO_PROXY and no_proxy to `localhost,127.0.0.1` in its child environment before Popen. The driver session is created inside that child. Therefore the missing setting in the backend parent snapshot alone is not a demonstrated cause. The snapshot also had no uppercase HTTP_PROXY/HTTPS_PROXY/ALL_PROXY configuration. Adding NO_PROXY locally is defensive consistency; it is not a proven repair for the observed failure.

## Confirmed versus unresolved

Confirmed: native direct and worker launches with pinned 156 work; Codex tool launches fail in Crashpad even without Selenium; the live backend currently relies on automatic binary selection and has an older driver in its cache.

Unresolved: which driver a real collection attempt selected, whether the live backend inherited restrictive process permissions, and whether import-path differences affect that attempt. Its Python executable name/path does not settle those questions. No evidence here establishes a marketplace access block, and no live endpoint was tested.

## Proposed configuration — not applied

The exact live configuration file to edit after authorization is:

`outputs/FakeReviewDetection/backend-api/backend/.env`

`config.py` loads this backend-relative file with `override=False`. Existing process environment values take priority. In the observed process, both binary variables and SE_CHROMEDRIVER were absent, so no conflicting binary override was observed. A restarted process would be required to load new file values; merely editing the file cannot reconfigure PID 25232.

Proposed values, where PROJECT_ROOT is the existing local project workspace:

```dotenv
BROWSER_BINARY=C:/Program Files/Google/Chrome/Application/chrome.exe
BROWSER_DRIVER_PATH=<PROJECT_ROOT>/work/chrome-diagnostics-20261022/chromedriver156.exe
NO_PROXY=localhost,127.0.0.1
```

The exact tested driver currently resides at the second path, version 156.0.8078.47. Before durable deployment, an authorized operator should place the same verified executable in a stable, versioned, access-controlled directory and point BROWSER_DRIVER_PATH there. Do not rely on a disposable audit directory for long-term production operation. Do not delete or replace the existing 155 cache, add a global PATH entry, configure Windows-wide proxies or disable Chrome/Windows security.

The inspected driver download ZIP SHA-256 was `024ee8cafa622e31cd0c3092c7a6b3548248bde7f68317d7415408dcd03ae510`; the existing diagnostic manifest identifies its official Chrome for Testing distribution. Verify the actual executable hash before/after any future copy, rather than confusing a ZIP digest with an executable digest.

Preserve BROWSER_TEMP_DIR and SE_CACHE_PATH initially, provided the worker account can write their existing private directories. Keep SE_CHROMEDRIVER absent or deliberately aligned with the same driver; Selenium's environment override can take precedence over the requested executable. No launcher edit is necessary for the proposed backend `.env` route. If an operator chooses launcher variables instead, the alternative file is `outputs/RUN_LOCAL_API.cmd`; do not maintain conflicting values in both locations.

## Future application sequence and impact

1. Obtain authorization for the maintenance change and identify the actual launch method/account. Record current PID, health response, executable versions and only the allowlisted configuration values. Record pre-change `.env` hash; keep any full backup locally with restricted access because it contains database credentials. Never commit or upload that backup.
2. Verify the chosen driver and Chrome still match 156.0.8078.47. If Chrome has auto-updated, stop and select a compatible driver before changing configuration.
3. Set only the proposed local configuration keys. Do not change DATABASE_URL, model paths, schemas, migrations or application roles. The existing server continues with its old environment until an explicitly authorized restart.
4. The diagnostic branch's code is not installed in outputs. Do not copy only browser_collector.py: it now depends on browser_worker.py and browser_diagnostics.py; collection_strategy.py also consumes the safe code list. Review/deploy those related service files together only if a separate source deployment is authorized. No runtime source copy is part of this proposal.
5. When authorized, restart only the identified backend through its normal launcher. Expect a brief service interruption; do not terminate every python.exe or a PostgreSQL process. Do not run setup_postgres.py or seed scripts. Check startup settings before any operation that could auto-create tables; this plan does not authorize schema changes.

## Verification after an authorized application

- Read the new listener's executable/cwd and allowlisted environment. Confirm the configured binary and driver files exist and their actual versions match; confirm no conflicting SE_CHROMEDRIVER.
- Run the shared local data-HTML worker diagnostic with the same interpreter, dependency paths and effective binary settings. It isolates cache/profile paths and does not use PostgreSQL or any marketplace. Inspect safe capabilities for both versions and the parent/cwd checks. This is a post-change configuration test, not proof of public review collection.
- Check `/health` again. If diagnostics are deployed, validate allowlisted error structure using fixtures; never expose raw logs or exception messages through frontend responses.
- Only a separately authorized real collection can verify the selected driver and subsequent access to a platform. Separate startup, transport and access failures in the report.

## Rollback

If versions, health or the local worker test fail, stop rollout before any real collection. Restore only the changed BROWSER_BINARY/BROWSER_DRIVER_PATH/NO_PROXY values to their recorded original presence and values (all absent in the observed parent snapshot; independently preserve the original file state). Leave every other `.env` key untouched. If restoring a full local backup is considered, first verify no other `.env` edits occurred; otherwise merge only these keys manually.

If a future source deployment was separately performed, restore exactly its backed-up service files as one set; never substitute a single incompatible module. Restart only the backend when authorized and verify health. Keep both driver versions and caches intact. PostgreSQL, review data, Windows settings and main remain unchanged throughout rollback. Removing pinning restores previous behavior, not a guarantee that automatic resolution is healthy.

## Patch validation

The prior diagnostics commit passed all 84 backend tests on isolated SQLite. For this runtime-inspection extension, 29 focused tests passed and one TCP control was deselected after a restricted-context run hit WinError 10013. Seven new tests verify environment/argv redaction, configuration presence and observed version extraction. A broader rerun stalled in Windows asyncio socketpair creation before the first API request and was stopped; it is not reported as a passing full suite. Native process inspection succeeded twice without restarting the backend.
