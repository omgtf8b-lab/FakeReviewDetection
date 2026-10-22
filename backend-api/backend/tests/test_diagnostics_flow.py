"""Controlled worker/API fixtures and disposable SQLite only; no real Chrome or sàn."""
import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
import pytest
from services.browser_diagnostics import public_collection, public_diagnostics

PRIVATE = 'synthetic-private-diagnostic'


def dataset():
    return {'url': 'https://shopee.vn/product/123/456', 'platform': 'shopee', 'product': {},
            'source': 'selenium_rendered_page', 'reviews': [], 'reported_total': None,
            'collection_status': 'browser_start_failed', 'collection_message': 'Browser failed',
            'diagnostics': {'stage': 'startup', 'code': 'chrome_crashpad_failed',
                'exception_type': 'SessionNotCreatedException', 'evidence': ['crashpad_self_termination'],
                'driver_version_from_log': '156.0.8078.47', 'raw': PRIVATE,
                'configuration': {'driver_requested': True, 'profile_path': PRIVATE}}}


@pytest.mark.parametrize('bad', [None, [], 'private', {'code': []}, {'code': {}}, {'code': 'private'}])
def test_malformed_diagnostics_are_ignored(bad):
    assert public_diagnostics(bad) is None


def test_strict_types_and_bounds_never_forward_raw_diagnostic_fields():
    raw = {'code': 'chrome_crashpad_failed', 'stage': [], 'exception_type': [],
           'evidence': ['crashpad_self_termination', PRIVATE, {}], 'returncode': True,
           'driver_version_from_log': PRIVATE, 'configuration': {'driver_requested': PRIVATE, 'python_version': PRIVATE}}
    result = public_diagnostics(raw)
    assert result == {'code': 'chrome_crashpad_failed', 'stage': 'startup', 'evidence': ['crashpad_self_termination']}
    assert public_collection({'attempts': [{'collector': []}, {'collector': 'selenium', 'status': [], 'raw': PRIVATE}]}) == {
        'attempts': [{'collector': 'selenium', 'status': 'unknown'}]}


def test_worker_transport_filters_unsafe_worker_output(monkeypatch):
    from services import browser_worker
    class Process:
        stdin = stdout = stderr = None
        returncode = 0
        def communicate(self, *a, **k): return json.dumps({**dataset(), 'stderr': PRIVATE}), PRIVATE
    monkeypatch.setattr(browser_worker.subprocess, 'Popen', lambda *a, **k: Process())
    result = browser_worker.run_worker({})
    assert result['diagnostics']['code'] == 'chrome_crashpad_failed'
    assert PRIVATE not in json.dumps(result)


@pytest.mark.parametrize('exit_code,output,expected', [
    (1, '{}', 'collection_exit_failed'), (0, PRIVATE, 'collection_invalid_output')])
def test_outer_collection_transport_preserves_failure_evidence(monkeypatch, exit_code, output, expected):
    from services import collection_strategy
    class Process:
        stdin = stdout = None
        returncode = exit_code
        def communicate(self, *a, **k): return output, PRIVATE
        def wait(self, timeout): return exit_code
    monkeypatch.setattr(collection_strategy.subprocess, 'Popen', lambda *a, **k: Process())
    result = collection_strategy.collect_bounded(dataset()['url'])
    assert result['diagnostics']['code'] == expected
    assert result['attempts'][0]['diagnostics'] == result['diagnostics']
    assert PRIVATE not in json.dumps(result)


def test_outer_spawn_failure_becomes_storable_safe_result(monkeypatch):
    from services import collection_strategy
    def fail(*a, **k): raise PermissionError(PRIVATE)
    monkeypatch.setattr(collection_strategy.subprocess, 'Popen', fail)
    result = collection_strategy.collect_bounded(dataset()['url'])
    assert result['diagnostics']['code'] == 'collection_spawn_failed'
    assert result['reviews'] == [] and PRIVATE not in json.dumps(result)


def test_worker_setup_or_cleanup_exception_is_not_silently_erased(monkeypatch):
    from services import browser_collector
    def fail(*a, **k): raise PermissionError(PRIVATE)
    monkeypatch.setattr(browser_collector, 'worker', fail)
    result = browser_collector.execute_payload({'url': dataset()['url']})
    assert result['diagnostics'] == {'stage': 'worker', 'code': 'worker_execution_failed', 'exception_type': 'PermissionError'}
    assert PRIVATE not in json.dumps(result)


def test_http_first_and_successful_fallback_keep_browser_failure_details(monkeypatch):
    from services import collection_strategy
    browser = dataset()
    direct = {**dataset(), 'source': 'http_fixture', 'product': {'name': 'fixture'},
              'diagnostics': None, 'collection_status': 'network_error'}
    monkeypatch.setattr(collection_strategy, 'collect_browser', lambda *a: browser.copy())
    monkeypatch.setattr(collection_strategy, 'collect_http', lambda *a: direct.copy())
    lazada = collection_strategy.collect('https://www.lazada.vn/products/pdp-i123-s456.html')
    assert lazada['attempts'][1]['diagnostics'] == public_diagnostics(browser['diagnostics'])
    direct.update(collection_status='reviews_collected', reviews=[{'id': 'fixture', 'text': 'Review fixture'}])
    result = collection_strategy.collect(dataset()['url'])
    assert result['reviews'] and result['attempts'][0]['diagnostics'] == public_diagnostics(browser['diagnostics'])
    assert PRIVATE not in json.dumps(result)


