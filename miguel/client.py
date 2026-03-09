"""HTTP client for communicating with the Docker-sandboxed agent server."""

import json

import httpx
from agno.run.agent import run_output_event_from_dict

CONTAINER_URL = "http://localhost:8420"


def stream_from_container(prompt: str, session_id: str | None = None,
                          interactive: bool = False):
    """POST to the container's /run endpoint and yield reconstructed RunEvent objects.

    The yielded events are identical Agno dataclass instances, so render_stream()
    works without any changes.
    """
    with httpx.stream(
        "POST",
        f"{CONTAINER_URL}/run",
        json={"prompt": prompt, "session_id": session_id, "interactive": interactive},
        timeout=None,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                return
            try:
                data = json.loads(payload)
                yield run_output_event_from_dict(data)
            except Exception:
                continue


def reload_agent():
    """Tell the container to reload its agent modules."""
    resp = httpx.post(f"{CONTAINER_URL}/reload", timeout=30)
    resp.raise_for_status()
    return resp.json()


def container_healthy() -> bool:
    """Check if the container is running and responsive."""
    try:
        resp = httpx.get(f"{CONTAINER_URL}/health", timeout=5)
        return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError):
        return False
