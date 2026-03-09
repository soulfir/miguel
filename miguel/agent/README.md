# Miguel

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude%20Opus%204.6-blueviolet.svg)](https://anthropic.com)
[![Docker Required](https://img.shields.io/badge/Docker-Required-2496ED.svg)](https://docker.com)
[![Built with Agno](https://img.shields.io/badge/Built%20with-Agno-green.svg)](https://github.com/agno-agi/agno)

**A self-improving AI agent that reads, modifies, and extends its own source code — safely sandboxed inside Docker.**

---

Miguel is an AI agent that can rewrite itself. Not just generate code for you — it modifies *its own* source code, creates new tools, rewrites its own system prompts, and generates new capabilities it didn't start with.

It began with 10 seed capabilities. It completed all 10, then autonomously generated 6 more and has already implemented 3 of those. Every improvement is validated (syntax, imports, schema), committed to git, and pushed to this repo. If validation fails, the batch is rolled back automatically. The agent literally cannot corrupt itself.

This is a **living repository**. Miguel auto-commits and pushes after each successful improvement. The code you see today will be different tomorrow as Miguel continues to evolve. Star or watch this repo to follow along.

Beyond self-improvement, Miguel is also a fully interactive AI assistant — chat with it, have it search the web, remember things across sessions, plan multi-step projects, or work with your files.

## What It Looks Like

**Interactive mode:**

```
  __  __ _                  _
 |  \/  (_) __ _ _   _  ___| |
 | |\/| | |/ _` | | | |/ _ \ |
 | |  | | | (_| | |_| |  __/ |
 |_|  |_|_|\__, |\__,_|\___|_|
            |___/

  Self-improving AI agent. Type /help for commands.

You: What can you do?

Miguel: I'm a self-improving AI agent. Here's what I can do right now:

  - Answer questions and have conversations
  - Search the web for current information
  - Remember facts and preferences across sessions
  - Break complex tasks into structured plans
  - Read, write, and analyze files in your workspace
  - Execute Python code and shell commands
  - And I can improve myself — add new tools, rewrite my own
    prompts, and generate new capabilities autonomously.

  Type /capabilities to see my full capability checklist,
  or /improve N to watch me enhance myself in real time.
```

**Improvement mode:**

```
───────────────── IMPROVEMENT BATCH 1/3 ─────────────────

I'll start by finding the next capability to implement.
╭─────── Tool Call ───────╮
│ get_next_capability({}) │
╰─────────────────────────╯
╭─────────────────── Result ───────────────────────╮
│ cap-011: Web search and information retrieval    │
│ Priority: 1 | Status: unchecked                  │
╰──────────────────────────────────────────────────╯

[Agent reads its own code, designs the solution, writes
 new files, registers tools, updates prompts, validates,
 and marks the capability as complete]

Running validation checks...
✅ All checks passed
✅ Pushed to remote.
Batch 1 succeeded: Added web search via DuckDuckGo
```

## Features

### As an AI Assistant

- **Interactive REPL** — Chat with slash commands (`/help`, `/capabilities`, `/improve`, `/history`)
- **Web search** — Search the web and news via DuckDuckGo, with region filtering
- **Persistent memory** — Remembers facts, preferences, and context across sessions (SQLite-backed)
- **Task planning** — Breaks complex requests into ordered tasks with dependencies and progress tracking
- **File workspace** — Read, write, and analyze files in the shared `user_files/` directory
- **Code execution** — Run Python code and shell commands inside the sandbox
- **Conversation history** — Maintains context across messages (last 20 turns per session)

### As a Self-Improving Agent

- **Self-modification** — Reads and rewrites its own source code during improvement batches
- **Capability checklist** — Starts with seeds, completes them, then generates new ones autonomously
- **Tool creation** — Writes new tool files and auto-registers them into its own configuration
- **Prompt rewriting** — Safely modifies its own system instructions with syntax validation
- **Self-describing architecture** — Maintains a map of its own codebase that it updates after changes
- **Dependency management** — Can install Python packages it needs and record them for persistence
- **Error recovery** — Automatic backups, health checks, and backup restoration

## Quick Start

### Prerequisites

- **Docker** (Docker Desktop or Docker Engine)
- **Python 3.11+**

### Install

```bash
git clone https://github.com/soulfir/miguel.git
cd miguel
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Add your Anthropic API key to `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

That's it. Docker is managed automatically — the first run builds the image and starts the container.

### Run

```bash
miguel              # Interactive mode — chat, explore, trigger improvements
miguel improve 5    # Run 5 improvement batches autonomously
```

## Usage

### Interactive Mode

```bash
miguel
```

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/capabilities` | Show the capability checklist |
| `/improve N` | Run N improvement batches |
| `/history` | Show the improvement log |
| `/quit` | Exit |

Ask Miguel to search the web, remember your preferences, create a plan for a project, or analyze files in `user_files/`.

### Improvement Mode

```bash
miguel improve 5
```

Each batch: git snapshot → reload agent → agent picks next capability → implements it → host validates (AST + schema + imports) → commit and push, or rollback on failure.

### User Files

Drop files in the `user_files/` directory to share them with Miguel. He can read, write, and manipulate anything there — analyze spreadsheets, transform data, generate reports, etc.

## Architecture

```
HOST (your machine)                           DOCKER CONTAINER (sandboxed)
┌──────────────────────────────┐              ┌──────────────────────────────┐
│  miguel CLI (cli.py)         │              │  FastAPI server (port 8420)  │
│  Improvement runner          │   HTTP/SSE   │                              │
│  Git commit/push             │ ◄──────────► │  Agent + all tool execution  │
│  Validation checks           │              │  Shell, Python, file I/O     │
│  Terminal display            │              │  30+ tools                   │
└──────────────────────────────┘              └──────────────────────────────┘
```

The host is the "immune system" — it handles the CLI, git operations, and validation. The container is the "brain in a jar" — all agent execution happens there, isolated from the host.

**Volume mounts:**

| Host path | Container path | Access |
|-----------|---------------|--------|
| Entire project | `/app` | **Read-only** |
| `miguel/agent/` | `/app/miguel/agent` | Read-write |
| `user_files/` | `/app/user_files` | Read-write |

The agent can only write to its own code (`miguel/agent/`) and the shared `user_files/` directory. Everything else — the CLI, runner, tests, Dockerfile — is physically read-only inside the container.

## Safety

Nine layers of protection ensure the agent cannot corrupt itself or escape its sandbox:

1. **Docker isolation** — Agent runs in a container; cannot access host files beyond mounted volumes
2. **Read-only mounts** — Protected files (CLI, runner, tests, config) are mounted read-only
3. **Path validation** — All file-writing tools refuse to operate outside `miguel/agent/`
4. **AST validation** — Every Python file is syntax-checked after each batch
5. **Schema validation** — `capabilities.json` structure is verified for correctness
6. **Import validation** — The agent is re-instantiated after changes to verify it still loads
7. **Atomic writes** — Temp file + rename pattern prevents partial or corrupt writes
8. **Automatic backups** — `.bak` files created before every file modification
9. **Git rollback** — Failed batches are automatically reverted to the last known good state

## How the Improvement Loop Works

```
┌──────────────────────────────────────────────────┐
│              IMPROVEMENT BATCH                    │
│                                                   │
│  1. Git snapshot current state                    │
│  2. Reload agent in Docker container              │
│  3. Agent reads its own code + checklist          │
│  4. Agent picks next unchecked capability         │
│  5. Agent modifies its own code (inside Docker)   │
│  6. Host validates (AST, imports, schema)         │
│  7. Pass → git commit + push                      │
│     Fail → git rollback                           │
│  8. Repeat                                        │
└──────────────────────────────────────────────────┘
```

When all capabilities are checked, the agent generates new ones and keeps going.

## Capabilities

Miguel started with 10 seed capabilities and has been generating its own ever since.

### Seed Capabilities

| ID | Title | Category | Status |
|----|-------|----------|--------|
| cap-001 | Respond to basic questions | core | done |
| cap-002 | Read and explain own source code | self-awareness | done |
| cap-003 | Modify own instructions/prompts | self-improvement | done |
| cap-004 | Create new custom tools | self-improvement | done |
| cap-005 | Error handling and recovery | robustness | done |
| cap-006 | Execute and validate Python code | capability | done |
| cap-007 | Maintain improvement context | memory | done |
| cap-008 | Validate own code before writing | safety | done |
| cap-009 | Refactor and optimize existing code | quality | done |
| cap-010 | Generate new capabilities autonomously | self-improvement | done |

### Self-Generated Capabilities

These were created by Miguel itself after completing all seed capabilities:

| ID | Title | Status |
|----|-------|--------|
| cap-011 | Web search and information retrieval | done |
| cap-012 | Persistent memory across sessions | done |
| cap-013 | Structured task planning and decomposition | done |
| cap-014 | File analysis — PDF, CSV, images, structured data | pending |
| cap-015 | API integration framework | pending |
| cap-016 | Project scaffolding and code generation | pending |

*This list grows over time as Miguel generates and implements new capabilities.*

## Project Structure

```
Miguel/
├── Dockerfile                     # Container image definition
├── docker-compose.yml             # Container config + volume mounts
├── pyproject.toml                 # Dependencies + CLI entry point
├── .env                           # API key (gitignored)
├── LICENSE                        # CC BY-NC 4.0
├── CONTRIBUTING.md                # Contribution guidelines
├── user_files/                    # Shared workspace for user files
├── miguel/
│   ├── cli.py                     # CLI entry point + REPL (host)
│   ├── runner.py                  # Improvement loop + git ops (host)
│   ├── display.py                 # Terminal renderer (host)
│   ├── client.py                  # HTTP client for container (host)
│   ├── container.py               # Docker lifecycle management (host)
│   ├── tests/
│   │   └── test_agent_health.py   # Validation checks (host)
│   └── agent/                     # MUTABLE — Miguel modifies everything here
│       ├── server.py              # FastAPI server (container)
│       ├── core.py                # Agent factory + tool registration
│       ├── config.py              # Agent settings
│       ├── prompts.py             # System prompts (self-modifying)
│       ├── architecture.md        # Self-describing architecture map
│       ├── capabilities.json      # Capability checklist
│       ├── improvements.md        # Improvement log
│       └── tools/
│           ├── error_utils.py     # Safe tool decorator + atomic writes
│           ├── capability_tools.py # Checklist management
│           ├── self_tools.py      # Self-inspection + logging
│           ├── prompt_tools.py    # Prompt self-modification
│           ├── tool_creator.py    # Tool creation + auto-registration
│           ├── recovery_tools.py  # Backups + diagnostics
│           ├── dep_tools.py       # Dependency management
│           ├── web_tools.py       # Web search (DuckDuckGo)
│           ├── memory_tools.py    # Persistent memory (SQLite)
│           └── planning_tools.py  # Task planning + dependencies
```

## Tools

Miguel has 30+ tools across 10 categories, plus access to Python, shell, and filesystem tools from Agno.

| Category | Tools | Description |
|----------|-------|-------------|
| **Capability Management** | `get_capabilities`, `get_next_capability`, `check_capability`, `add_capability` | Manage the self-improvement checklist |
| **Self-Inspection** | `read_own_file`, `list_own_files`, `get_architecture`, `log_improvement` | Read own code, understand own structure |
| **Prompt Modification** | `get_prompt_sections`, `modify_prompt_section` | Safely rewrite own system instructions |
| **Tool Creation** | `create_tool`, `add_functions_to_tool` | Create new tools and auto-register them |
| **Error Recovery** | `recover_backup`, `list_recovery_points`, `validate_agent_file`, `health_check` | Diagnostics, backups, restoration |
| **Dependencies** | `add_dependency`, `list_dependencies` | Install and track Python packages |
| **Web Search** | `web_search`, `web_news`, `web_search_detailed` | Search the web via DuckDuckGo |
| **Memory** | `remember`, `recall`, `forget`, `memory_stats` | Persistent facts, preferences, context |
| **Planning** | `create_plan`, `add_task`, `update_task`, `show_plan`, `list_plans`, `get_next_task`, `remove_plan` | Structured task decomposition |
| **Built-in (Agno)** | `PythonTools`, `ShellTools`, `LocalFileSystemTools` | Execute code, run commands, file I/O |

## This Is a Living Project

Miguel is continuously improving itself. After each successful improvement batch, the changes are automatically committed and pushed to this repository. The capabilities list, tool count, and code quality grow over time.

**What you see in this repo today will be different tomorrow.**

The current bottleneck on Miguel's improvement rate is API costs — each improvement batch requires calls to Claude Opus 4.6. The more that can be invested, the faster Miguel evolves.

Star and watch this repo to follow Miguel's evolution as it becomes more capable.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get involved.

## License

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License](https://creativecommons.org/licenses/by-nc/4.0/).

You are free to use, modify, and share Miguel for non-commercial purposes with attribution. See [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [Agno](https://github.com/agno-agi/agno) — the agent framework
- Powered by [Claude](https://anthropic.com) (Anthropic) — the LLM backbone
- Web search via [DuckDuckGo](https://duckduckgo.com)