# This existing fixture overrides all API sessions with in-memory SQLite. The
# app lifespan's independent session must also be pointed at a disposable DB by the runner.
from test_product_links import client


@pytest.fixture
def startup_failure_chain(monkeypatch, tmp_path):
    from selenium.common.exceptions import SessionNotCreatedException
    from services import browser_collector, browser_proxy, browser_worker, collection_strategy
    from routers import product_links
    monkeypatch.setenv('BROWSER_TEMP_DIR', str(tmp_path))
    monkeypatch.setattr(browser_proxy, 'PublicProxy', lambda: nullcontext('http://127.0.0.1:1234'))
    def fail(profile, proxy):
        (Path(profile)/'chromedriver-startup.log').write_text(
            'Starting ChromeDriver 156.0.8078.47\ncrash server failed to launch\nCookie: '+PRIVATE, encoding='utf-8')
        raise SessionNotCreatedException(PRIVATE)
    monkeypatch.setattr(browser_collector, '_create_driver', fail)
    class Process:
        stdin = stdout = stderr = None
        returncode = 0
        def communicate(self, payload, **kwargs):
            return json.dumps(browser_collector.worker(json.loads(payload))), PRIVATE
    monkeypatch.setattr(browser_worker.subprocess, 'Popen', lambda *a, **k: Process())
    monkeypatch.setattr(collection_strategy, 'collect_http', lambda *a: {
        **dataset(), 'source': 'http_fixture', 'diagnostics': None,
        'product': {'name': 'HTTP metadata only'}, 'collection_status': 'network_error'})
    monkeypatch.setattr(product_links, 'collect', lambda url, limit, mode='auto': collection_strategy.collect(url, limit, mode))


def assert_clean_code(value):
    assert PRIVATE not in json.dumps(value)
    attempt = value['attempts'][0]
    assert attempt['collector'] == 'selenium'
    assert attempt['diagnostics']['code'] == 'chrome_crashpad_failed'
    assert attempt['diagnostics']['driver_version_from_log'] == '156.0.8078.47'


def test_failure_flows_through_worker_fallback_api_history_and_snapshot(client, startup_failure_chain):
    import main
    from auth import get_current_user
    c, factory = client
    job = c.post('/api/product-links', json={'url': dataset()['url']}).json()
    result = c.get(f"/api/product-links/{job['id']}").json()
    assert result['status'] == 'completed'  # analysis completes with insufficient data, not a fake verdict
    assert result['result']['summary']['observed_reviews'] == 0
    assert_clean_code(result['result'])
    assert_clean_code(c.get('/api/product-links').json()[0]['result'])
    sid = result['result']['provenance']['snapshot_id']
    exported = c.get(f'/api/product-links/snapshots/{sid}').json()
    assert_clean_code(exported['dataset'])
    from services.review_repository import digest, encode
    assert exported['dataset_sha256'] == digest(encode(exported['dataset']))
    import extended_models as ex
    with factory() as db:
        row = db.get(ex.CollectionSnapshot, sid)
        assert PRIVATE not in row.payload and digest(row.payload) == row.sha256
    main.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=2, role='buyer')
    assert c.get(f"/api/product-links/{job['id']}").status_code == 404
    assert c.get(f'/api/product-links/snapshots/{sid}').status_code == 404


def test_analysis_failure_keeps_saved_diagnostics_in_failed_job(client, startup_failure_chain, monkeypatch):
    from routers import product_links
    def fail(*a, **k): raise RuntimeError(PRIVATE)
    monkeypatch.setattr(product_links, 'analyze', fail)
    c, _ = client
    job = c.post('/api/product-links', json={'url': dataset()['url']}).json()
    result = c.get(f"/api/product-links/{job['id']}").json()
    assert result['status'] == 'failed'
    assert_clean_code(result['result'])
    assert result['result']['snapshot_id']


def test_legacy_snapshot_and_job_are_filtered_without_rewriting_evidence(client):
    import extended_models as ex
    from services.review_repository import digest, encode
    c, factory = client
    raw = encode({**dataset(), 'storage_schema': 'review-rows-v1'})
    with factory() as db:
        snapshot = ex.CollectionSnapshot(user_id=1, canonical_url=dataset()['url'], platform='shopee',
            source='legacy_fixture', payload=raw, sha256=digest(raw))
        job = ex.ProductLinkAnalysis(user_id=1, url=dataset()['url'], platform='shopee', status='completed', result=raw)
        db.add_all([snapshot, job]); db.commit(); sid, jid = snapshot.id, job.id
    exported = c.get(f'/api/product-links/snapshots/{sid}').json()
    assert PRIVATE not in json.dumps(exported)
    assert exported['sha256'] == digest(raw)
    assert exported['dataset_sha256'] == digest(encode(exported['dataset']))
    assert exported['dataset_sha256'] != exported['sha256']
    assert PRIVATE not in c.get(f'/api/product-links/{jid}').text
    assert PRIVATE not in c.get('/api/product-links').text
    with factory() as db:
        assert db.get(ex.CollectionSnapshot, sid).payload == raw
        assert db.get(ex.ProductLinkAnalysis, jid).result == raw
