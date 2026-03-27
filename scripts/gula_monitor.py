
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

def send_alert(message: str, severity: str = "WARNING"):
    """Sends an alert (placeholder for Telegram/Email/Slack)."""
    logger.warning(f"ALERT [{severity}]: {message}")
    # In a real implementation, this would call a webhook or send an email
    # Example: requests.post(TELEGRAM_WEBHOOK, json={"text": f"[{severity}] {message}"})

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
            send_alert(f"System is DEGRADED: DB={metrics['db']['ok']}, Redis={metrics['redis']['ok']}", "CRITICAL")

        # Detect slow operations (threshold 200ms for ping)
        if metrics["db"]["ping_ms"] > 200:
            report["slow_operations"].append("Database ping is slow")
            send_alert(f"Slow Database: {metrics['db']['ping_ms']}ms", "WARNING")
        if metrics["redis"]["ping_ms"] > 200:
            report["slow_operations"].append("Redis ping is slow")
            send_alert(f"Slow Redis: {metrics['redis']['ping_ms']}ms", "WARNING")

        # Check for high memory usage (if metrics provide it)
        # if metrics.get("memory_usage_percent", 0) > 90:
        #     send_alert("High Memory Usage detected", "CRITICAL")

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

