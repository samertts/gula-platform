
import os
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

CONTAINER_NAME = "gula-backend"

def is_container_healthy(container_name: str) -> bool:
    """Checks if a Docker container is running and healthy."""
    try:
        # Use docker inspect to get container health status
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name],
            capture_output=True, text=True, check=True
        )
        status = result.stdout.strip()
        return status == "healthy"
    except subprocess.CalledProcessError as e:
        logger.warning(f"Could not inspect container {container_name}: {e.stderr.strip()}")
        # If inspect fails, assume it's not healthy or doesn't exist
        return False
    except FileNotFoundError:
        logger.error("Docker command not found. Is Docker installed and in PATH?")
        return False

def restart_container(container_name: str) -> bool:
    """Restarts a Docker container."""
    logger.info(f"Attempting to restart container: {container_name}")
    try:
        subprocess.run(
            ["docker", "restart", container_name],
            capture_output=True, text=True, check=True
        )
        logger.info(f"Successfully restarted container: {container_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to restart container {container_name}: {e.stderr.strip()}")
        return False

def auto_heal_backend():
    """Checks backend health and attempts to auto-heal if necessary."""
    logger.info(f"Checking health of {CONTAINER_NAME}...")
    if not is_container_healthy(CONTAINER_NAME):
        logger.warning(f"Container {CONTAINER_NAME} is not healthy. Initiating restart...")
        if restart_container(CONTAINER_NAME):
            # Give it some time to start up and become healthy
            time.sleep(30) 
            if is_container_healthy(CONTAINER_NAME):
                logger.info(f"Container {CONTAINER_NAME} is now healthy after restart.")
            else:
                logger.error(f"Container {CONTAINER_NAME} is still unhealthy after restart. Manual intervention may be required.")
        else:
            logger.error(f"Failed to restart {CONTAINER_NAME}. Manual intervention may be required.")
    else:
        logger.info(f"Container {CONTAINER_NAME} is healthy.")

if __name__ == "__main__":
    auto_heal_backend()
