"""Docker container lifecycle management for Miguel."""

import subprocess
import time
from pathlib import Path

from miguel.client import container_healthy

PROJECT_DIR = Path(__file__).parent.parent


def ensure_container() -> bool:
    """Start the container if not running and wait for it to become healthy.

    Returns True if the container is ready, False if it failed to start.
    """
    if container_healthy():
        return True

    # Check if container exists but is stopped
    result = subprocess.run(
        ["docker", "compose", "ps", "-q"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )

    # Start (or rebuild if needed)
    subprocess.run(
        ["docker", "compose", "up", "-d", "--build"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )

    # Wait for health endpoint
    for _ in range(60):
        if container_healthy():
            return True
        time.sleep(1)

    return False


def stop_container():
    """Stop the Docker container."""
    subprocess.run(
        ["docker", "compose", "down"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
