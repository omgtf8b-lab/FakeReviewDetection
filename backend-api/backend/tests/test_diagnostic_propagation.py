"""Regression coverage for public collector diagnostics and historic snapshots.

Pure tests: no browser, subprocess, network, authentication, or database.
"""
import json

from services.browser_diagnostics import public_collection, public_diagnostics
from services import collection_strategy


def test_historical_raw_debug_fields_are_removed_from_public_result():
    secret = "synthetic-private-value"
    data = {
        "platform": "lazada", "url": "https://www.lazada.vn/products/example-i123.html",
        "reviews": [], "collection_status": "browser_start_failed",
        "driver_log_tail": secret, "stderr": secret, "stdout": secret,
        "traceback": secret, "raw_log": secret, "command_line": secret,
        "environment": secret,
        "diagnostics": {
            "stage": "startup", "code": "chrome_crashpad_failed",
            "exception_type": "SessionNotCreatedException",
            "evidence": ["crashpad_self_termination", secret],
            "driver_log_tail": secret, "private_path": secret,
        },
    }
    result = public_collection(data)
    assert secret not in json.dumps(result)
    assert result["diagnostics"] == {
        "stage": "startup", "code": "chrome_crashpad_failed",
        "exception_type": "SessionNotCreatedException",
        "evidence": ["crashpad_self_termination"],
    }


def test_invalid_legacy_diagnostics_are_dropped():
    result = public_collection({
        "reviews": [], "diagnostics": {"code": "user-supplied-private-code", "path": "private"},
        "attempts": [
            {"collector": "selenium", "status": "browser_start_failed",
             "diagnostics": {"code": "invalid", "stderr": "private"},
             "diagnostic_code": "not-allowed"},
            {"collector": "evil", "status": "browser_start_failed"},
            {"collector": "http", "status": "access_restricted", "debug": "private"},
        ],
    })
    assert "diagnostics" not in result
    assert result["attempts"] == [
        {"collector": "selenium", "status": "browser_start_failed"},
        {"collector": "http", "status": "access_restricted"},
    ]
    assert "private" not in json.dumps(result)


def test_safe_attempt_diagnostics_survive_public_filter():
    diagnostics = {
        "stage": "startup", "code": "chrome_crashpad_failed",
        "evidence": ["crashpad_pipe_ended", "devtools_port_missing"],
        "configuration": {"driver_requested": False, "automatic_driver_requested": True,
                          "private_value": "synthetic-private-value"},
    }
    result = public_collection({"reviews": [], "attempts": [
        {"collector": "selenium", "status": "browser_start_failed",
         "diagnostics": diagnostics},
    ]})
    attempt = result["attempts"][0]
    assert attempt["diagnostic_code"] == "chrome_crashpad_failed"
    assert attempt["diagnostics"]["configuration"] == {
        "driver_requested": False, "automatic_driver_requested": True,
    }
    assert "synthetic-private-value" not in json.dumps(result)


def test_fallback_http_preserves_selenium_failure_diagnostics(monkeypatch):
    url = "https://shopee.vn/product/123/456"
    browser = {
        "platform": "shopee", "url": url, "product": {}, "reviews": [],
        "source": "selenium_rendered_page", "collection_status": "browser_start_failed",
        "diagnostics": {"stage": "startup", "code": "chrome_crashpad_failed",
                        "log": "synthetic-private-value"},
    }
    http = {
        "platform": "shopee", "url": url, "product": {"name": "Test product"},
        "reviews": [], "source": "public_http", "collection_status": "access_restricted",
    }
    monkeypatch.setattr(collection_strategy, "collect_browser", lambda *_: dict(browser))
    monkeypatch.setattr(collection_strategy, "collect_http", lambda *_: dict(http))
    result = collection_strategy.collect(url, mode="auto")
    assert result["source"] == "public_http"
    assert result["attempts"][0]["collector"] == "selenium"
    assert result["attempts"][0]["diagnostic_code"] == "chrome_crashpad_failed"
    assert result["attempts"][1]["collector"] == "http"
    assert result["attempts"][1]["status"] == "access_restricted"
    assert "synthetic-private-value" not in json.dumps(result)


def test_public_diagnostics_cannot_reflect_unbounded_or_unknown_values():
    result = public_diagnostics({
        "stage": "unknown", "code": "worker_timeout",
        "exception_type": "synthetic-secret",
        "returncode": 10 ** 100,
        "driver_version_from_log": "156.0.8078.47;private",
        "evidence": ["devtools_port_missing", "synthetic-secret"],
    })
    assert result == {
        "stage": "worker", "code": "worker_timeout",
        "evidence": ["devtools_port_missing"],
    }
