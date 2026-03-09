"""Recovery and diagnostic tools for Miguel.

Provides tools to recover from errors: restore backups, validate files,
and diagnose issues in the agent's codebase.
"""

import ast
import json
from pathlib import Path

from miguel.agent.tools.error_utils import (
    safe_tool,
    safe_write,
    validate_python,
    list_backups,
    AGENT_DIR,
)


@safe_tool
def recover_backup(file_path: str) -> str:
    """Restore a file from its .bak backup. Use list_recovery_points() first to see available backups.

    Args:
        file_path: Relative path to the original file (e.g. 'core.py', 'tools/self_tools.py').

    Returns:
        Success message or error.
    """
    if not file_path or not file_path.strip():
        return "Error: file_path must not be empty."

    target = AGENT_DIR / file_path
    backup = target.with_suffix(target.suffix + ".bak")

    if not backup.exists():
        available = list_backups()
        if available:
            names = [b["original"] for b in available]
            return (
                f"Error: No backup found for '{file_path}'. "
                f"Available backups exist for: {', '.join(names)}"
            )
        return f"Error: No backup found for '{file_path}' and no backups exist at all."

    # Read backup content
    backup_content = backup.read_text()

    # If it's a Python file, validate syntax before restoring
    if file_path.endswith(".py"):
        is_valid, error = validate_python(backup_content)
        if not is_valid:
            return (
                f"Warning: Backup file has syntax errors ({error}). "
                "Restoring anyway — but the file may need manual fixing."
            )

    # Restore: backup → original (keep the backup file intact for safety)
    target.write_text(backup_content)

    # Verify the restore worked
    restored = target.read_text()
    if restored != backup_content:
        return "Error: Restore verification failed — file content doesn't match backup."

    size = len(backup_content)
    return f"Restored '{file_path}' from backup ({size} bytes). Backup file preserved."


@safe_tool
def list_recovery_points() -> str:
    """List all available .bak backup files that can be restored.

    Returns:
        Formatted list of available backups, or a message if none exist.
    """
    backups = list_backups()
    if not backups:
        return "No backup files found. Backups are created automatically when tools modify files."

    result = "## Available Backups\n\n"
    for b in backups:
        result += f"- **{b['original']}** → backup: `{b['backup']}` ({b['size_bytes']} bytes)\n"
    result += "\nUse `recover_backup(file_path)` to restore from a backup."
    return result


@safe_tool
def validate_agent_file(file_path: str) -> str:
    """Validate a Python file in the agent directory for syntax errors.

    Args:
        file_path: Relative path to the file (e.g. 'core.py', 'tools/self_tools.py').

    Returns:
        Validation result: either 'Valid' or details about errors found.
    """
    if not file_path or not file_path.strip():
        return "Error: file_path must not be empty."

    if not file_path.endswith(".py"):
        return "Error: Can only validate .py files."

    target = AGENT_DIR / file_path
    if not target.exists():
        return f"Error: File '{file_path}' not found."

    # Security check
    agent_resolved = AGENT_DIR.resolve()
    target_resolved = target.resolve()
    if not str(target_resolved).startswith(str(agent_resolved)):
        return "Error: Cannot validate files outside agent/ directory."

    code = target.read_text()
    is_valid, error = validate_python(code)

    if is_valid:
        # Also check for common issues
        issues = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            pass
        else:
            # Check for functions without docstrings (just a warning)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    if not (node.body
                            and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and isinstance(node.body[0].value.value, str)):
                        issues.append(f"Function '{node.name}' has no docstring (warning)")

        result = f"✅ **{file_path}** — Valid Python syntax ({len(code)} bytes, {code.count(chr(10)) + 1} lines)"
        if issues:
            result += "\n\n**Warnings:**\n" + "\n".join(f"- {i}" for i in issues)
        return result
    else:
        return f"❌ **{file_path}** — {error}"


@safe_tool
def health_check() -> str:
    """Run a comprehensive health check on Miguel's codebase.

    Validates all critical Python files for syntax, checks that key files exist,
    and verifies the capabilities.json structure.

    Returns:
        Formatted health check report.
    """
    results = []
    all_ok = True

    # Check critical files exist
    critical_files = ["core.py", "config.py", "prompts.py", "capabilities.json", "architecture.md"]
    for f in critical_files:
        path = AGENT_DIR / f
        if path.exists():
            results.append(f"✅ {f} exists")
        else:
            results.append(f"❌ {f} MISSING")
            all_ok = False

    # Validate all Python files
    results.append("")
    results.append("**Python Syntax Validation:**")
    py_files = sorted(AGENT_DIR.rglob("*.py"))
    for py in py_files:
        if "__pycache__" in str(py):
            continue
        rel = str(py.relative_to(AGENT_DIR))
        code = py.read_text()
        is_valid, error = validate_python(code)
        if is_valid:
            results.append(f"  ✅ {rel}")
        else:
            results.append(f"  ❌ {rel} — {error}")
            all_ok = False

    # Validate capabilities.json structure
    results.append("")
    results.append("**Capabilities JSON:**")
    cap_path = AGENT_DIR / "capabilities.json"
    if cap_path.exists():
        try:
            data = json.loads(cap_path.read_text())
            if "capabilities" in data and isinstance(data["capabilities"], list):
                checked = sum(1 for c in data["capabilities"] if c["status"] == "checked")
                total = len(data["capabilities"])
                results.append(f"  ✅ Valid structure — {checked}/{total} capabilities checked")
            else:
                results.append("  ❌ Missing 'capabilities' key or wrong type")
                all_ok = False
        except json.JSONDecodeError as e:
            results.append(f"  ❌ Invalid JSON — {e}")
            all_ok = False

    # Check for orphan backup files
    backups = list_backups()
    if backups:
        results.append("")
        results.append(f"**Backup files:** {len(backups)} found")
        for b in backups:
            results.append(f"  📦 {b['backup']}")

    # Summary
    status = "✅ All checks passed" if all_ok else "⚠️ Issues found — see details above"
    header = f"## Miguel Health Check\n\n**Status:** {status}\n\n"
    return header + "\n".join(results)