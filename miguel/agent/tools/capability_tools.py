"""Tools for managing Miguel's capability checklist."""

import json
from datetime import datetime, timezone
from pathlib import Path

from miguel.agent.tools.error_utils import safe_tool

CAPABILITIES_PATH = Path(__file__).parent.parent / "capabilities.json"


def _load() -> dict:
    """Load capabilities data. Raises on failure for callers to handle."""
    if not CAPABILITIES_PATH.exists():
        raise FileNotFoundError(f"Capabilities file not found at {CAPABILITIES_PATH}")
    text = CAPABILITIES_PATH.read_text()
    data = json.loads(text)
    if "capabilities" not in data:
        raise KeyError("capabilities.json is missing the 'capabilities' key")
    return data


def _save(data: dict) -> None:
    """Save capabilities data with validation."""
    if not isinstance(data, dict) or "capabilities" not in data:
        raise ValueError("Invalid capabilities data structure")
    text = json.dumps(data, indent=2) + "\n"
    tmp_path = CAPABILITIES_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(text)
    tmp_path.rename(CAPABILITIES_PATH)


@safe_tool
def get_capabilities() -> str:
    """Read the full capabilities checklist and return it as formatted JSON."""
    return json.dumps(_load(), indent=2)


@safe_tool
def get_next_capability() -> str:
    """Get the highest-priority unchecked capability. Returns its JSON or a message if all are checked."""
    data = _load()
    unchecked = [c for c in data["capabilities"] if c["status"] == "unchecked"]
    if not unchecked:
        return "ALL_CHECKED: All capabilities are checked. You should generate new capabilities using add_capability."
    unchecked.sort(key=lambda c: c["priority"])
    return json.dumps(unchecked[0], indent=2)


@safe_tool
def check_capability(capability_id: str) -> str:
    """Mark a capability as completed by its ID (e.g. 'cap-001')."""
    if not capability_id or not capability_id.startswith("cap-"):
        return f"Error: Invalid capability ID '{capability_id}'. Must be like 'cap-001'."

    data = _load()
    for item in data["capabilities"]:
        if item["id"] == capability_id:
            if item["status"] == "checked":
                return f"Warning: Capability '{capability_id}' ({item['title']}) is already checked."
            item["status"] = "checked"
            item["completed_at"] = datetime.now(timezone.utc).isoformat()
            _save(data)
            return f"Capability '{capability_id}' ({item['title']}) marked as completed."
    return f"Error: Capability '{capability_id}' not found. Use get_capabilities() to see valid IDs."


@safe_tool
def add_capability(title: str, description: str, priority: int) -> str:
    """Add a new capability to the checklist. Priority determines order (lower = higher priority)."""
    if not title or not title.strip():
        return "Error: title must not be empty."
    if not description or not description.strip():
        return "Error: description must not be empty."
    if not isinstance(priority, int) or priority < 1:
        return "Error: priority must be a positive integer."

    data = _load()
    existing_ids = [c["id"] for c in data["capabilities"]]
    max_num = max(int(cid.split("-")[1]) for cid in existing_ids) if existing_ids else 0
    new_id = f"cap-{max_num + 1:03d}"

    existing_titles = [c["title"].lower() for c in data["capabilities"]]
    if title.strip().lower() in existing_titles:
        return f"Warning: A capability with a similar title already exists. Adding anyway as '{new_id}'."

    new_cap = {
        "id": new_id,
        "title": title.strip(),
        "description": description.strip(),
        "priority": priority,
        "status": "unchecked",
        "category": "self-generated",
        "added_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }
    data["capabilities"].append(new_cap)
    _save(data)
    return f"Added capability '{new_id}': {title}"