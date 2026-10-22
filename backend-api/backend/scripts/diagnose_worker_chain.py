"""Same parent transport and Chrome factory as collector; fixed local HTML only."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from services.browser_worker import run_worker, BrowserWorkerError

HTML = 'data:text/html,<title>Collector worker chain</title><p>OK</p>'


def local_worker(payload):
    from services.browser_collector import _create_driver
    from services import browser_proxy
    from services.browser_diagnostics import startup_failure
    def deny_all(*args): raise ValueError('No upstream permitted in local diagnostic')
    browser_proxy.public_addresses = deny_all
    base = Path(os.environ['BROWSER_TEMP_DIR']); base.mkdir(parents=True, exist_ok=True)
    result = {'reviews': [], 'ok': False, 'collection_status': 'diagnostic_failed',
              'python_matches_parent': sys.executable == payload['expected_python'],
              'cwd_matches_backend': Path.cwd().resolve() == ROOT,
              'no_proxy_is_local': os.environ.get('NO_PROXY') == 'localhost,127.0.0.1',
              'explicit_binary': bool(os.getenv('BROWSER_BINARY')),
              'explicit_driver': bool(os.getenv('BROWSER_DRIVER_PATH')),
              'python_version': sys.version.split()[0], 'stage': 'startup'}
    with browser_proxy.PublicProxy() as proxy, tempfile.TemporaryDirectory(
            prefix='collector-', dir=base, ignore_cleanup_errors=True) as profile:
        driver = None
        try:
            driver = _create_driver(profile, proxy)
            result['stage'] = 'render'; driver.set_page_load_timeout(10)
            driver.get(HTML)
            result.update(ok=driver.title == 'Collector worker chain',
                browser_version=driver.capabilities.get('browserVersion'),
                driver_version=driver.capabilities.get('chrome', {}).get('chromedriverVersion', '').split(' ')[0])
            result['collection_status'] = 'diagnostic_pass' if result['ok'] else 'diagnostic_failed'
        except Exception as exc:
            result['diagnostics'] = startup_failure(exc, Path(profile)/'chromedriver-startup.log')
            result['diagnostics']['stage'] = result['stage']
        finally:
            if driver is not None:
                try: driver.quit()
                except Exception: result['cleanup_failed'] = True; result['ok'] = False
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--worker', action='store_true')
    parser.add_argument('--output-dir'); args = parser.parse_args()
    if args.worker:
        print(json.dumps(local_worker(json.load(sys.stdin))), flush=True); return 0
    if not args.output_dir: parser.error('--output-dir is required')
    root = Path(args.output_dir).resolve(); root.mkdir(parents=True, exist_ok=False)
    for key in ('BROWSER_BINARY', 'BROWSER_DRIVER_PATH'):
        if not os.environ.get(key) or not Path(os.environ[key]).is_file():
            parser.error(f'{key} must point to an existing local file')
    # Deliberate path isolation only: preserve the parent launch algorithm, not live caches.
    os.environ['BROWSER_TEMP_DIR'] = str(root/'profiles')
    os.environ['SE_CACHE_PATH'] = str(root/'selenium-cache')
    try:
        result = run_worker({'expected_python': sys.executable}, module='scripts.diagnose_worker_chain')
    except BrowserWorkerError as exc:
        result = {'ok': False, 'diagnostics': exc.diagnostics}
    (root/'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    return 0 if result.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(main())
