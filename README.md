# Miguel

A self-improving AI agent that iteratively enhances its own architecture, tools, and capabilities — safely sandboxed inside Docker.

## What is Miguel?

Miguel is an AI agent built on [Agno](https://github.com/agno-agi/agno) and powered by Claude Opus 4.6 that can **modify its own source code**. It runs in improvement batches — each batch reviews its own code, picks the next unchecked capability from a checklist, implements it, and validates the result. When all capabilities are checked, the agent generates new ones autonomously.

You can also chat with Miguel interactively — ask questions, have it work with your files, or trigger improvements from the REPL.

## Architecture

Miguel's agent runs inside a **Docker container**, while the CLI, validation, and git operations run on your host machine. The agent communicates via a FastAPI server with SSE streaming.

```
HOST (your machine)                           DOCKER CONTAINER (sandboxed)
┌──────────────────────────────┐              ┌──────────────────────────────┐
│  miguel CLI (cli.py)         │              │  FastAPI server (port 8420)  │
│  Improvement runner          │   HTTP/SSE   │                              │
│  Git commit/push             │ ◄──────────► │  Agent + all tool execution  │
│  Validation checks           │              │  Shell, Python, file I/O     │
│  Terminal display             │              │                              │
└──────────────────────────────┘              └──────────────────────────────┘
```

**Volume mounts:**
| Host path | Container path | Access |
|-----------|---------------|--------|
| Entire project | `/app` | Read-only |
| `miguel/agent/` | `/app/miguel/agent` | Read-write |
| `user_files/` | `/app/user_files` | Read-write |

The agent can only write to its own code (`miguel/agent/`) and the shared `user_files/` directory. Everything else — including `cli.py`, `runner.py`, `pyproject.toml` — is physically read-only inside the container.

## Safety

Multiple layers of protection:

1. **Docker isolation** — the agent process cannot access host files beyond the mounted volumes
2. **Read-only mounts** — protected files (CLI, runner, tests) are mounted read-only
3. **AST validation** — all Python files are syntax-checked after each batch
4. **Schema validation** — capabilities.json is verified for correct structure
5. **Import validation** — the agent is re-instantiated to verify it still loads
6. **Scope check** — `git diff` rejects changes outside `miguel/agent/`
7. **Git rollback** — failed batches are reverted automatically

## Setup

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

## Usage

### Interactive Mode

```bash
miguel
```

Chat with Miguel, check capabilities, or trigger improvements from the REPL:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/capabilities` | Show the capability checklist |
| `/improve N` | Run N improvement batches |
| `/history` | Show the improvement log |
| `/quit` | Exit |

### Improvement Mode

```bash
miguel improve 5    # Run 5 improvement batches
```

Each batch: snapshot → agent picks capability → implements it → validate → commit + push (or rollback).

### User Files

Drop files in the `user_files/` directory to share them with Miguel. He can read, write, and manipulate anything there. Ask him to analyze a file, transform data, generate reports, etc.

## How the Improvement Loop Works

```
┌──────────────────────────────────────────────────┐
│              IMPROVEMENT BATCH                   │
│                                                  │
│  1. Git snapshot current state                   │
│  2. Reload agent in Docker container             │
│  3. Agent reads its own code + checklist         │
│  4. Agent picks next unchecked capability        │
│  5. Agent modifies its own code (inside Docker)  │
│  6. Host validates (AST, imports, schema, scope) │
│  7. Pass → git commit + push                     │
│     Fail → git rollback                          │
│  8. Repeat                                       │
└──────────────────────────────────────────────────┘
```

## Project Structure

```
Miguel/
├── Dockerfile                     # Container image definition
├── docker-compose.yml             # Container config + volume mounts
├── pyproject.toml                 # Project dependencies + CLI entry point
├── .env                           # API key (gitignored)
├── user_files/                    # Shared workspace for user files
├── miguel/
│   ├── cli.py                     # CLI entry point (host)
│   ├── runner.py                  # Improvement loop + git ops (host)
│   ├── display.py                 # Terminal renderer (host)
│   ├── client.py                  # HTTP client for container (host)
│   ├── container.py               # Docker lifecycle management (host)
│   ├── tests/
│   │   └── test_agent_health.py   # Validation checks (host)
│   └── agent/                     # MUTABLE — Miguel modifies everything here
│       ├── server.py              # FastAPI server (container)
│       ├── core.py                # Agent factory
│       ├── prompts.py             # System prompts
│       ├── config.py              # Agent config
│       ├── capabilities.json      # Capability checklist
│       ├── improvements.md        # Improvement log
│       └── tools/                 # Custom tools
│           ├── error_utils.py     # Safe tool decorator + utilities
│           ├── capability_tools.py
│           ├── self_tools.py
│           ├── prompt_tools.py
│           ├── tool_creator.py
│           ├── recovery_tools.py
│           └── dep_tools.py
```

## The Capability Checklist

Miguel starts with 10 seed capabilities. As it checks them off, it generates new ones:

| ID | Title | Category |
|---|---|---|
| cap-001 | Respond to basic questions | core |
| cap-002 | Read and explain own source code | self-awareness |
| cap-003 | Modify own instructions/prompts | self-improvement |
| cap-004 | Create new custom tools | self-improvement |
| cap-005 | Error handling and recovery | robustness |
| cap-006 | Execute and validate Python code | capability |
| cap-007 | Maintain improvement context | memory |
| cap-008 | Validate own code before writing | safety |
| cap-009 | Refactor and optimize existing code | quality |
| cap-010 | Generate new capabilities autonomously | self-improvement |

## Improvement Log

See [`miguel/agent/improvements.md`](miguel/agent/improvements.md) for a running log of every improvement Miguel has made to itself.
