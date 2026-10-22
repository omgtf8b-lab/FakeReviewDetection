"""Opt-in local HTML matrix. No backend/config/DB imports or marketplace requests.

Run from a normal terminal, with explicit BROWSER_BINARY/BROWSER_DRIVER_PATH:
python scripts/diagnose_collector_matrix.py --output-dir PATH
Each case runs in its own bounded subprocess and fresh profile. PublicProxy's
destination resolver is replaced by a deny-all guard for this diagnostic only.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

BACKEND = Path(__file__).resolve().parents[1]
HTML = 'data:text/html,<title>Collector local test</title><p id="result">OK</p>'
FLAGS = ['--disable-gpu', '--disable-background-networking', '--disable-sync',
         '--disable-default-apps', '--disable-quic', '--autoplay-policy=user-gesture-required']
PREFS = {'profile.managed_default_content_settings.images': 2, 'credentials_enable_service': False}


def cases():
    spec = {'flags': ['--headless=new', '--no-first-run', '--disable-extensions'],
            'strategy': 'normal', 'prefs': False, 'proxy': False,
            'bypass': False, 'profile_location': 'audit', 'no_window': True}
    result = []
    def add(name):
        result.append({'name': name, **spec, 'flags': list(spec['flags'])})
    add('00_baseline')
    spec['flags'].remove('--disable-extensions'); add('01_remove_explicit_disable_extensions')
    spec['strategy'] = 'eager'; add('02_eager')
    for n, flag in enumerate(FLAGS, 3):
        spec['flags'].append(flag); add(f'{n:02d}_{flag[2:].split("=")[0]}')
    spec['prefs'] = True; add('09_collector_prefs')
    spec['proxy'] = True; add('10_public_proxy')
    spec['bypass'] = True; add('11_force_loopback_through_proxy')
    spec['profile_location'] = 'backend'; add('12_backend_profile_location')
    spec['no_window'] = False; add('13_service_default_creation_flags')
    return result


def proxy_module():
    # Load this standalone module without importing the application or dotenv.
    spec = importlib.util.spec_from_file_location('local_matrix_proxy', BACKEND/'services/browser_proxy.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    def deny_all(host, port):
        raise ValueError('Diagnostic permits no upstream destinations')
    module.public_addresses = deny_all
    return module


def evidence(text):
    # Return only allowlisted categories: never log tails, cookies or exception messages.
    rules = {'crashpad_pipe_ended': 'TransactNamedPipe',
             'crashpad_self_termination': 'crash server failed to launch',
             'devtools_port_missing': "DevToolsActivePort file doesn't exist",
             'driver_version_mismatch': 'only supports Chrome version',
             'access_denied': 'Access is denied',
             'chrome_crashed': 'Chrome failed to start: crashed'}
    return [key for key, marker in rules.items() if marker in text]


def child(case, root):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from contextlib import ExitStack
    run = root/case['name']; run.mkdir()
    profile_base = run if case['profile_location'] == 'audit' else BACKEND/'data/browser-temp'
    profile_base.mkdir(parents=True, exist_ok=True)
    profile = profile_base/('matrix-'+uuid.uuid4().hex)
    profile.mkdir(); (profile/'write-check.txt').write_text('local diagnostic', encoding='utf-8')
    raw = run/'driver-private.tmp'
    result = {'case': case['name'], 'stage': 'startup', 'profile_write_ok': True}
    driver = None
    try:
        with ExitStack() as stack:
            proxy = stack.enter_context(proxy_module().PublicProxy()) if case['proxy'] else None
            options = webdriver.ChromeOptions(); options.page_load_strategy = case['strategy']
            options.binary_location = os.environ['BROWSER_BINARY']
            for flag in case['flags'] + [f'--user-data-dir={profile}']:
                options.add_argument(flag)
            if proxy: options.add_argument(f'--proxy-server={proxy}')
            if case['bypass']: options.add_argument('--proxy-bypass-list=<-loopback>')
            if case['prefs']: options.add_experimental_option('prefs', PREFS)
            service = Service(executable_path=os.environ['BROWSER_DRIVER_PATH'],
                              log_output=str(raw), service_args=['--verbose'])
            if os.name == 'nt' and case['no_window']: service.creation_flags = subprocess.CREATE_NO_WINDOW
            try:
                driver = webdriver.Chrome(service=service, options=options)
                result['stage'] = 'render'; driver.set_page_load_timeout(10)
                driver.get(HTML)
                result.update(status='PASS' if driver.title == 'Collector local test' else 'FAIL',
                              browser_version=driver.capabilities.get('browserVersion'),
                              driver_version=driver.capabilities.get('chrome', {}).get('chromedriverVersion', '').split(' ')[0])
            finally:
                if driver is not None:
                    try: driver.quit()
                    except Exception as exc: result['cleanup_exception'] = type(exc).__name__
    except Exception as exc:
        result.update(status='FAIL', exception_type=type(exc).__name__, evidence=evidence(str(exc)))
    finally:
        if raw.exists():
            text = raw.read_text(encoding='utf-8', errors='replace')
            result['evidence'] = sorted(set(result.get('evidence', []) + evidence(text)))
            # Persist categories only, not raw ChromeDriver requests or capabilities.
            (run/'chromedriver-sanitized.json').write_text(json.dumps({'evidence': result['evidence']}), encoding='utf-8')
            raw.unlink()
    (run/'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    return 0 if result.get('status') == 'PASS' else 1


def proxy_control():
    import http.client
    from urllib.parse import urlsplit
    with proxy_module().PublicProxy() as address:
        p = urlsplit(address)
        conn = http.client.HTTPConnection(p.hostname, p.port, timeout=3)
        conn.request('GET', 'http://127.0.0.1/local-test')
        get = conn.getresponse().status; conn.close()
        conn = http.client.HTTPConnection(p.hostname, p.port, timeout=3)
        conn.request('CONNECT', '127.0.0.1:443')
        connect = conn.getresponse().status; conn.close()
    return {'case': 'proxy_local_destination_guard', 'status': 'PASS' if (get, connect) == (403, 403) else 'FAIL',
            'http_status': get, 'connect_status': connect, 'expected': 'local upstream denied, not render failure'}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output-dir', required=True)
    parser.add_argument('--case'); args = parser.parse_args()
    root = Path(args.output_dir).resolve()
    if args.case:
        return child(next(c for c in cases() if c['name'] == args.case), root)
    for key in ('BROWSER_BINARY', 'BROWSER_DRIVER_PATH'):
        if not os.environ.get(key) or not Path(os.environ[key]).is_file():
            parser.error(f'{key} must name an existing local file (no automatic download)')
    root.mkdir(parents=True, exist_ok=False)
    (root/'plan.json').write_text(json.dumps(cases(), indent=2), encoding='utf-8')
    results = [proxy_control()]
    env = {**os.environ, 'NO_PROXY': 'localhost,127.0.0.1', 'no_proxy': 'localhost,127.0.0.1',
           'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'}
    for case in cases():
        command = [sys.executable, '-B', str(Path(__file__).resolve()), '--output-dir', str(root), '--case', case['name']]
        process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        try:
            stdout, _ = process.communicate(timeout=40)
            result = json.loads(stdout)
        except subprocess.TimeoutExpired:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else: process.kill()
            process.communicate()
            result = {'case': case['name'], 'status': 'FAIL', 'exception_type': 'TimeoutExpired'}
        except ValueError:
            result = {'case': case['name'], 'status': 'FAIL', 'exception_type': 'WorkerOutputError'}
        results.append(result); print(json.dumps(result), flush=True)
    (root/'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    return int(any(r['status'] != 'PASS' for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
