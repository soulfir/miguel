"""Tool for creating and registering new tools in Miguel's toolset."""

import ast
from pathlib import Path

from miguel.agent.tools.error_utils import safe_tool, validate_python

AGENT_DIR = Path(__file__).parent.parent
CORE_PATH = AGENT_DIR / "core.py"
TOOLS_DIR = AGENT_DIR / "tools"


def _extract_function_names(code: str) -> list[str]:
    """Extract top-level function names from Python code (excluding _ prefixed)."""
    tree = ast.parse(code)
    return [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]


def _has_docstring(code: str, func_name: str) -> bool:
    """Check if a function has a docstring."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            if (node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                return True
    return False


def _register_tools_in_core(file_name: str, func_names: list[str]) -> str:
    """Add import and tool registration for given functions to core.py."""
    if not CORE_PATH.exists():
        return "Error: core.py not found. Cannot register tools."

    core_code = CORE_PATH.read_text()

    # Backup core.py before modifying
    backup_path = CORE_PATH.with_suffix(".py.bak")
    backup_path.write_text(core_code)

    module_name = file_name.replace(".py", "")
    import_module = f"miguel.agent.tools.{module_name}"

    # Check which functions are already imported/registered
    new_funcs = [fn for fn in func_names if fn not in core_code]
    if not new_funcs:
        return "All functions already registered in core.py."

    # Build the import block
    if len(new_funcs) == 1:
        import_block = f"from {import_module} import {new_funcs[0]}"
    else:
        inner = "".join(f"    {fn},\n" for fn in new_funcs)
        import_block = f"from {import_module} import (\n{inner})"

    # Find the right place to insert the import — after the last top-level import block
    lines = core_code.split("\n")
    last_import_line = 0
    in_multiline_import = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("from ") or stripped.startswith("import "):
            last_import_line = i
            if "(" in stripped and ")" not in stripped:
                in_multiline_import = True
        if in_multiline_import:
            last_import_line = i
            if ")" in stripped:
                in_multiline_import = False

    # Insert import after the last import line
    lines.insert(last_import_line + 1, import_block)

    # Now find the tools=[ ... ] list and insert before its closing ]
    new_code = "\n".join(lines)

    tools_start = new_code.find("tools=[")
    if tools_start == -1:
        return "Warning: Could not find tools=[ in core.py. Manual registration needed."

    # Find the matching ] for the tools list
    search_start = tools_start + len("tools=[")
    bracket_depth = 1
    tools_end_pos = -1
    for i in range(search_start, len(new_code)):
        if new_code[i] == "[":
            bracket_depth += 1
        elif new_code[i] == "]":
            bracket_depth -= 1
            if bracket_depth == 0:
                tools_end_pos = i
                break

    if tools_end_pos == -1:
        return "Warning: Could not find end of tools list. Manual registration needed."

    # Insert new tool entries before the closing ]
    tool_entries = "".join(f"            {fn},\n" for fn in new_funcs)
    new_code = new_code[:tools_end_pos] + tool_entries + new_code[tools_end_pos:]

    # Validate the modified core.py before writing
    is_valid, error = validate_python(new_code)
    if not is_valid:
        # Restore backup
        backup_path.rename(CORE_PATH)
        return f"Warning: Modified core.py would have syntax errors ({error}). Restored backup. Add manually."

    CORE_PATH.write_text(new_code)
    return f"Registered {', '.join(new_funcs)} in core.py."


@safe_tool
def create_tool(file_name: str, code: str, register: bool = True) -> str:
    """Create a new tool file in tools/ and optionally register it in core.py.

    Args:
        file_name: Name of the file (e.g. 'web_tools.py'). Must end with .py.
        code: Python source code for the tool file. Must contain at least one public function with a docstring.
        register: If True (default), automatically imports and registers the tools in core.py.

    Returns:
        Success message listing created functions, or an error message.
    """
    if not file_name or not file_name.strip():
        return "Error: file_name must not be empty."
    if not file_name.endswith(".py"):
        return "Error: file_name must end with .py"
    if file_name.startswith("_"):
        return "Error: file_name must not start with underscore"
    if "/" in file_name or "\\" in file_name:
        return "Error: file_name must be a simple filename, not a path"

    target_path = TOOLS_DIR / file_name
    if target_path.exists():
        return (
            f"Error: tools/{file_name} already exists. "
            "Use add_functions_to_tool to extend it, or choose a different name."
        )

    is_valid, error = validate_python(code)
    if not is_valid:
        return f"Error: Invalid Python syntax in provided code. {error}"

    func_names = _extract_function_names(code)
    if not func_names:
        return "Error: Code must contain at least one public function (no leading underscore)."

    for fn in func_names:
        if not _has_docstring(code, fn):
            return f"Error: Function '{fn}' must have a docstring. Agno uses docstrings as tool descriptions."

    target_path.write_text(code)
    result_parts = [f"Created tools/{file_name} with functions: {', '.join(func_names)}"]

    if register:
        reg_result = _register_tools_in_core(file_name, func_names)
        result_parts.append(reg_result)

    return "\n".join(result_parts)


@safe_tool
def add_functions_to_tool(file_name: str, new_code: str) -> str:
    """Add new functions to an existing tool file and register them in core.py.

    Args:
        file_name: Name of the existing tool file (e.g. 'self_tools.py').
        new_code: Python code with new functions to append. Must not duplicate existing function names.

    Returns:
        Success message or error.
    """
    if not file_name or not file_name.strip():
        return "Error: file_name must not be empty."

    target_path = TOOLS_DIR / file_name
    if not target_path.exists():
        return f"Error: tools/{file_name} does not exist. Use create_tool to create it first."

    is_valid, error = validate_python(new_code)
    if not is_valid:
        return f"Error: Invalid Python syntax. {error}"

    new_funcs = _extract_function_names(new_code)
    if not new_funcs:
        return "Error: new_code must contain at least one public function."

    for fn in new_funcs:
        if not _has_docstring(new_code, fn):
            return f"Error: Function '{fn}' must have a docstring."

    existing_code = target_path.read_text()
    existing_funcs = _extract_function_names(existing_code)
    conflicts = set(new_funcs) & set(existing_funcs)
    if conflicts:
        return f"Error: Functions already exist in {file_name}: {', '.join(conflicts)}"

    combined = existing_code.rstrip() + "\n\n\n" + new_code.strip() + "\n"
    is_valid, error = validate_python(combined)
    if not is_valid:
        return f"Error: Combined code has syntax errors. {error}"

    backup_path = target_path.with_suffix(".py.bak")
    backup_path.write_text(existing_code)

    target_path.write_text(combined)

    reg_result = _register_tools_in_core(file_name, new_funcs)
    return f"Added functions {', '.join(new_funcs)} to tools/{file_name}. {reg_result}"