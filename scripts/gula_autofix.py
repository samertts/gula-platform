#!/usr/bin/env python3
"""DEPRECATED — superseded by scripts/auto_heal.sh.

Evidence (session forensic inventory, docs/engineering/
MUSTAFA_ACTIVE_REPAIR_QUEUE.md, row "autonomous-repair-family-inventory"):
this script is a strict subset of auto_heal.sh's Docker-container
health-check-and-restart logic, with no MAX_RESTARTS_PER_HOUR-style
rate-limit guard, and is not referenced by any cron entry, systemd unit,
Makefile target, or CI workflow anywhere in this repo (exhaustively
grepped) — auto_heal.sh is the real, cron-installed (scripts/
server-setup.sh), rate-limited version of this same idea.

Not deleted: per this session's own retirement policy, an unused script
is documented and guarded against accidental reactivation, not removed
outright, without an explicit human decision to do so. Do not wire this
into cron/systemd/Makefile — use scripts/auto_heal.sh instead.
"""

import logging
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gula.autofix")

BACKEND_CONTAINER = "gula-backend"
DB_CONTAINER = "gula-postgres"
DB_ERROR_PATTERNS = [
    "psycopg2.OperationalError",
    "Connection refused",
    "database_unavailable",
    "Database not ready",
    "Database unreachable",
]

def _run_docker_command(command: list[str]) -> tuple[bool, str]:
    """Runs a Docker command and returns (success, output)."""
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=30
        )
        return True, result.stdout.strip()
    except FileNotFoundError:
        logger.error("Docker command not found. Is Docker installed and in PATH?")
        return False, "Docker not found"
    except subprocess.TimeoutExpired:
        logger.error(f"Docker command timed out: {' '.join(command)}")
        return False, "Command timed out"
    except subprocess.CalledProcessError as e:
        logger.warning(f"Docker command failed: {' '.join(command)}\nError: {e.stderr.strip()}")
        return False, e.stderr.strip()

def get_container_health(container_name: str) -> str:
    """Returns the health status of a container (e.g., 'healthy', 'unhealthy', 'starting')."""
    success, status = _run_docker_command(
        ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name]
    )
    return status if success else "unknown"

def get_container_logs(container_name: str, tail: int = 100) -> str:
    """Fetches the last N lines of logs from a container."""
    success, logs = _run_docker_command(
        ["docker", "logs", "--tail", str(tail), container_name]
    )
    return logs if success else ""

def restart_container(container_name: str) -> bool:
    """Restarts a Docker container."""
    logger.info(f"Attempting to restart container: {container_name}")
    success, _ = _run_docker_command(["docker", "restart", container_name])
    if success:
        logger.info(f"Successfully issued restart command for container: {container_name}")
    return success

def analyze_logs_for_db_errors(logs: str) -> bool:
    """Checks if logs contain known database connection error patterns."""
    for pattern in DB_ERROR_PATTERNS:
        if pattern in logs:
            logger.warning(f"Detected database error pattern in logs: '{pattern}'")
            return True
    return False

def auto_heal_system():
    """The main self-healing orchestration logic."""
    logger.info(f"Starting self-healing check for {BACKEND_CONTAINER}...")
    backend_health = get_container_health(BACKEND_CONTAINER)

    if backend_health == "healthy":
        logger.info("System is healthy. No action needed.")
        return

    logger.warning(f"Backend container '{BACKEND_CONTAINER}' is not healthy (status: {backend_health}). Analyzing logs...")
    logs = get_container_logs(BACKEND_CONTAINER)

    if analyze_logs_for_db_errors(logs):
        logger.error("Root Cause Analysis: Database connection failure detected. Attempting to heal the database.")
        db_health = get_container_health(DB_CONTAINER)
        logger.info(f"Current database container '{DB_CONTAINER}' health: {db_health}")

        if restart_container(DB_CONTAINER):
            logger.info("Waiting for database to stabilize after restart (60 seconds)...")
            time.sleep(60)
            db_health_after_restart = get_container_health(DB_CONTAINER)
            if db_health_after_restart == "healthy":
                logger.info("Database is now healthy. Proceeding to restart the backend.")
                restart_container(BACKEND_CONTAINER)
            else:
                logger.critical(f"Database '{DB_CONTAINER}' failed to become healthy after restart. Manual intervention required.")
        else:
            logger.critical(f"Failed to issue restart command for database '{DB_CONTAINER}'. Manual intervention required.")
    else:
        logger.warning("No specific database errors found in recent logs. Performing a standard restart of the backend.")
        restart_container(BACKEND_CONTAINER)

    # Final check after healing attempts
    logger.info("Waiting 30 seconds for backend to stabilize after healing actions...")
    time.sleep(30)
    final_health = get_container_health(BACKEND_CONTAINER)
    if final_health == "healthy":
        logger.info(f"SUCCESS: System has been auto-healed. '{BACKEND_CONTAINER}' is now healthy.")
    else:
        logger.error(f"FAILURE: System could not be auto-healed. '{BACKEND_CONTAINER}' is still unhealthy (status: {final_health}).")

if __name__ == "__main__":
    auto_heal_system()
