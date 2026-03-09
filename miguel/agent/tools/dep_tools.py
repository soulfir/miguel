"""Tools for Miguel to manage Python package dependencies."""

import re
import subprocess
import sys
from pathlib import Path

from miguel.agent.tools.error_utils import safe_tool

AGENT_DIR = Path(__file__).parent.parent
ADDED_DEPS_PATH = AGENT_DIR / "added_deps.txt"

# pyproject.toml may be read-only in Docker; used only for reading
PROJECT_DIR = Path(__file__).parent.parent.parent.parent
PYPROJECT_PATH = PROJECT_DIR / "pyproject.toml"


@safe_tool
def add_dependency(package_name: str) -> str:
    """Install a Python package and record it for persistence.

    Use this when you need a new library (e.g. 'duckduckgo-search', 'requests').
    The package is pip-installed immediately. It is also recorded so the host-side
    runner can add it to pyproject.toml after validation.

    Args:
        package_name: PyPI package name (e.g. 'duckduckgo-search', 'requests').
    """
    if not package_name or not package_name.strip():
        return "Error: package_name must not be empty."

    package_name = package_name.strip()

    # Basic validation: only allow reasonable package names
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*(\[.*\])?$', package_name):
        return f"Error: Invalid package name '{package_name}'."

    # 1. Install the package
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package_name],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        return f"Error: pip install failed:\n{result.stderr.strip()}"

    # 2. Record the dependency for host-side merging into pyproject.toml
    # Check if already recorded
    existing = set()
    if ADDED_DEPS_PATH.exists():
        existing = {d.strip().lower() for d in ADDED_DEPS_PATH.read_text().splitlines() if d.strip()}

    base_name = package_name.split("[")[0].lower()
    if base_name not in existing:
        with open(ADDED_DEPS_PATH, "a") as f:
            f.write(f"{package_name}\n")

    return f"Installed '{package_name}'. It will be added to pyproject.toml after validation."


@safe_tool
def list_dependencies() -> str:
    """List all current dependencies from pyproject.toml."""
    try:
        content = PYPROJECT_PATH.read_text()
    except FileNotFoundError:
        return "pyproject.toml not accessible (may be read-only in Docker)."

    # Extract dependencies list
    match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if not match:
        return "Could not find dependencies in pyproject.toml."
    deps = re.findall(r'"([^"]+)"', match.group(1))

    # Also show pending deps
    pending = []
    if ADDED_DEPS_PATH.exists():
        pending = [d.strip() for d in ADDED_DEPS_PATH.read_text().splitlines() if d.strip()]

    result = "\n".join(f"- {d}" for d in deps) if deps else "No dependencies found."
    if pending:
        result += "\n\nPending (will be added after validation):\n"
        result += "\n".join(f"- {d}" for d in pending)
    return result
