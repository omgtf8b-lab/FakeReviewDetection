import json
from pathlib import Path
import pytest
from services.browser_diagnostics import startup_failure


@pytest.mark.parametrize('message,code', [
    ('crash server failed to launch, self-terminating', 'chrome_crashpad_failed'),
    ('This version only supports Chrome version 155', 'driver_version_mismatch'),
    ('user data directory is already in use', 'profile_in_use'),
    ('Access is denied', 'browser_permission_denied'),
    ('no chrome binary at private path', 'chrome_binary_missing'),
    ('Chrome failed to start: crashed', 'chrome_start_crashed'),
    ("DevToolsActivePort file doesn't exist", 'browser_start_unknown'),
])
def test_startup_classifier(message, code, tmp_path):
    assert startup_failure(RuntimeError(message), tmp_path/'missing')['code'] == code


def test_raw_secrets_paths_and_arbitrary_exception_names_are_never_returned(tmp_path):
    log = tmp_path/'driver.log'
    secret = 'synthetic-secret-never-returned'
    log.write_text('Cookie: '+secret+' Authorization: Bearer '+secret+' C:/Users/private/profile\n'
                   'TransactNamedPipe: The pipe has been ended.\ncrash server failed to launch', encoding='utf-8')
    custom = type(secret, (Exception,), {})
    result = startup_failure(custom(secret), log)
    assert result['code'] == 'chrome_crashpad_failed'
    assert result['exception_type'] == 'OtherError'
    assert secret not in json.dumps(result) and 'C:/' not in json.dumps(result)


def test_permission_error_is_not_misreported_as_platform_blocking(tmp_path):
    result = startup_failure(PermissionError('private'), tmp_path/'missing')
    assert result['code'] == 'browser_permission_denied'


def test_worker_failure_exposes_only_safe_diagnostics(monkeypatch, tmp_path):
    from contextlib import nullcontext
    from selenium import webdriver
    from selenium.common.exceptions import SessionNotCreatedException
    from services import browser_collector, browser_proxy
    monkeypatch.setenv('BROWSER_TEMP_DIR', str(tmp_path))
    monkeypatch.setattr(browser_proxy, 'PublicProxy', lambda: nullcontext('http://127.0.0.1:1234'))
    captured = {}
    def fail(*, service, options):
        captured['args'] = service.service_args
        # ChromiumService maps a string log_output to the driver's --log-path.
        path = next(a.split('=', 1)[1] for a in service.service_args if a.startswith('--log-path='))
        Path(path).write_text('crash server failed to launch\nCookie: synthetic-private\n', encoding='utf-8')
        raise SessionNotCreatedException('synthetic-private')
    monkeypatch.setattr(webdriver, 'Chrome', fail)
    result = browser_collector.worker({'url': 'https://shopee.vn/product/123/456'})
    assert result['collection_status'] == 'browser_start_failed'
    assert result['diagnostics']['code'] == 'chrome_crashpad_failed'
    assert 'synthetic-private' not in json.dumps(result)
    assert '--verbose' not in captured['args']
    assert '--log-level=WARNING' in captured['args']
    assert not list(tmp_path.glob('collector-*'))


def test_fallback_preserves_allowlisted_diagnostic_code_only(monkeypatch):
    from services import collection_strategy
    base = {'platform': 'shopee', 'url': 'https://shopee.vn/product/123/456', 'product': {}, 'reviews': []}
    monkeypatch.setattr(collection_strategy, 'collect_browser', lambda *a: {
        **base, 'collection_status': 'browser_start_failed',
        'diagnostics': {'code': 'chrome_crashpad_failed', 'raw': 'synthetic-private'}})
    monkeypatch.setattr(collection_strategy, 'collect_http', lambda *a: {
        **base, 'product': {'name': 'fixture'}, 'collection_status': 'network_error'})
    result = collection_strategy.collect(base['url'])
    assert result['attempts'][0]['diagnostic_code'] == 'chrome_crashpad_failed'
    assert 'synthetic-private' not in json.dumps(result)
