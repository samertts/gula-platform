
import os
import json
import logging
import requests
from datetime import datetime, timedelta, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gula.monitor")

# Configuration from environment variables
BACKEND_URL = os.getenv("BASE_URL", "http://localhost:8000")
MONITORING_REPORT_PATH = "/var/log/gula/monitoring_report.json"

def get_backend_metrics():
    """Fetch metrics from the backend /metrics endpoint."""
    try:
        response = requests.get(f"{BACKEND_URL}/metrics", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch backend metrics: {e}")
        return None

def generate_daily_report():
    """Generates a daily system status report."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "report_type": "daily",
        "system_status": "UNKNOWN",
        "backend_metrics": {},
        "errors_detected": [],
        "issues_resolved": [],
        "slow_operations": [],
    }

    metrics = get_backend_metrics()
    if metrics:
        report["backend_metrics"] = metrics
        if metrics["db"]["ok"] and metrics["redis"]["ok"]:
            report["system_status"] = "UP"
        else:
            report["system_status"] = "DEGRADED"

        # Example: Detect slow operations (threshold 200ms for ping)
        if metrics["db"]["ping_ms"] > 200:
            report["slow_operations"].append("Database ping is slow")
        if metrics["redis"]["ping_ms"] > 200:
            report["slow_operations"].append("Redis ping is slow")

    # Placeholder for actual error detection from logs
    # In a real scenario, this would parse actual log files
    if report["system_status"] == "DEGRADED":
        report["errors_detected"].append("DB or Redis is not healthy")

    # Save report
    os.makedirs(os.path.dirname(MONITORING_REPORT_PATH), exist_ok=True)
    with open(MONITORING_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=4)
    logger.info(f"Daily report generated and saved to {MONITORING_REPORT_PATH}")
    return report

def generate_weekly_report():
    """Generates a weekly deep dive report (placeholder)."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "report_type": "weekly",
        "performance_summary": "N/A",
        "security_summary": "N/A",
        "stability_summary": "N/A",
    }
    # In a real implementation, this would aggregate daily reports or query a monitoring system
    logger.info("Weekly report generated (placeholder).")
    return report

if __name__ == "__main__":
    # This script can be called with arguments to specify report type
    # For simplicity, we'll just generate a daily report for now.
    generate_daily_report()

