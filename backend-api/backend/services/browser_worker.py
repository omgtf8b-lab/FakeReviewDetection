"""Bounded browser worker transport; never expose stdout/stderr as error details."""
import json
import os
from pathlib import Path
import subprocess
import sys
from services.browser_diagnostics import public_collection

ROOT = Path(__file__).resolve().parents[1]


class BrowserWorkerError(Exception):
    def __init__(self, code, exc=None, returncode=None):
        super().__init__(code)
        self.diagnostics = {'stage': 'worker', 'code': code}
        if exc is not None:
            kind = type(exc).__name__
            self.diagnostics['exception_type'] = kind if kind in {
                'PermissionError', 'FileNotFoundError', 'TimeoutExpired', 'OSError'} else 'OtherError'
        if isinstance(returncode, int): self.diagnostics['returncode'] = returncode


def run_worker(payload, module='services.browser_collector', timeout=65):
    # module is a trusted call-site constant, never a request parameter.
    if module not in {'services.browser_collector', 'scripts.diagnose_worker_chain'}:
        raise ValueError('Unsupported worker module')
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8',
           'NO_PROXY': 'localhost,127.0.0.1', 'no_proxy': 'localhost,127.0.0.1'}
    env.setdefault('SE_CACHE_PATH', str(ROOT/'data/browser-cache'))
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    try:
        process = subprocess.Popen([sys.executable, '-m', module, '--worker'], cwd=ROOT, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding='utf-8', creationflags=flags)
    except OSError as exc:
        raise BrowserWorkerError('worker_spawn_failed', exc) from None
    try:
        try:
            stdout, _ = process.communicate(json.dumps(payload), timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            if os.name == 'nt':
                try:
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=flags, timeout=5)
                except (OSError, subprocess.TimeoutExpired): pass
            try: process.kill()
            except OSError: pass
            try: process.communicate(timeout=5)
            except (subprocess.TimeoutExpired, OSError, UnicodeError): pass
            raise BrowserWorkerError('worker_timeout', exc) from None
        except UnicodeError:
            raise BrowserWorkerError('worker_invalid_output') from None
        except OSError as exc:
            try: process.kill()
            except OSError: pass
            raise BrowserWorkerError('worker_io_failed', exc) from None
        if process.returncode != 0:
            raise BrowserWorkerError('worker_exit_failed', returncode=process.returncode)
        try:
            data = json.loads(stdout)
            if not isinstance(data, dict) or not isinstance(data.get('reviews'), list): raise ValueError()
        except (ValueError, TypeError):
            raise BrowserWorkerError('worker_invalid_output') from None
        return public_collection(data)
    finally:
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream: stream.close()
