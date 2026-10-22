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
         'worker_invalid_output', 'worker_timeout', 'worker_io_failed', 'worker_execution_failed',
         'collection_spawn_failed', 'collection_exit_failed', 'collection_invalid_output',
         'collection_timeout', 'collection_io_failed'}
EXCEPTIONS = {'SessionNotCreatedException', 'WebDriverException', 'NoSuchDriverException',
              'PermissionError', 'FileNotFoundError', 'TimeoutException', 'TimeoutExpired', 'OSError', 'OtherError'}
STATUSES = {'browser_start_failed', 'browser_unavailable', 'browser_disabled', 'browser_busy',
            'browser_timeout', 'reviews_collected', 'no_accessible_reviews', 'network_error',
            'access_restricted', 'source_error', 'source_too_large', 'invalid_url', 'unsafe_address',
            'media_host_not_supported', 'unexpected_redirect', 'invalid_redirect', 'too_many_redirects',
            'unsupported_response', 'collection_timeout', 'collector_error', 'imported', 'unknown'}
VERSION = re.compile(r'\d{1,4}\.\d{1,6}\.\d{1,8}\.\d{1,6}')
CONFIG_BOOLS = {'binary_requested', 'driver_requested', 'selenium_env_override_present',
                'cache_configured', 'profile_base_configured', 'automatic_driver_requested'}


def public_diagnostics(value):
    """Strict public schema, including for old snapshots and malformed worker data."""
    if not isinstance(value, dict) or not isinstance(value.get('code'), str) or value['code'] not in CODES: return None
    code = value['code']
    stage = value.get('stage')
    if not isinstance(stage, str) or stage not in {'startup', 'worker', 'collection', 'render'}:
        stage = 'collection' if code.startswith('collection_') else 'worker' if code.startswith('worker_') else 'startup'
    result = {'stage': stage, 'code': code}
    if isinstance(value.get('exception_type'), str) and value['exception_type'] in EXCEPTIONS: result['exception_type'] = value['exception_type']
    found = value.get('evidence')
    if isinstance(found, list): result['evidence'] = [k for k in MARKERS if k in found]
    for key in ('driver_version_from_log', 'browser_version_from_error'):
        version = value.get(key)
        if isinstance(version, str) and VERSION.fullmatch(version): result[key] = version
    number = value.get('returncode')
    if type(number) is int and -(2**32) <= number <= 2**32: result['returncode'] = number
    config = value.get('configuration')
    if isinstance(config, dict):
        safe = {k: config[k] for k in CONFIG_BOOLS if type(config.get(k)) is bool}
        for key in ('binary_request_exists', 'driver_request_exists'):
            if key in config and (config[key] is None or type(config[key]) is bool): safe[key] = config[key]
        if config.get('observed_in') == 'browser_worker': safe['observed_in'] = 'browser_worker'
        version = config.get('python_version')
        if isinstance(version, str) and re.fullmatch(r'\d{1,3}\.\d{1,3}\.\d{1,3}', version): safe['python_version'] = version
        if safe: result['configuration'] = safe
    return result


def public_collection(data):
    """Filter diagnostic slots only; do not alter review/media evidence or source checksums."""
    if not isinstance(data, dict): return None
    result = dict(data)
    # Historical debug fields have no place in public collection/job responses.
    for key in ('driver_log_tail', 'stderr', 'stdout', 'traceback', 'raw_log', 'command_line', 'environment'):
        result.pop(key, None)
    if 'diagnostics' in result:
        safe = public_diagnostics(result['diagnostics'])
        if safe: result['diagnostics'] = safe
        else: result.pop('diagnostics')
    if 'attempts' in result:
        attempts = []
        raw = result['attempts']
        for item in raw[:8] if isinstance(raw, list) else []:
            if not isinstance(item, dict) or not isinstance(item.get('collector'), str) or item['collector'] not in {'selenium', 'http', 'collection'}: continue
            status = item.get('status')
            attempt = {'collector': item['collector'], 'status': status if isinstance(status, str) and status in STATUSES else 'unknown'}
            safe = public_diagnostics(item.get('diagnostics'))
            code = safe['code'] if safe else item.get('diagnostic_code')
            if isinstance(code, str) and code in CODES: attempt['diagnostic_code'] = code
            if safe: attempt['diagnostics'] = safe
            attempts.append(attempt)
        result['attempts'] = attempts
    return result


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
