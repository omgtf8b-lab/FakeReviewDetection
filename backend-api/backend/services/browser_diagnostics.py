"""Allowlisted startup evidence only. Never expose raw browser logs/messages."""

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
    return {'stage': 'startup', 'code': code,
            'exception_type': kind if kind in EXCEPTIONS else 'OtherError', 'evidence': found}
