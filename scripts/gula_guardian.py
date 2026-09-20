#!/usr/bin/env python3
"""
GULA Guardian - Advanced Self-Healing Orchestrator
--------------------------------------------------
Complements the internal auto_repair engine by handling infrastructure-level
failures and performing deep clinical data reconciliation.

NOT CURRENTLY ACTIVE (session forensic inventory, docs/engineering/
MUSTAFA_ACTIVE_REPAIR_QUEUE.md, row "autonomous-repair-family-inventory"):
not referenced by any cron entry, systemd unit, Makefile target, or CI
workflow anywhere in this repo (exhaustively grepped). Its main() is
also a standing `while True: ...; time.sleep(300)` loop -- if this is
ever activated, convert it to a bounded, cron-triggered single-shot
invocation first ("no permanent polling daemon" is a hard requirement
this session's engineering directives establish); do not just add it to
cron as-is with the infinite loop intact.
"""

import os
import sys
import time
import logging
import subprocess
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] GULA_GUARDIAN: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gula.guardian")

BACKEND_URL = os.getenv("BASE_URL", "http://localhost:8000")
BACKEND_CONTAINER = "gula-backend"
DB_CONTAINER = "gula-postgres"

def check_backend_deep_health():
    """Queries the /health/deep endpoint for detailed component status."""
    try:
        response = requests.get(f"{BACKEND_URL}/health/deep", timeout=10)
        if response.status_code == 200:
            return True, response.json()
        return False, {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}

def restart_service(name):
    logger.warning(f"Initiating restart for {name}...")
    subprocess.run(["docker", "restart", name], check=False)

def fix_outbox_stuck():
    """Restarts the worker if the outbox backlog is growing."""
    logger.warning("Detected outbox backlog spike. Restarting background workers...")
    # In GULA, workers are often part of the backend container or a separate 'gula-worker'
    restart_service("gula-worker")
    restart_service(BACKEND_CONTAINER)

def verify_audit_chain():
    """Runs the audit_verifier script and alerts on failure."""
    logger.info("Verifying audit log integrity...")
    result = subprocess.run([sys.executable, "scripts/audit_verifier.py"], capture_output=True, text=True)
    if result.returncode != 0:
        logger.critical("AUDIT CHAIN TAMPERED OR BROKEN!")
        # In a real system, this would trigger a hardware security module (HSM) lock
        return False
    return True

def main():
    logger.info("GULA Guardian started. Monitoring platform stability...")
    
    while True:
        healthy, data = check_backend_deep_health()
        
        if not healthy:
            logger.error(f"Platform health check failed: {data.get('error')}")
            # If backend is completely down, restart it
            restart_service(BACKEND_CONTAINER)
        else:
            # Check specific components from deep health
            # Example: data['components']['outbox']['backlog'] > 500
            backlog = data.get('stats', {}).get('queue_backlog', 0)
            if backlog > 500:
                fix_outbox_stuck()
                
            # Periodic integrity check
            if not verify_audit_chain():
                # Flag system as insecure
                logger.error("System integrity compromised. Alerting administrators.")
        
        # Sleep for 5 minutes between checks to avoid resource thrashing
        time.sleep(300)

if __name__ == "__main__":
    main()
