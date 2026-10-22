import importlib.util
import json
from pathlib import Path
import pytest
from services.browser_diagnostics import collector_configuration, startup_failure

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runtime_inspection', ROOT/'scripts/inspect_collector_runtime.py')
inspection = importlib.util.module_from_spec(spec); spec.loader.exec_module(inspection)


def test_environment_only_exports_allowlisted_settings():
    private = 'synthetic-private-value'
    result = inspection.safe_environment({'DATABASE_URL': private, 'SECRET_KEY': private,
        'HTTP_PROXY': 'https://user:'+private+'@proxy.invalid', 'COOKIE': private,
        'BROWSER_DRIVER_PATH': 'https://private.invalid/token='+private,
        'NO_PROXY': 'localhost,127.0.0.1'})
    assert private not in json.dumps(result)
    assert result['BROWSER_DRIVER_PATH']['nonempty'] is True
    assert result['no_proxy_has_loopback'] is True
    assert 'SECRET_KEY' not in result and 'DATABASE_URL' not in result


def test_launch_summary_does_not_return_arbitrary_arguments():
    result = inspection.launch_summary(['python', '-m', 'uvicorn', 'main:app', '--port', '8001', '--secret', 'synthetic-private'])
    assert result == {'uvicorn_mentioned': True, 'main_app_mentioned': True, 'reload': False, 'port_argument': 8001}


def test_configuration_records_missing_settings_without_claiming_driver_version():
    result = collector_configuration({})
    assert result['automatic_driver_requested'] is True
    assert result['driver_request_exists'] is None and result['binary_request_exists'] is None
    assert 'driver_version' not in result


def test_configuration_does_not_export_paths_or_other_values(tmp_path):
    binary = tmp_path/'synthetic-private.exe'; binary.touch()
    result = collector_configuration({'BROWSER_BINARY': str(binary), 'BROWSER_DRIVER_PATH': str(binary),
                                      'SECRET_KEY': 'synthetic-private'})
    assert result['driver_request_exists'] and result['binary_request_exists']
    assert result['automatic_driver_requested'] is False
    assert 'synthetic-private' not in json.dumps(result)


def test_override_presence_is_not_proof_that_driver_was_selected():
    result = collector_configuration({'SE_CHROMEDRIVER': 'synthetic-private'})
    assert result['selenium_env_override_present'] is True
    assert result['automatic_driver_requested'] is False
    assert 'selected_driver' not in result


def test_versions_are_observations_from_evidence_not_directory_names(tmp_path):
    log = tmp_path/'driver.log'
    log.write_text('Starting ChromeDriver 155.0.8059.84 Cookie: synthetic-private', encoding='utf-8')
    result = startup_failure(RuntimeError('current browser version is 156.0.8078.47; synthetic-private'), log)
    assert result['driver_version_from_log'] == '155.0.8059.84'
    assert result['browser_version_from_error'] == '156.0.8078.47'
    assert 'synthetic-private' not in json.dumps(result)


def test_process_inspection_never_exports_complete_environment_or_commandline(monkeypatch):
    class Process:
        pid = 123
        def exe(self): return 'python'
        def cwd(self): return 'relative-workspace'
        def cmdline(self): return ['python', '-m', 'uvicorn', 'main:app', '--secret', 'synthetic-private']
        def environ(self): return {'SECRET_KEY': 'synthetic-private'}
        def children(self, recursive): return []
        def parent(self): return None
    monkeypatch.setattr(inspection.shutil, 'which', lambda *a, **k: None)
    result = inspection.inspect_process(Process())
    assert 'synthetic-private' not in json.dumps(result)
    assert 'cmdline' not in result and 'SECRET_KEY' not in json.dumps(result)
    assert result['active_driver_children'] == []
