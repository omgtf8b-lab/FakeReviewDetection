# Collector startup and worker diagnostics

This change is on `fix/collector-diagnostics`, based on `a8b5c4626147c41594160e67f828ea0ee8a760cb`. It does not alter marketplace navigation, proxy restrictions, model inference or database configuration.

## Observed results (2026-10-22)

The owner ran the original Chrome smoke test twice in a normal VS Code terminal: both rendered the local HTML successfully with Chrome and ChromeDriver 156.0.8078.47, exit 0.

The separate native matrix produced 14/14 browser PASS results, plus one PASS for the proxy destination policy:

| Step | Cumulative change | Native result |
|---|---|---|
| 00 | Original smoke-test baseline | PASS |
| 01 | Remove explicit disable-extensions | PASS |
| 02 | eager page loading | PASS |
| 03–08 | Add GPU/background-network/sync/default-app/QUIC/autoplay flags individually | PASS each |
| 09 | Collector image/credential preferences | PASS |
| 10 | PublicProxy | PASS |
| 11 | Force loopback destinations through proxy | PASS |
| 12 | New profile under backend data/browser-temp | PASS |
| 13 | Default Service creation flags instead of CREATE_NO_WINDOW | PASS |
| Policy control | Local HTTP and CONNECT upstream forbidden | PASS: both 403 |

All browser cases navigated only a fixed `data:text/html` URL. The diagnostic proxy denied every upstream destination before DNS resolution. Consequently these tests verify startup/render with proxy configuration and destination rejection, **not** successful public HTTPS tunnelling or marketplace access. A 403 for a local upstream is expected security behavior, not evidence that the collector cannot start.

In the Codex execution context, both matrix baseline and full collector options failed before rendering with `SessionNotCreatedException`, `TransactNamedPipe` pipe-ended evidence and `crash server failed to launch, self-terminating`. Direct Chrome without Selenium also failed there. Changing driver to the exact matching 156 build and disabling crash reporter flags did not fix that context.

No individual tested Chrome option, profile location, Service window flag or proxy setting explains the native startup failure, because no such failure occurred in the native matrix. There is a demonstrated execution-context difference. The precise Windows restriction affecting Crashpad has not been established; pipe-ended evidence alone does not prove an ACL or antivirus cause.

## Parent → worker launch

The actual collector uses the backend's `sys.executable`, `-m services.browser_collector --worker`, backend cwd, inherited environment, forced local NO_PROXY, a default Selenium cache path, piped JSON stdin/stdout and CREATE_NO_WINDOW on Windows. The surrounding collection strategy may itself run in another bounded subprocess. A direct Chrome smoke test bypasses these launch layers.

`services/browser_worker.py` now holds the same browser child launch algorithm for both the collector and the new local diagnostic. It preserves the interpreter, cwd and environment rules. It adds structured spawn/exit/invalid-output/I/O/timeout errors and checks the exit code. Raw stderr/stdout errors are never returned to the API. The 65-second timeout still targets only the child process tree owned by that invocation.

`scripts/diagnose_worker_chain.py` exercises that shared parent transport and the exact `_create_driver` factory used by the collector (same ChromeOptions, prefs, Service and proxy flags). The worker loads only fixed local data HTML. It uses isolated cache/profile directories and a deny-all upstream proxy. It does not import the application, settings or database and does not fetch product links.

In Codex, the child confirmed matching parent interpreter, correct backend cwd and local NO_PROXY, then failed at Chrome startup with allowlisted `chrome_crashpad_failed` evidence. This demonstrates transport/import execution reached the Chrome factory; it does not imply the native child must fail.

The native parent→worker control subsequently PASSED: `ok=true`, `stage=render`, `collection_status=diagnostic_pass`, Python 3.12.14, matching parent interpreter, correct backend cwd and local NO_PROXY. Both Chrome and ChromeDriver were 156.0.8078.47. This used the same `_create_driver` factory including the new non-verbose error logging settings.

Together, the native matrix and child control rule out the shared browser launch mechanism under the pinned tested environment as a reproducible cause. They do not establish which interpreter, driver discovery settings or Windows execution token are used by an already running backend. The remaining strongest lead is an execution-environment difference: Codex fails at Crashpad even without Selenium, whereas native passes both direct and worker launches. The live service process configuration still needs comparison before asserting its original failure is fixed.

The local diagnostic does not exercise an HTTP request into the running backend or the outer `collect_bounded` strategy process. It intentionally uses explicit matching binaries and isolated cache/profile paths. Automatic driver discovery, externally inherited environment settings and the live backend process context remain unverified.

## Safe diagnostics

- Browser startup errors retain the compatible `browser_start_failed` status and add a structured `diagnostics` object with stage, allowlisted exception type, code and allowlisted evidence categories.
- Codes distinguish Crashpad self-termination, incompatible driver, profile-in-use, explicit permission failure, missing binary, generic Chrome crash and unknown startup failures. Missing DevToolsActivePort alone is not called a Crashpad failure.
- Worker errors distinguish spawn, nonzero exit, malformed response, I/O and timeout.
- Raw exception messages, command lines, profiles, cookie/token values and log tails are not returned. Browser log reading is bounded to the last 128 KiB. Logs belong to the disposable profile and are removed during normal profile cleanup; no raw artifacts are committed. Forced process termination may leave temporary diagnostic artifacts requiring normal local retention management.
- Production driver logging is not verbose. Matrix verbose logs are converted to evidence categories and deleted after each normal diagnostic case. No product reviews are used in these tests.
- The secondary HTTP fallback retains only an allowlisted diagnostic code in its Selenium attempt, so startup evidence is not silently lost when the HTTP result is selected.

## Verification

84 backend tests passed using new disposable SQLite/in-memory fixtures and a trusted existing local SVM artifact read without modifying it. This includes 23 new tests for options/prefs parity, proxy rejection without upstream requests, redaction, startup classifications, fallback preservation and worker launch/error/timeout behavior. One existing Starlette/httpx deprecation warning remains.

No live PostgreSQL connection/migration or marketplace request was used. The running workspace's collector, proxy and strategy still match their pre-change versions; all changes are confined to the Git checkout.

## Running the new diagnostic in a normal terminal

Use the same trusted Python dependencies as the backend. Set local BROWSER_BINARY and BROWSER_DRIVER_PATH to installed matching binaries and invoke:

```powershell
python backend-api/backend/scripts/diagnose_worker_chain.py --output-dir PATH_TO_A_NEW_DIAGNOSTIC_DIRECTORY
```

The output directory must not already exist. `result.json` contains only safe structured results. The diagnostic reports whether the Python executable matches the parent and cwd matches the backend, without printing private paths or inherited environment values.

Do not replace proxy guards with unrestricted local access or add no-sandbox flags based solely on these results. No anti-bot/platform-blocking conclusion follows from a local HTML startup test.
