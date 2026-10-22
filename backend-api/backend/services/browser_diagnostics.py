"""Allowlisted startup evidence only. Never expose raw browser logs/messages."""
import os
from pathlib import Path
import platform
import re

MARKERS = {
    'crashpad_pipe_ended': 'TransactNamedPipe',
    'crashpad_self_termination': 'crash server failed to launch',
    'devtools_port_missing': "DevToolsActivePort file doesn't exist",
    'driver_version_mismatch': 'only supports Chrome version',
    'profile_in_use': 'user data directory is already in use',
    'access_denied': 'Access is denied',
    'chrome_crashed': 'Chrome failed to start: crashed',
    'chrome_binary_missing': 'no chrome binary',
}
CODES = {'chrome_crashpad_failed', 'driver_version_mismatch', 'profile_in_use',
         'browser_permission_denied', 'chrome_binary_missing', 'chrome_start_crashed',
         'browser_start_unknown', 'worker_spawn_failed', 'worker_exit_failed',
         'worker_invalid_output', 'worker_timeout', 'worker_io_failed'}
EXCEPTIONS = {'SessionNotCreatedException', 'WebDriverException', 'NoSuchDriverException',
              'PermissionError', 'FileNotFoundError', 'TimeoutException'}


def collector_configuration(env=None):
    """Presence/existence only; no private paths, environment values or guesses about selection."""
    env = os.environ if env is None else env
    binary, driver = env.get('BROWSER_BINARY'), env.get('BROWSER_DRIVER_PATH')
    def exists(path):
        try: return Path(path).is_file() if path else None
        except (OSError, ValueError): return False
    return {'observed_in': 'browser_worker', 'python_version': platform.python_version(),
            'binary_requested': bool(binary), 'binary_request_exists': exists(binary),
            'driver_requested': bool(driver), 'driver_request_exists': exists(driver),
            'selenium_env_override_present': bool(env.get('SE_CHROMEDRIVER')),
            'cache_configured': bool(env.get('SE_CACHE_PATH')),
            'profile_base_configured': bool(env.get('BROWSER_TEMP_DIR')),
            'automatic_driver_requested': not driver and not env.get('SE_CHROMEDRIVER')}


def startup_failure(exc, log_path):
    text = str(exc)
    try:
        with log_path.open('rb') as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell() - 131072))
            text += '\n' + stream.read(131072).decode('utf-8', errors='replace')
    except OSError:
        pass
    found = [key for key, marker in MARKERS.items() if marker.lower() in text.lower()]
    code = 'browser_start_unknown'
    for marker, candidate in [
        ('crashpad_self_termination', 'chrome_crashpad_failed'),
        ('driver_version_mismatch', 'driver_version_mismatch'),
        ('profile_in_use', 'profile_in_use'), ('access_denied', 'browser_permission_denied'),
        ('chrome_binary_missing', 'chrome_binary_missing'), ('chrome_crashed', 'chrome_start_crashed')]:
        if marker in found:
            code = candidate; break
    if isinstance(exc, PermissionError) and code == 'browser_start_unknown':
        code = 'browser_permission_denied'
    kind = type(exc).__name__
    result = {'stage': 'startup', 'code': code,
              'exception_type': kind if kind in EXCEPTIONS else 'OtherError', 'evidence': found}
    for key, pattern in [('driver_version_from_log', r'Starting ChromeDriver (\d+\.\d+\.\d+\.\d+)'),
                         ('browser_version_from_error', r'current browser version is (\d+\.\d+\.\d+\.\d+)')]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match: result[key] = match.group(1)
    return result
