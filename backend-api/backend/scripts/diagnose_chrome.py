"""Local, opt-in Chrome startup diagnostic. Does not visit marketplaces or access databases.

Run from backend-api/backend:
    python scripts/diagnose_chrome.py

Diagnostic files remain in a temporary directory and are not uploaded.
"""
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path


def main():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
    except ImportError as exc:
        print(json.dumps({"ok": False, "stage": "import", "error_type": type(exc).__name__}))
        return 2

    with tempfile.TemporaryDirectory(prefix="review-chrome-diagnostic-") as root:
        root_path = Path(root)
        profile = root_path / "profile"
        driver_log = root_path / "chromedriver.log"
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument(f"--user-data-dir={profile}")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-extensions")
        if os.getenv("BROWSER_BINARY"):
            options.binary_location = os.environ["BROWSER_BINARY"]
        driver = None
        try:
            with driver_log.open("w", encoding="utf-8") as log:
                service = Service(
                    executable_path=os.getenv("BROWSER_DRIVER_PATH") or None,
                    log_output=log,
                )
                if os.name == "nt":
                    service.creation_flags = subprocess.CREATE_NO_WINDOW
                driver = webdriver.Chrome(service=service, options=options)
                driver.set_page_load_timeout(10)
                driver.get("data:text/html,<title>Chrome smoke test</title><p>OK</p>")
                title = driver.title
                print(json.dumps({
                    "ok": title == "Chrome smoke test",
                    "stage": "render",
                    "title": title,
                    "system": platform.system(),
                    "browser_version": driver.capabilities.get("browserVersion"),
                    "driver_version": driver.capabilities.get("chrome", {}).get("chromedriverVersion", "").split(" ")[0],
                }, ensure_ascii=False))
                return 0 if title == "Chrome smoke test" else 1
        except Exception as exc:
            # Avoid printing the exception text: it can contain local paths or URLs.
            print(json.dumps({
                "ok": False,
                "stage": "startup_or_render",
                "error_type": type(exc).__name__,
                "system": platform.system(),
                "driver_log_tail": driver_log.read_text(encoding="utf-8", errors="replace")[-2500:]
                    if driver_log.exists() else "",
            }, ensure_ascii=False))
            return 1
        finally:
            if driver is not None:
                driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
