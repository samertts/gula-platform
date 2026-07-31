#!/usr/bin/env python3

import json
import logging
import os
import subprocess
from datetime import UTC, datetime

import requests

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

# Thresholds for alerting
CPU_THRESHOLD = 80  # percentage
MEMORY_THRESHOLD = 80  # percentage
DISK_THRESHOLD = 90  # percentage

# Path to the autofix script
AUTOFIX_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "gula_autofix.py")

def _run_command(command: list[str]) -> tuple[bool, str]:
    """Runs a shell command and returns (success, output)."""
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=10
        )
        return True, result.stdout.strip()
    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}")
        return False, "Command not found"
    except subprocess.TimeoutExpired:
        logger.error("Command timed out: %s", " ".join(command))
        return False, "Command timed out"
    except subprocess.CalledProcessError as e:
        logger.warning("Command failed: %s\nError: %s", " ".join(command), e.stderr.strip())
        return False, e.stderr.strip()

def get_backend_metrics():
    """Fetch metrics from the backend /metrics endpoint."""
    try:
        response = requests.get(f"{BACKEND_URL}/metrics", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch backend metrics: {e}")
        return None

def get_system_resources() -> dict:
    """Fetches system-wide CPU, Memory, and Disk usage."""
    resources = {"cpu_percent": None, "memory_percent": None, "disk_percent": None}

    # Get CPU usage (using top)
    success, output = _run_command([
        "sh", "-c",
        "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'",
    ])
    if success and output.strip().replace(".", "", 1).isdigit():
        resources["cpu_percent"] = float(output.strip())

    # Get Memory usage (using free -m)
    success, output = _run_command([
        "sh", "-c",
        "free -m | awk '/Mem:/ {print $3/$2 * 100}'",
    ])
    if success and output.strip().replace(".", "", 1).isdigit():
        resources["memory_percent"] = float(output.strip())

    # Get Disk usage (using df -h for root partition)
    success, output = _run_command([
        "sh", "-c",
        "df -h / | awk '/\\// {print $5}' | sed 's/%//'",
    ])
    if success and output.strip().isdigit():
        resources["disk_percent"] = int(output.strip())

    return resources

def send_alert(message: str, severity: str = "WARNING"):
    """Sends an alert (placeholder for Telegram/Email/Slack)."""
    logger.warning(f"ALERT [{severity}]: {message}")
    # In a real implementation, this would call a webhook or send an email
    # Example: requests.post(TELEGRAM_WEBHOOK, json={"text": f"[{severity}] {message}"})

def trigger_autofix(reason: str):
    """Triggers the gula_autofix.py script to attempt a fix."""
    logger.critical(f"Critical issue detected: {reason}. Triggering auto-fix...")
    try:
        subprocess.Popen([AUTOFIX_SCRIPT_PATH])
        logger.info("Auto-fix script triggered successfully.")
    except Exception as e:
        logger.error(f"Failed to trigger auto-fix script: {e}")

def generate_daily_report():
    """Generates a daily system status report."""
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "report_type": "daily",
        "system_status": "UNKNOWN",
        "backend_metrics": {},
        "system_resources": {},
        "errors_detected": [],
        "issues_resolved": [],
        "slow_operations": [],
    }

    # Fetch Backend Metrics
    metrics = get_backend_metrics()
    if metrics:
        report["backend_metrics"] = metrics
        if metrics["db"]["ok"] and metrics["redis"]["ok"]:
            report["system_status"] = "UP"
        else:
            report["system_status"] = "DEGRADED"
            send_alert("System is DEGRADED: DB=%s, Redis=%s" % (metrics["db"]["ok"], metrics["redis"]["ok"]), "CRITICAL")
            trigger_autofix("Backend services degraded (DB/Redis issues)")

        # Detect slow operations (threshold 200ms for ping)
        if metrics["db"]["ping_ms"] > 200:
            report["slow_operations"].append("Database ping is slow")
            send_alert("Slow Database: %sms" % metrics["db"]["ping_ms"], "WARNING")
        if metrics["redis"]["ping_ms"] > 200:
            report["slow_operations"].append("Redis ping is slow")
            send_alert("Slow Redis: %sms" % metrics["redis"]["ping_ms"], "WARNING")

    # Fetch System Resources
    system_resources = get_system_resources()
    report["system_resources"] = system_resources

    if system_resources["cpu_percent"] is not None and system_resources["cpu_percent"] > CPU_THRESHOLD:
        send_alert("High CPU Usage: %.2f%%" % system_resources["cpu_percent"], "CRITICAL")
        trigger_autofix("High CPU usage detected")
    if system_resources["memory_percent"] is not None and system_resources["memory_percent"] > MEMORY_THRESHOLD:
        send_alert("High Memory Usage: %.2f%%" % system_resources["memory_percent"], "CRITICAL")
        trigger_autofix("High Memory usage detected")
    if system_resources["disk_percent"] is not None and system_resources["disk_percent"] > DISK_THRESHOLD:
        send_alert("High Disk Usage: %s%%" % system_resources["disk_percent"])
        trigger_autofix("High Disk usage detected")

    # Save report
    os.makedirs(os.path.dirname(MONITORING_REPORT_PATH), exist_ok=True)
    with open(MONITORING_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=4)
    logger.info(f"Daily report generated and saved to {MONITORING_REPORT_PATH}")
    return report

def generate_weekly_report():
    """Generates a weekly deep dive report (placeholder)."""
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "report_type": "weekly",
        "performance_summary": "N/A",
        "security_summary": "N/A",
        "stability_summary": "N/A",
    }
    # In a real implementation, this would aggregate daily reports or query a monitoring system
    logger.info("Weekly report generated (placeholder).")
    return report

if __name__ == "__main__":
    generate_daily_report()
