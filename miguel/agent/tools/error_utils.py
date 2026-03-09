"""Error handling and recovery utilities for Miguel's tools.

Provides decorators and helpers for consistent, graceful error handling
across all tool functions. Instead of raw exceptions bubbling up, tools
return clean error messages the agent can understand and act on.

Also provides safe file writing with atomic operations and backups,
plus recovery tools for restoring from backups.
"""

import ast
import functools
import json
import traceback
from pathlib import Path
from typing import Callable

AGENT_DIR = Path(__file__).parent.parent


def safe_tool(func: Callable) -> Callable:
    """Decorator that wraps a tool function with error handling.

    Catches all exceptions and returns a formatted error string instead
    of letting the exception propagate. This ensures the agent always
    gets a usable response it can reason about.

    Usage:
        @safe_tool
        def my_tool(arg: str) -> str:
            '''My tool description.'''
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> str:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            return f"Error in {func.__name__}: File not found — {e}"
        except PermissionError as e:
            return f"Error in {func.__name__}: Permission denied — {e}"
        except json.JSONDecodeError as e:
            return f"Error in {func.__name__}: Invalid JSON — {e}"
        except (KeyError, IndexError) as e:
            return f"Error in {func.__name__}: Data access error — {type(e).__name__}: {e}"
        except SyntaxError as e:
            return f"Error in {func.__name__}: Python syntax error at line {e.lineno} — {e.msg}"
        except OSError as e:
            return f"Error in {func.__name__}: OS/filesystem error — {e}"
        except Exception as e:
            # Catch-all for unexpected errors — include traceback for debugging
            tb = traceback.format_exc()
            short_tb = "\n".join(tb.strip().split("\n")[-3:])
            return (
                f"Error in {func.__name__}: Unexpected {type(e).__name__} — {e}\n"
                f"Traceback (last 3 lines):\n{short_tb}"
            )

    return wrapper


def format_error(tool_name: str, error: Exception, hint: str = "") -> str:
    """Format an error message consistently for tool responses.

    Args:
        tool_name: Name of the tool/function that failed.
        error: The exception that was caught.
        hint: Optional hint for recovery.

    Returns:
        Formatted error string.
    """
    msg = f"Error in {tool_name}: {type(error).__name__} — {error}"
    if hint:
        msg += f"\nHint: {hint}"
    return msg


def safe_write(target: Path, content: str, backup: bool = True) -> str:
    """Write content to a file safely with atomic write and optional backup.

    Steps:
    1. If backup=True and file exists, create a .bak copy
    2. Write to a temporary file (.tmp)
    3. Rename tmp → target (atomic on most filesystems)

    Args:
        target: Path to the file to write.
        content: Content to write.
        backup: Whether to create a .bak backup first.

    Returns:
        Success message or raises an exception.
    """
    # Security check
    agent_resolved = AGENT_DIR.resolve()
    target_resolved = target.resolve()
    if not str(target_resolved).startswith(str(agent_resolved)):
        raise PermissionError(f"Cannot write outside agent directory: {target}")

    # Backup existing file
    if backup and target.exists():
        backup_path = target.with_suffix(target.suffix + ".bak")
        backup_path.write_text(target.read_text())

    # Atomic write via temp file
    tmp_path = target.with_suffix(target.suffix + ".tmp")
    try:
        tmp_path.write_text(content)
        tmp_path.rename(target)
    except Exception:
        # Clean up temp file on failure
        if tmp_path.exists():
            tmp_path.unlink()
        raise

    return f"Written {len(content)} bytes to {target.relative_to(AGENT_DIR)}"


def validate_python(code: str) -> tuple[bool, str]:
    """Validate Python code syntax.

    Args:
        code: Python source code to validate.

    Returns:
        Tuple of (is_valid, error_message). error_message is empty if valid.
    """
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"


def list_backups() -> list[dict]:
    """Find all .bak files in the agent directory.

    Returns:
        List of dicts with 'backup_path', 'original_path', and 'size' keys.
    """
    backups = []
    for bak in sorted(AGENT_DIR.rglob("*.bak")):
        if "__pycache__" in str(bak):
            continue
        # Determine original path by removing the .bak suffix
        original = bak.with_suffix("")  # removes .bak, keeps .py
        backups.append({
            "backup": str(bak.relative_to(AGENT_DIR)),
            "original": str(original.relative_to(AGENT_DIR)),
            "size_bytes": bak.stat().st_size,
        })
    return backups