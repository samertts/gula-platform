#!/usr/bin/env python3
"""OWASP ZAP API Scan — GULA Platform Dynamic Security Testing

Usage:
    python zap-api-scan.py \\
        --target https://staging.gula.health \\
        --username test@example.com \\
        --password secret123

Requires:
    - ZAP running in daemon mode (zap.sh -daemon -port 8090)
    - ZAP API key configured (default: ZAP_API_KEY)
    - OpenAPI spec accessible at {target}/openapi.json
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

# ==============================================================================
# CONFIGURATION
# ==============================================================================
ZAP_API_KEY = os.environ.get("ZAP_API_KEY", "ZAP_API_KEY")
ZAP_BASE_URL = os.environ.get("ZAP_BASE_URL", "http://localhost:8090")
ZAP_API_URL = f"{ZAP_BASE_URL}/JSON"

DEFAULT_TARGET = os.environ.get("ZAP_TARGET", "https://staging.gula.health")
DEFAULT_USERNAME = os.environ.get("ZAP_USERNAME", "")
DEFAULT_PASSWORD = os.environ.get("ZAP_PASSWORD", "")

OUTPUT_DIR = Path("reports/dast")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("zap-api-scan")

# ==============================================================================
# ZAP API CLIENT
# ==============================================================================


class ZAPClient:
    """Minimal ZAP API client for DAST scanning."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"X-ZAP-API-Key": api_key})

    def _request(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        url = f"{self.base_url}/JSON/{endpoint}/"
        response = self.session.get(url, params=params, timeout=120)
        response.raise_for_status()
        return response.json()

    def _request_action(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        url = f"{self.base_url}/JSON/{endpoint}/"
        response = self.session.post(url, params=params, timeout=120)
        response.raise_for_status()
        return response.json()

    def open_url(self, url: str) -> dict:
        return self._request_action("core/action/openUrl", {"url": url})

    def spider(self, context_name: str = "", max_children: int = 50) -> str:
        params = {"contextName": context_name, "maxChildren": str(max_children)}
        result = self._request_action("spider/action/scan", params)
        return result.get("scan", "")

    def spider_ajax(self, context_name: str = "") -> str:
        params: dict[str, Any] = {"contextName": context_name}
        result = self._request_action("ajaxSpider/action/scan", params)
        return result.get("scan", "")

    def active_scan(self, context_name: str = "") -> str:
        params: dict[str, Any] = {"contextName": context_name}
        result = self._request_action("ascan/action/scan", params)
        return result.get("scan", "")

    def import_openapi(self, url: str) -> dict:
        return self._request_action("openapi/action/importUrl", {"url": url})

    def set_context(self, context_id: str, include_paths: list[str]) -> dict:
        for path in include_paths:
            self._request_action(
                "context/action/includeInContext",
                {"contextName": context_id, "regex": path},
            )
        return {"success": True}

    def create_user(self, context_id: str, username: str) -> str:
        result = self._request_action(
            "authentication/action/setAuthenticationMethod",
            {
                "contextId": context_id,
                "authMethodName": "formBasedAuthentication",
                "authMethodConfigParams": (
                    f"loginUrl={DEFAULT_TARGET}/api/login&"
                    f"loginRequestData=email%3D%7B%25username%25%7D%26"
                    f"password%3D%7B%25password%25%7D"
                ),
            },
        )
        result = self._request_action(
            "authentication/action/setLoggedInIndicator",
            {
                "contextId": context_id,
                "loggedInIndicator": r"\Qaccess_token\E",
            },
        )
        result = self._request_action(
            "users/action/newUser",
            {
                "contextId": context_id,
                "name": username,
            },
        )
        user_id = result.get("userId", "")
        self._request_action(
            "users/action/setAuthenticationCredentials",
            {
                "contextId": context_id,
                "userId": user_id,
                "authCredentialsConfigParams": (
                    f"username={DEFAULT_USERNAME}&password={DEFAULT_PASSWORD}"
                ),
            },
        )
        self._request_action(
            "users/action/setUserEnabled",
            {"contextId": context_id, "userId": user_id, "enabled": "true"},
        )
        return user_id

    def status(self, scan_type: str, scan_id: str) -> int:
        result = self._request(f"{scan_type}/view/status", {"scanId": scan_id})
        return int(result.get("status", 0))

    def alerts(self, risk: str = "") -> list[dict]:
        params: dict[str, Any] = {}
        if risk:
            params["riskId"] = risk
        result = self._request("alert/view/alerts", params)
        return result.get("alerts", [])

    def alert_summary(self) -> list[dict]:
        result = self._request("alert/view/alertsSummary")
        return result.get("alertsSummary", [])

    def generate_report(self, format: str = "html") -> bytes:
        url = f"{self.base_url}/OTHER/core/other/htmlreport/"
        response = self.session.get(url, timeout=300)
        return response.content

    def generate_sarif_report(self) -> bytes:
        url = f"{self.base_url}/OTHER/core/other/sarifreport/"
        response = self.session.get(url, timeout=300)
        return response.content

    def shutdown(self) -> None:
        try:
            self._request_action("core/action/shutdown")
        except Exception:
            pass


# ==============================================================================
# SCAN RUNNER
# ==============================================================================


class ZAPScanRunner:
    """Orchestrates the full DAST scan process."""

    def __init__(self, target: str, username: str = "", password: str = ""):
        self.target = target.rstrip("/")
        self.username = username or DEFAULT_USERNAME
        self.password = password or DEFAULT_PASSWORD
        self.context_id = "gula-platform-scan"
        self.zap = ZAPClient(ZAP_API_URL, ZAP_API_KEY)
        self.results: dict[str, Any] = {}
        self.passed = False

    def run(self) -> bool:
        """Execute the full scan pipeline."""
        logger.info("=" * 60)
        logger.info("GULA Platform DAST Scan")
        logger.info(f"Target: {self.target}")
        logger.info("=" * 60)

        try:
            self._initialize()
            self._import_openapi()
            self._authenticate()
            self._spider()
            self._active_scan()
            self._analyze_results()
            self._generate_reports()
            self._shutdown()
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            self.passed = False
            raise
        finally:
            self._print_summary()

        return self.passed

    def _initialize(self) -> None:
        logger.info("Initializing ZAP session...")
        self.zap._request_action(
            "core/action/newSession",
            {"name": "gula-scan", "overwrite": "true"},
        )

    def _import_openapi(self) -> None:
        logger.info("Importing OpenAPI specification...")
        spec_url = urljoin(self.target, "/openapi.json")
        result = self.zap.import_openapi(spec_url)
        logger.info(f"OpenAPI import result: {result}")

    def _authenticate(self) -> None:
        logger.info("Setting up authentication context...")
        self.zap.create_user(self.context_id, self.username)
        logger.info("Authentication configured")

    def _spider(self) -> None:
        logger.info("Running traditional spider...")
        scan_id = self.zap.spider(self.context_id)
        self._wait_for_completion("spider", scan_id, "Spider")

        logger.info("Running AJAX spider...")
        self.zap.spider_ajax(self.context_id)
        self._wait_for_ajax_spider()

    def _active_scan(self) -> None:
        logger.info("Running active scan...")
        scan_id = self.zap.active_scan(self.context_id)
        self._wait_for_completion("ascan", scan_id, "Active Scan")

    def _wait_for_completion(self, scan_type: str, scan_id: str, label: str) -> None:
        logger.info(f"Waiting for {label} to complete...")
        progress = 0
        while progress < 100:
            progress = self.zap.status(scan_type, scan_id)
            sys.stdout.write(f"\r  {label}: {progress}%")
            sys.stdout.flush()
            time.sleep(5)
        print()
        logger.info(f"{label} completed")

    def _wait_for_ajax_spider(self) -> None:
        logger.info("Waiting for AJAX spider to complete...")
        while True:
            result = self.zap._request("ajaxSpider/view/status")
            status = result.get("status", "stopped")
            sys.stdout.write(f"\r  AJAX Spider: {status}")
            sys.stdout.flush()
            if status == "stopped":
                break
            time.sleep(5)
        print()
        logger.info("AJAX spider completed")

    def _analyze_results(self) -> None:
        logger.info("Analyzing scan results...")
        alert_summary = self.zap.alert_summary()
        alerts = self.zap.alerts()

        high_count = 0
        medium_count = 0
        low_count = 0
        info_count = 0

        for alert in alert_summary:
            risk = alert.get("risk", "").lower()
            count = int(alert.get("count", 0))
            if risk == "high":
                high_count = count
            elif risk == "medium":
                medium_count = count
            elif risk == "low":
                low_count = count
            elif risk == "info":
                info_count = count

        self.results = {
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
            "info": info_count,
            "total": high_count + medium_count + low_count + info_count,
            "alerts": alerts,
        }

        logger.info(f"  High:   {high_count}")
        logger.info(f"  Medium: {medium_count}")
        logger.info(f"  Low:    {low_count}")
        logger.info(f"  Info:   {info_count}")

        # Pass/Fail evaluation
        if high_count > 0:
            logger.error(f"FAILED: {high_count} HIGH severity alerts (max 0)")
            self.passed = False
        elif medium_count > 5:
            logger.warning(f"WARNING: {medium_count} MEDIUM alerts (max 5)")
            self.passed = False
        else:
            logger.info("PASSED: All security criteria met")
            self.passed = True

    def _generate_reports(self) -> None:
        logger.info("Generating reports...")

        # HTML report
        html_report = self.zap.generate_report("html")
        html_path = OUTPUT_DIR / "zap-report.html"
        html_path.write_bytes(html_report)
        logger.info(f"HTML report: {html_path}")

        # SARIF report
        sarif_report = self.zap.generate_sarif_report()
        sarif_path = OUTPUT_DIR / "zap-report.sarif"
        sarif_path.write_bytes(sarif_report)
        logger.info(f"SARIF report: {sarif_path}")

        # JSON report
        json_path = OUTPUT_DIR / "zap-report.json"
        with open(json_path, "w") as f:
            json.dump(self.results["alerts"], f, indent=2, default=str)
        logger.info(f"JSON report: {json_path}")

        # Markdown summary
        md_path = OUTPUT_DIR / "zap-report.md"
        self._generate_markdown_report(md_path)
        logger.info(f"Markdown report: {md_path}")

    def _generate_markdown_report(self, path: Path) -> None:
        with open(path, "w") as f:
            f.write("# GULA Platform DAST Scan Report\n\n")
            f.write(f"**Target:** {self.target}\n")
            f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Result:** {'PASS' if self.passed else 'FAIL'}\n\n")
            f.write("## Alert Summary\n\n")
            f.write("| Severity | Count | Threshold | Status |\n")
            f.write("|----------|-------|-----------|--------|\n")
            high_status = "FAIL" if self.results["high"] > 0 else "PASS"
            med_status = "FAIL" if self.results["medium"] > 5 else "PASS"
            f.write(f"| High | {self.results['high']} | 0 | {high_status} |\n")
            f.write(f"| Medium | {self.results['medium']} | <=5 | {med_status} |\n")
            f.write(f"| Low | {self.results['low']} | N/A | INFO |\n")
            f.write(f"| Info | {self.results['info']} | N/A | INFO |\n\n")

            if self.results["alerts"]:
                f.write("## Alerts\n\n")
                for alert in self.results["alerts"][:50]:  # Top 50
                    risk = alert.get("risk", "Unknown")
                    name = alert.get("alert", "Unknown")
                    url = alert.get("url", "")
                    desc = alert.get("description", "")
                    f.write(f"### [{risk}] {name}\n\n")
                    f.write(f"- **URL:** {url}\n")
                    f.write(f"- **Description:** {desc[:200]}...\n\n")

    def _print_summary(self) -> None:
        logger.info("=" * 60)
        logger.info("SCAN COMPLETE")
        logger.info(f"Result: {'PASSED' if self.passed else 'FAILED'}")
        logger.info(f"High alerts: {self.results.get('high', 0)}")
        logger.info(f"Medium alerts: {self.results.get('medium', 0)}")
        logger.info(f"Reports: {OUTPUT_DIR}/")
        logger.info("=" * 60)

    def _shutdown(self) -> None:
        logger.info("Shutting down ZAP...")
        try:
            self.zap.shutdown()
        except Exception:
            pass


# ==============================================================================
# CLI ENTRYPOINT
# ==============================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GULA Platform OWASP ZAP API DAST Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python zap-api-scan.py --target https://staging.gula.health
  python zap-api-scan.py --target http://localhost:8000 --username admin@test.com --password test123
        """,
    )
    parser.add_argument(
        "--target",
        default=DEFAULT_TARGET,
        help=f"Target base URL (default: {DEFAULT_TARGET})",
    )
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="Login username")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Login password")
    parser.add_argument("--zap-url", default=ZAP_BASE_URL, help="ZAP daemon URL")
    parser.add_argument("--zap-api-key", default=ZAP_API_KEY, help="ZAP API key")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Report output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Update global config from args
    global ZAP_BASE_URL, OUTPUT_DIR
    ZAP_BASE_URL = args.zap_url
    OUTPUT_DIR = Path(args.output_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    runner = ZAPScanRunner(
        target=args.target,
        username=args.username,
        password=args.password,
    )

    success = runner.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
