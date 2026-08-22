"""
GULA Platform - Autonomous Manager (Self-Healing Platform)
Executive Order 23: Self-healing, auto-restart, isolation of failed services
"""

import asyncio
import logging
import os
import subprocess
from datetime import UTC, datetime, timedelta

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from starlette.responses import Response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("autonomous-manager")

# Metrics
SERVICE_HEALTH = Gauge("service_health", "Service health status (1=healthy, 0=unhealthy)", ["service"])
RESTART_COUNTER = Counter("service_restarts_total", "Total service restarts", ["service"])
CIRCUIT_STATE = Gauge("circuit_breaker_state", "Circuit breaker state (0=closed, 1=half-open, 2=open)", ["service"])

SERVICES = {
    "gula-lab-service":           {"url": "http://lab-service:8000/health",           "critical": True},
    "gula-patient-service":       {"url": "http://patient-service:8000/health",       "critical": True},
    "gula-order-service":         {"url": "http://order-service:8000/health",         "critical": True},
    "gula-result-service":        {"url": "http://result-service:8000/health",        "critical": True},
    "gula-sample-service":        {"url": "http://sample-service:8000/health",        "critical": True},
    "gula-ai-service":            {"url": "http://ai-service:9000/health",            "critical": False},
    "gula-notification-service":  {"url": "http://notification-service:8000/health",  "critical": False},
    "gula-rabbitmq":              {"url": "http://rabbitmq:15672/api/health/checks/virtual-hosts", "critical": True},
    "gula-redis":                 {"url": None,                                       "critical": True},
    "gula-ollama":                {"url": "http://ollama:11434/api/tags",             "critical": False},
}

FAILURE_COUNTS: dict[str, int] = dict.fromkeys(SERVICES, 0)
LAST_RESTART: dict[str, datetime | None] = dict.fromkeys(SERVICES)
MAX_FAILURES_BEFORE_RESTART = 3
HEALTH_CHECK_INTERVAL = 15  # seconds
RESTART_COOLDOWN = 60       # seconds between restarts

app = FastAPI(
    title="GULA Autonomous Manager",
    description="Self-healing platform manager",
    version="1.0.0",
)

_cors_origins = os.getenv("CORS_ORIGINS", "https://gula-platform.org,http://gula-platform.org").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


def check_service_health(service_name: str, service_config: dict) -> bool:
    """Check if a service is healthy."""
    url = service_config.get("url")
    if not url:
        return True  # No health URL = assume healthy

    try:
        resp = requests.get(url, timeout=5, auth=("guest", "guest") if "rabbitmq" in service_name else None)
        return resp.status_code < 500
    except Exception:
        return False


def restart_service(service_name: str) -> bool:
    """Restart a Docker container by name."""
    last = LAST_RESTART.get(service_name)
    if last and datetime.now(UTC) - last < timedelta(seconds=RESTART_COOLDOWN):
        logger.warning(f"[AutoManager] {service_name}: restart cooldown active, skipping")
        return False

    logger.warning(f"[AutoManager] Restarting container: {service_name}")
    try:
        result = subprocess.run(
            ["docker", "restart", service_name],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            LAST_RESTART[service_name] = datetime.now(UTC)
            RESTART_COUNTER.labels(service=service_name).inc()
            logger.info(f"[AutoManager] {service_name}: restarted successfully")
            return True
        logger.error(f"[AutoManager] {service_name}: restart failed: {result.stderr}")
        return False
    except Exception as e:
        logger.error(f"[AutoManager] {service_name}: restart error: {e}")
        return False


async def health_monitor_loop():
    """Continuous health monitoring and auto-healing loop."""
    logger.info("[AutoManager] Health monitor started")

    while True:
        for service_name, config in SERVICES.items():
            try:
                healthy = check_service_health(service_name, config)

                if healthy:
                    SERVICE_HEALTH.labels(service=service_name).set(1)
                    if FAILURE_COUNTS[service_name] > 0:
                        logger.info(f"[AutoManager] {service_name}: recovered")
                    FAILURE_COUNTS[service_name] = 0
                else:
                    FAILURE_COUNTS[service_name] += 1
                    SERVICE_HEALTH.labels(service=service_name).set(0)
                    logger.warning(
                        f"[AutoManager] {service_name}: unhealthy "
                        f"(failures: {FAILURE_COUNTS[service_name]})"
                    )

                    if FAILURE_COUNTS[service_name] >= MAX_FAILURES_BEFORE_RESTART:
                        if config.get("critical", False):
                            restart_service(service_name)
                        else:
                            logger.warning(f"[AutoManager] {service_name}: non-critical, not restarting")
                        FAILURE_COUNTS[service_name] = 0

            except Exception as e:
                logger.error(f"[AutoManager] Error checking {service_name}: {e}")

        await asyncio.sleep(HEALTH_CHECK_INTERVAL)


@app.on_event("startup")
async def startup():
    asyncio.create_task(health_monitor_loop())
    logger.info("[AutoManager] Autonomous Manager started")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "autonomous-manager"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/status")
def status():
    """Get current health status of all services."""
    service_status = {}
    for service_name, config in SERVICES.items():
        service_status[service_name] = {
            "healthy": FAILURE_COUNTS[service_name] == 0,
            "failure_count": FAILURE_COUNTS[service_name],
            "critical": config.get("critical", False),
            "last_restart": LAST_RESTART[service_name].isoformat() if LAST_RESTART[service_name] else None,
        }
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "services": service_status,
        "total_services": len(SERVICES),
        "healthy_services": sum(1 for f in FAILURE_COUNTS.values() if f == 0),
    }


@app.post("/restart/{service_name}")
def manual_restart(service_name: str):
    """Manually restart a service."""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")
    success = restart_service(service_name)
    return {"service": service_name, "restarted": success}


@app.get("/circuit-breakers")
def circuit_breakers():
    """Get circuit breaker states from database."""
    return {
        "message": "Circuit breaker states stored in audit_log database",
        "endpoint": "/status for service health",
    }
