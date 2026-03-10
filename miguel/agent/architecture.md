# Miguel Architecture Map

## Overview
Miguel is a self-improving AI agent built on **Agno** (framework) + **Claude** (LLM). It operates as an **Agno Team in `coordinate` mode** — a coordinator with three sub-agents, context-aware execution, and persistent memory/planning.

## Directory Structure
```
agent/
├── core.py              # Agent/Team factory — assembles coordinator + sub-agents + tools
├── team.py              # Sub-agent definitions (Coder, Researcher, Analyst)
├── config.py            # Settings: model ID, version, context limits, paths
├── prompts.py           # System prompt builder — defines identity & behavior rules
├── server.py            # FastAPI server — batch mode (Agent) + interactive mode (Team)
├── architecture.md      # This file
├── capabilities.json    # Capability checklist (checked/unchecked)
├── improvements.md      # Log of all self-improvements
├── memory.db            # Persistent memory (SQLite)
├── planning.db          # Task plans + progress (SQLite)
└── tools/
    ├── error_utils.py           # Foundation: @safe_tool decorator, safe_write, validate_python
    ├── capability_tools.py      # Capability checklist CRUD
    ├── self_tools.py            # Self-inspection: read_own_file, list_own_files, get_architecture, log_improvement
    ├── prompt_tools.py          # Safe prompt modification with syntax validation
    ├── tool_creator.py          # Create new tools + auto-register in core.py
    ├── recovery_tools.py        # Backups, health_check, file validation
    ├── context_tools.py         # Context window monitoring + auto-compaction
    ├── memory_tools.py          # Persistent memory: remember, recall, forget, list_memories
    ├── planning_tools.py        # Task planning: plans, tasks, dependencies, progress tracking
    ├── web_tools.py             # DuckDuckGo search (text + news)
    ├── api_tools.py             # HTTP client + 10 pre-built API integrations
    ├── file_analysis_tools.py   # CSV/Excel, PDF, image analysis + pandas queries
    ├── reddit_tools.py          # Reddit OAuth2: browse, post, comment, search
    └── dep_tools.py             # Dependency management (pip install + record)
```

## Team Architecture
```
                    Miguel (Coordinator)
                   Agno Team — coordinate mode
                   52 tools, memory, planning
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
         Coder       Researcher     Analyst
       (6 tools)     (7 tools)    (6 tools)
      Python exec   Web search    CSV/Excel
      Shell cmds    News search   PDF extract
      File write    HTTP client   Image analyze
      Validation    API calls     Pandas query
```

**How it works:** User message → coordinator assesses complexity → simple tasks handled directly, complex tasks delegated to sub-agents with fresh context → results synthesized and returned.

## Key Design Decisions

1. **Context as cognitive capacity** — Every prompt token reduces thinking space. Prompts encode judgment, not tool docs (tool schemas already provide docs).
2. **Sub-agents for context isolation** — Heavy tasks get fresh context windows via delegation.
3. **Memory as external storage** — SQLite-backed memory bridges conversations and sub-agent boundaries.
4. **Safety layers** — Docker isolation, read-only mounts, path validation, AST validation, atomic writes, automatic backups, git rollback.
5. **Shared utilities** — `error_utils.py` provides `@safe_tool`, `validate_python`, `safe_write` used across all tools.
6. **Centralized config** — Model IDs, context limits, and paths in `config.py`, imported where needed.

## Data Flow
1. **User request** → coordinator → assess complexity → handle or delegate
2. **Self-improvement** → read checklist → implement → validate → mark done → log
3. **Error recovery** → health_check → diagnose → recover_backup or fix
4. **Memory** → remember() to store → recall() to retrieve → persists in SQLite
5. **Planning** → create_plan → add tasks → work through → auto-complete
6. **Context monitoring** → check_context → auto_compact when critical → recall to recover