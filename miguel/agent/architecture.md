# Miguel Architecture Map

## Overview
Miguel is a self-improving AI agent built on the **Agno** framework with **Claude** (Anthropic) as its LLM backbone. It can read, modify, and extend its own source code.

## Directory Structure

```
agent/
├── __init__.py          # Package entry point — exports create_agent()
├── core.py              # Agent factory — creates and configures the Agent instance
├── config.py            # Settings — model ID, version, constants
├── prompts.py           # System prompt builder — defines Miguel's personality & instructions
├── architecture.md      # This file — self-describing architecture map
├── capabilities.json    # Checklist of capabilities (checked/unchecked)
├── improvements.md      # Log of all self-improvements made
└── tools/
    ├── __init__.py      # Empty — makes tools/ a Python package
    ├── capability_tools.py  # Tools for managing the capability checklist
    ├── prompt_tools.py      # Tools for safely inspecting and modifying the system prompt
    ├── self_tools.py    # Tools for self-inspection and logging improvements
    └── tool_creator.py  # Tools for creating new tools and auto-registering them
```

## Key Components

### core.py — The Heart
- `create_agent()` — Factory function that instantiates an `agno.agent.Agent`
- Wires together: model, instructions, and all tools
- External tools: `PythonTools` (run code), `ShellTools` (run commands), `LocalFileSystemTools` (read/write files)
- Custom tools: capability management + self-inspection + prompt modification + tool creation

### prompts.py — The Brain
- `get_system_prompt()` returns a list of instruction strings
- Defines Miguel's identity, behavior rules, and improvement process
- This file is the primary target for self-improvement
- Can be safely modified using the prompt_tools

### config.py — Settings
- `MODEL_ID` — Which Claude model to use
- `AGENT_VERSION` — Current version string
- `MAX_TOOL_RETRIES` — Error handling config

### tools/capability_tools.py — Growth Engine
- `get_capabilities()` — Read full checklist
- `get_next_capability()` — Find highest-priority unchecked item
- `check_capability(id)` — Mark item as done
- `add_capability(title, desc, priority)` — Add new items
- Data stored in `capabilities.json`

### tools/self_tools.py — Self-Awareness
- `read_own_file(path)` — Read any file in agent/ (with security check)
- `list_own_files()` — List all files in agent/
- `get_architecture()` — Return this architecture map
- `log_improvement(summary, files)` — Append to improvements.md

### tools/prompt_tools.py — Prompt Self-Modification
- `get_prompt_sections()` — Parse and list all sections in the system prompt with line counts
- `modify_prompt_section(section_name, new_content, action)` — Safely modify prompt sections
  - Actions: `replace` (overwrite), `append` (add lines), `add_new` (create section)
  - Uses AST parsing to extract current prompt lines
  - Validates generated Python syntax before writing — prevents breaking prompts.py
  - Handles f-strings containing `{AGENT_DIR}` correctly

### tools/tool_creator.py — Tool Factory
- `create_tool(file_name, code, register)` — Create a new tool file in tools/ and auto-register in core.py
  - Validates Python syntax before writing
  - Ensures all public functions have docstrings (required by Agno)
  - Automatically adds import statement and tool registration to core.py
  - Validates core.py syntax after modification — rolls back if broken
- `add_functions_to_tool(file_name, new_code)` — Append new functions to an existing tool file
  - Checks for naming conflicts with existing functions
  - Validates combined file syntax
  - Auto-registers new functions in core.py

## Data Flow
1. User message → `create_agent()` builds Agent → Claude processes with system prompt
2. Claude decides which tools to call → tools execute → results fed back
3. For self-improvement: read checklist → implement change → write files → mark done → log
4. For prompt modification: parse sections → modify → validate syntax → write → confirm
5. For tool creation: write tool file → validate syntax → update core.py imports → register tools

## Security Boundaries
- `read_own_file` refuses to read outside agent/
- `LocalFileSystemTools` is scoped to agent/ directory
- `modify_prompt_section` validates syntax before writing (prevents self-corruption)
- `create_tool` validates syntax and docstrings before writing, validates core.py after modification
- System prompt explicitly forbids modifying files outside agent/