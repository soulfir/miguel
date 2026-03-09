# Miguel

A self-improving AI agent that iteratively enhances its own architecture, tools, and capabilities.

## What is Miguel?

Miguel is an AI agent built on the [Agno](https://github.com/agno-agi/agno) framework that can **modify its own source code**. It runs in improvement batches — each batch reviews its own code, picks the next unchecked capability from a checklist, implements it, and validates the result. When all capabilities are checked, the agent generates new ones autonomously.

The agent is powered by Claude Opus 4.6.

## How It Works

```
┌─────────────────────────────────────────────┐
│              IMPROVEMENT LOOP               │
│                                             │
│  1. Git snapshot current state              │
│  2. Load agent fresh                        │
│  3. Agent reads its own code + checklist    │
│  4. Agent picks next unchecked capability   │
│  5. Agent modifies its own code             │
│  6. Validate (AST, imports, schema)         │
│  7. Pass → git commit │ Fail → git rollback │
│  8. Repeat                                  │
└─────────────────────────────────────────────┘
```

### Safety Boundary

Miguel can only modify files inside `miguel/agent/`. The outer loop (`runner.py`, `cli.py`, `display.py`) is **protected** — the agent cannot touch it. Every batch is validated with:

- AST syntax checking on all Python files
- JSON schema validation on the capabilities checklist
- Import + instantiation test (can the agent still load?)
- Scope check (did it modify anything outside `miguel/agent/`?)

If any check fails, the batch is rolled back via git.

## Project Structure

```
Miguel/
├── pyproject.toml              # Project config
├── README.md
├── miguel/
│   ├── cli.py                  # PROTECTED — CLI entry point
│   ├── runner.py               # PROTECTED — improvement loop + validation
│   ├── display.py              # PROTECTED — terminal renderer
│   ├── tests/
│   │   └── test_agent_health.py  # PROTECTED — health checks
│   └── agent/                  # MUTABLE — Miguel modifies everything here
│       ├── core.py             # Agent factory
│       ├── prompts.py          # System prompts
│       ├── config.py           # Agent config
│       ├── capabilities.json   # Capability checklist
│       ├── improvements.md     # Improvement log
│       └── tools/              # Custom tools
│           ├── capability_tools.py
│           └── self_tools.py
```

## Usage

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Add your Anthropic API key to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### Interactive Mode

```bash
miguel
```

Chat with Miguel, check capabilities, or trigger improvements from the REPL:
- `/help` — show commands
- `/capabilities` — show the checklist
- `/improve N` — run N improvement batches
- `/history` — show improvement log
- `/quit` — exit

### Improvement Mode

```bash
miguel improve 5    # Run 5 improvement batches
```

Each batch picks the next capability, implements it, validates, and commits.

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
