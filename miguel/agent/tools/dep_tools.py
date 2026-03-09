"""Tools for Miguel to manage Python package dependencies."""

import re
import subprocess
import sys
from pathlib import Path

from miguel.agent.tools.error_utils import safe_tool

PROJECT_DIR = Path(__file__).parent.parent.parent.parent
PYPROJECT_PATH = PROJECT_DIR / "pyproject.toml"


@safe_tool
def add_dependency(package_name: str) -> str:
    """Install a Python package and add it to pyproject.toml dependencies.

    Use this when you need a new library (e.g. 'duckduckgo-search', 'requests').
    The package is pip-installed immediately and added to pyproject.toml so it
    persists across installs.

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

    # 2. Add to pyproject.toml
    content = PYPROJECT_PATH.read_text()

    # Check if already in dependencies
    # Normalize: 'duckduckgo-search' matches 'duckduckgo-search' or 'duckduckgo_search'
    base_name = package_name.split("[")[0]  # strip extras like [all]
    normalized = base_name.lower().replace("-", "[-_]").replace("_", "[-_]")
    if re.search(rf'"{normalized}', content, re.IGNORECASE):
        return f"Package '{package_name}' already in pyproject.toml. Installed/updated successfully."

    # Insert before the closing bracket of dependencies list
    content = content.replace(
        '    "python-dotenv",\n',
        f'    "python-dotenv",\n    "{package_name}",\n',
    )

    # Fallback: find the last dependency line and add after it
    if f'"{package_name}"' not in content:
        lines = content.split("\n")
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('"') and lines[i].strip().endswith('",'):
                lines.insert(i + 1, f'    "{package_name}",')
                content = "\n".join(lines)
                break

    PYPROJECT_PATH.write_text(content)

    return f"Installed '{package_name}' and added to pyproject.toml."


@safe_tool
def list_dependencies() -> str:
    """List all current dependencies from pyproject.toml."""
    content = PYPROJECT_PATH.read_text()
    # Extract dependencies list
    match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if not match:
        return "Could not find dependencies in pyproject.toml."
    deps = re.findall(r'"([^"]+)"', match.group(1))
    return "\n".join(f"- {d}" for d in deps) if deps else "No dependencies found."
