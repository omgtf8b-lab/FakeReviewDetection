import json
import sys
import pytest
from services import browser_worker as runner


class Process:
    stdin = stdout = stderr = None
    pid = 987654321  # Synthetic only; never use real taskkill in tests.
    def __init__(self, output='{"reviews":[]}', code=0):
        self.output = output; self.returncode = code; self.killed = False
    def communicate(self, *args, **kwargs): return self.output, 'synthetic-private-stderr'
    def kill(self): self.killed = True


def test_worker_launch_preserves_interpreter_cwd_and_safe_environment(monkeypatch):
    captured = {}
    def popen(command, **kwargs):
        captured.update(command=command, **kwargs); return Process()
    monkeypatch.setattr(runner.subprocess, 'Popen', popen)
    monkeypatch.setenv('PYTHONPATH', 'synthetic-dependency-path')
    monkeypatch.delenv('SE_CACHE_PATH', raising=False)
    assert runner.run_worker({'url': 'fixture'}) == {'reviews': []}
    assert captured['command'] == [sys.executable, '-m', 'services.browser_collector', '--worker']
    assert captured['cwd'] == runner.ROOT
    assert captured['env']['PYTHONPATH'] == 'synthetic-dependency-path'
    assert captured['env']['SE_CACHE_PATH'] == str(runner.ROOT/'data/browser-cache')
    assert captured['env']['NO_PROXY'] == 'localhost,127.0.0.1'


@pytest.mark.parametrize('output,code,expected', [
    ('private-invalid-json', 0, 'worker_invalid_output'),
    ('{"reviews":"invalid"}', 0, 'worker_invalid_output'),
    ('{"reviews":[]}', 2, 'worker_exit_failed')])
def test_invalid_worker_responses_do_not_leak_output(monkeypatch, output, code, expected):
    monkeypatch.setattr(runner.subprocess, 'Popen', lambda *a, **k: Process(output, code))
    with pytest.raises(runner.BrowserWorkerError) as error: runner.run_worker({})
    assert error.value.diagnostics['code'] == expected
    assert 'private' not in json.dumps(error.value.diagnostics)


def test_spawn_failure_is_structured_and_redacted(monkeypatch):
    def fail(*args, **kwargs): raise PermissionError('synthetic-private-path')
    monkeypatch.setattr(runner.subprocess, 'Popen', fail)
    with pytest.raises(runner.BrowserWorkerError) as error: runner.run_worker({})
    assert error.value.diagnostics == {'stage': 'worker', 'code': 'worker_spawn_failed', 'exception_type': 'PermissionError'}


def test_timeout_targets_only_the_spawned_process(monkeypatch):
    p = Process(); commands = []
    def timeout(*args, **kwargs): raise runner.subprocess.TimeoutExpired('synthetic-private', 1)
    p.communicate = timeout
    monkeypatch.setattr(runner.subprocess, 'Popen', lambda *a, **k: p)
    monkeypatch.setattr(runner.subprocess, 'run', lambda command, **kwargs: commands.append(command))
    with pytest.raises(runner.BrowserWorkerError) as error: runner.run_worker({}, timeout=1)
    assert error.value.diagnostics['code'] == 'worker_timeout' and p.killed
    if runner.os.name == 'nt': assert commands == [['taskkill', '/PID', str(p.pid), '/T', '/F']]


def test_worker_module_cannot_be_supplied_arbitrarily():
    with pytest.raises(ValueError): runner.run_worker({}, module='arbitrary')
