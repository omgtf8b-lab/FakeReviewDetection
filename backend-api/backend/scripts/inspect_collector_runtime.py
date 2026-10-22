"""Read-only listener/process inspection. Optional psutil, no backend/DB imports.

Never export complete command lines or environments. Only explicitly allowlisted
path settings and boolean flags are retained. Does not start Chrome or a worker.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import re
import shutil
import sys

PATH_KEYS = ('BROWSER_BINARY', 'BROWSER_DRIVER_PATH', 'BROWSER_TEMP_DIR',
             'SE_CACHE_PATH', 'SE_CHROMEDRIVER', 'PYTHONPATH')


def safe_path(value):
    if not value: return None
    # Configuration paths may contain spaces; URLs, credentials and tokens are never paths here.
    if len(value) > 4096 or any(x in value.lower() for x in
            ('://', '\n', '\r', 'password=', 'token=', 'ghp_', 'github_pat_', 'bearer ')):
        return '<configured; omitted>'
    parts = value.split(os.pathsep)
    return os.pathsep.join(p if Path(p).is_absolute() else '<relative path>' for p in parts)


def safe_environment(env):
    result = {key: {'present': key in env, 'nonempty': bool(env.get(key)),
                    'path': safe_path(env.get(key))} for key in PATH_KEYS}
    result['SE_DEBUG'] = {'enabled': bool(env.get('SE_DEBUG'))}
    result['proxy_environment'] = {key: bool(env.get(key)) for key in
                                 ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY')}
    local = env.get('NO_PROXY', env.get('no_proxy', '')).split(',')
    result['no_proxy_has_loopback'] = all(x in [p.strip() for p in local] for x in ('localhost', '127.0.0.1'))
    return result


def file_version(path):
    if os.name != 'nt' or not path or not Path(path).is_file(): return None
    try:
        api = ctypes.WinDLL('version', use_last_error=True)
        size = api.GetFileVersionInfoSizeW(ctypes.c_wchar_p(str(path)), None)
        if not size: return None
        buffer = ctypes.create_string_buffer(size)
        if not api.GetFileVersionInfoW(ctypes.c_wchar_p(str(path)), 0, size, buffer): return None
        pointer = ctypes.c_void_p(); length = ctypes.c_uint()
        if not api.VerQueryValueW(buffer, ctypes.c_wchar_p('\\'), ctypes.byref(pointer), ctypes.byref(length)): return None
        values = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32))
        if length.value < 24 or values[0] != 0xFEEF04BD: return None
        high, low = values[2], values[3]
        return '.'.join(str(x) for x in (high >> 16, high & 65535, low >> 16, low & 65535))
    except (OSError, ValueError): return None


def path_info(path):
    safe = safe_path(path)
    if not safe or safe.startswith('<'): return {'path': safe, 'exists': False, 'file_version': None}
    return {'path': safe, 'exists': Path(path).is_file(), 'file_version': file_version(path)}


def launch_summary(args):
    # Full argv may include credentials. Never retain arbitrary options/values.
    result = {'uvicorn_mentioned': any('uvicorn' in a.lower() for a in args),
              'main_app_mentioned': 'main:app' in args, 'reload': '--reload' in args}
    for i, arg in enumerate(args[:-1]):
        if arg == '--port' and args[i+1].isdigit(): result['port_argument'] = int(args[i+1])
    return result


def inspect_process(process):
    result = {'pid': process.pid}
    for key, function in [('python_executable', process.exe), ('working_directory', process.cwd)]:
        try: result[key] = safe_path(function())
        except Exception as exc: result[key+'_error'] = type(exc).__name__ if type(exc).__name__ in {'AccessDenied', 'NoSuchProcess'} else 'InspectionError'
    try: result['launch'] = launch_summary(process.cmdline())
    except Exception: result['launch_error'] = 'InspectionError'
    try:
        env = process.environ()
        result['environment'] = safe_environment(env)
        result['configured_binary'] = path_info(env.get('BROWSER_BINARY'))
        result['requested_driver'] = path_info(env.get('BROWSER_DRIVER_PATH'))
        result['selenium_env_override'] = path_info(env.get('SE_CHROMEDRIVER'))
        # This is only a PATH candidate, not proof of Selenium's selected driver.
        result['path_driver_candidate'] = path_info(shutil.which('chromedriver', path=env.get('PATH', '')))
        cache = env.get('SE_CACHE_PATH')
        if not cache and result.get('working_directory') and not result['working_directory'].startswith('<'):
            cache = str(Path(result['working_directory'])/'data/browser-cache')
        candidates = []
        if cache and Path(cache).is_dir():
            for p in Path(cache).glob('chromedriver/*/*/chromedriver.exe'):
                if len(candidates) >= 20: break
                candidates.append(path_info(str(p)))
        result['cache_candidates_not_selected_driver'] = candidates
        del env
    except Exception as exc:
        result['environment_error'] = type(exc).__name__ if type(exc).__name__ in {'AccessDenied', 'NoSuchProcess'} else 'InspectionError'
    try:
        result['active_driver_children'] = [path_info(p.exe()) for p in process.children(recursive=True)
                                            if 'chromedriver' in p.name().lower()]
    except Exception: result['children_error'] = 'InspectionError'
    try:
        parent = process.parent()
        if parent: result['parent'] = {'pid': parent.pid, 'executable': safe_path(parent.exe()), 'launch': launch_summary(parent.cmdline())}
    except Exception: result['parent_error'] = 'InspectionError'
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output-dir', required=True)
    args = parser.parse_args(); root = Path(args.output_dir).resolve()
    root.mkdir(parents=True, exist_ok=False)
    result = {'port': 8001, 'read_only': True, 'processes': []}
    try:
        import psutil
        listeners = {c.pid for c in psutil.net_connections(kind='tcp')
                     if c.pid and c.laddr and c.laddr.port == 8001 and c.status == psutil.CONN_LISTEN}
        result['listener_pids'] = sorted(listeners)
        result['processes'] = [inspect_process(psutil.Process(pid)) for pid in sorted(listeners)]
        if not listeners: result['visibility_note'] = 'No visible listener; this does not prove backend is stopped.'
    except Exception as exc:
        result['inspection_error'] = type(exc).__name__ if type(exc).__name__ in {'AccessDenied', 'ImportError', 'ModuleNotFoundError', 'RuntimeError'} else 'InspectionError'
    (root/'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    return 0 if result['processes'] else 1


if __name__ == '__main__': raise SystemExit(main())
