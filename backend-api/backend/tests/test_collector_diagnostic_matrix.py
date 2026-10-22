"""Standalone diagnostics tests: no app imports, database or external requests."""
import ast
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('collector_matrix', ROOT/'scripts/diagnose_collector_matrix.py')
matrix = importlib.util.module_from_spec(spec); spec.loader.exec_module(matrix)


def test_cumulative_matrix_matches_collector_flags_and_prefs():
    plans = matrix.cases()
    assert len(plans) == 14
    final = plans[-2]
    tree = ast.parse((ROOT/'services/browser_collector.py').read_text(encoding='utf-8'))
    worker = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_create_driver')
    flags = next(n.iter for n in ast.walk(worker) if isinstance(n, ast.For) and isinstance(n.iter, ast.List))
    literals = {n.value for n in flags.elts if isinstance(n, ast.Constant)}
    assert set(final['flags']) == literals - {'--proxy-bypass-list=<-loopback>'}
    assert final['proxy'] and final['bypass'] and final['prefs'] and final['no_window']
    assert final['profile_location'] == 'backend' and final['strategy'] == 'eager'
    prefs = next(n.args[1] for n in ast.walk(worker) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == 'add_experimental_option')
    assert matrix.PREFS == ast.literal_eval(prefs)


def test_proxy_control_blocks_local_destinations_without_network_upstream():
    result = matrix.proxy_control()
    assert result['status'] == 'PASS'
    assert (result['http_status'], result['connect_status']) == (403, 403)


def test_diagnostic_proxy_denies_even_public_hosts_without_dns(monkeypatch):
    module = matrix.proxy_module()
    monkeypatch.setattr(module.socket, 'getaddrinfo', lambda *a, **k: pytest.fail('No DNS permitted'))
    with pytest.raises(ValueError): module.public_addresses('example.com', 443)


def test_evidence_never_returns_raw_secrets_or_paths():
    raw = 'Authorization: Bearer synthetic-secret Cookie: synthetic-cookie C:/Users/private/path '
    raw += 'TransactNamedPipe: The pipe has been ended. crash server failed to launch'
    assert matrix.evidence(raw) == ['crashpad_pipe_ended', 'crashpad_self_termination']
    assert matrix.evidence('unrecognized exception with synthetic-secret') == []


def test_local_html_and_plan_contain_no_marketplace_navigation():
    assert matrix.HTML.startswith('data:text/html,')
    assert all(not any(x in str(c) for x in ('shopee.vn', 'lazada.vn', 'tiktok.com')) for c in matrix.cases())
