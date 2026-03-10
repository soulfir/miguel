# Miguel Improvement Log

Each entry records: batch number, timestamp, what changed, and why.

---

### 2026-03-09 11:27:37 UTC
**Summary:** Batch #1: Implemented cap-001 (Respond to basic questions). Added a comprehensive 'Core Behavior: Answering Questions' section to the system prompt in prompts.py. This gives Miguel clear instructions for its primary function: answering user questions directly, honestly, using tools to verify facts, working step-by-step on technical problems, formatting with markdown, asking for clarification when needed, and scaling response length to question complexity.
**Files changed:** prompts.py

### 2026-03-09 11:46:50 UTC
**Summary:** Batch #2: Implemented cap-002 (Read and explain own source code). Created architecture.md — a structured self-describing map of Miguel's entire codebase, covering directory structure, key components, data flow, and security boundaries. Added a new `get_architecture()` tool in self_tools.py that returns this map on demand. Registered the tool in core.py. Enhanced the Self-Awareness section of prompts.py to instruct Miguel to use get_architecture first when asked about itself, and to explain both WHAT and WHY for each component, using analogies to make things accessible.
**Files changed:** architecture.md, tools/self_tools.py, core.py, prompts.py

### 2026-03-09 11:53:40 UTC
**Summary:** Batch #3: Implemented cap-003 (Modify own instructions and prompts). Created tools/prompt_tools.py with two new tools: `get_prompt_sections()` lists all sections in the system prompt with line counts, and `modify_prompt_section(section_name, new_content, action)` safely modifies prompt sections with AST-based parsing and syntax validation before writing. Supports 'replace', 'append', and 'add_new' actions. Handles f-strings with {AGENT_DIR} correctly. Registered both tools in core.py. Updated the Self-Improvement Process section of prompts.py to document the new tools. Updated architecture.md with the new component description.
**Files changed:** tools/prompt_tools.py, core.py, prompts.py, architecture.md

### 2026-03-09 12:07:08 UTC
**Summary:** Batch #4: Implemented cap-004 (Create new custom tools). Created tools/tool_creator.py with two tools: `create_tool(file_name, code, register)` creates a new tool file in tools/ with full validation (syntax checking, public function extraction, docstring enforcement) and auto-registers it in core.py (adds import + tools list entry). `add_functions_to_tool(file_name, new_code)` appends new functions to an existing tool file with conflict detection and auto-registration. Both tools validate core.py syntax after modification to prevent self-corruption. Fixed Python 3.14 compatibility by using `ast.Constant` instead of deprecated `ast.Str`. Registered both tools in core.py. Updated prompts.py Guidelines section to recommend using create_tool(). Updated architecture.md with the new component description.
**Files changed:** tools/tool_creator.py, core.py, prompts.py, architecture.md

### 2026-03-09 12:26:00 UTC
**Summary:** Batch #5: Implemented cap-005 (Error handling and recovery). Three-layer approach: (1) Fixed error_utils.py — moved `json` import to top of file (was imported after use in decorator), added `safe_write()` for atomic file writes with automatic .bak backups and security checks, added `validate_python()` as a reusable syntax checker, and `list_backups()` to discover all .bak files. (2) Created tools/recovery_tools.py with four new tools: `recover_backup(file_path)` restores any file from its .bak backup with syntax validation and verification; `list_recovery_points()` shows all available backups; `validate_agent_file(file_path)` checks Python files for syntax errors and missing docstrings; `health_check()` runs a comprehensive diagnostic checking all critical files exist, validating every Python file's syntax, verifying capabilities.json structure, and listing backup files. (3) Registered all four tools in core.py. Updated prompts.py Error Handling section to document recovery tools. Updated architecture.md with new component descriptions and a new Error Handling Strategy section.
**Files changed:** tools/error_utils.py, tools/recovery_tools.py, core.py, prompts.py, architecture.md

### 2026-03-09 16:49:53 UTC
**Summary:** Batch #1: Implemented cap-011 (Web search and information retrieval). Created tools/web_tools.py with three DuckDuckGo-powered search tools: `web_search(query, max_results)` for general web search returning formatted results with titles, URLs, and snippets; `web_news(query, max_results)` for searching recent news articles with dates and sources; `web_search_detailed(query, region, max_results)` for detailed searches with region filtering that returns structured JSON output. All three tools use lazy imports (duckduckgo_search imported at call time to avoid startup overhead), the @safe_tool decorator for graceful error handling, and input sanitization (clamping max_results to 1-20). Installed duckduckgo-search as a new dependency. Registered all three tools in core.py imports and tools list. Added "Web Search and Research" section to prompts.py with guidance on when and how to use search. Updated architecture.md with the new component description and data flow. Verified end-to-end: both web_search and web_news return real, current results.
**Files changed:** tools/web_tools.py, core.py, prompts.py, architecture.md

### 2026-03-09 17:02:13 UTC
**Summary:** Batch #1: Implemented cap-012 (Persistent memory across sessions). Created tools/memory_tools.py with four SQLite-backed memory tools: `remember(key, value, category)` stores information with automatic upsert (same key+category updates instead of duplicating); `recall(query, category, limit)` searches memories by keyword across both keys and values with case-insensitive LIKE matching; `forget(memory_id)` deletes specific memories by ID; `list_memories(category, limit)` browses all memories grouped by category. Categories supported: 'fact', 'preference', 'context', 'summary'. Data persists in memory.db (SQLite) with indexed columns for fast lookups. All functions use @safe_tool decorator for graceful error handling. No external dependencies — uses Python's built-in sqlite3. Registered all four tools in core.py. Added "Persistent Memory" section to prompts.py with detailed guidance on when and how to use memory (store user names/preferences, recall context at conversation start, summarize completed tasks). Updated architecture.md with new component description, directory listing, and data flow. Verified all tools work end-to-end with store/recall/update/delete cycle.
**Files changed:** tools/memory_tools.py, core.py, prompts.py, architecture.md

### 2026-03-09 17:06:09 UTC
**Summary:** Batch #2: Implemented cap-013 (Structured task planning and decomposition). Created tools/planning_tools.py with seven SQLite-backed planning tools: `create_plan(title, description, tasks)` creates plans with optional comma-separated task list pre-population; `add_task(plan_id, title, description, depends_on)` adds tasks with dependency support — tasks auto-set to 'blocked' if dependencies aren't done, with validation that deps exist in the same plan; `update_task(task_id, status)` changes task status with cascade effects — completing a task auto-unblocks dependents when all their deps are satisfied, and auto-completes the plan when all tasks are done/skipped; `show_plan(plan_id)` displays a rich plan view with visual progress bar (█░), status counts, dependency chains, and full task list; `list_plans(status)` lists plans filtered by status with completion percentages; `get_next_task(plan_id)` finds the next actionable task (prioritizing in-progress, then pending); `remove_plan(plan_id)` permanently deletes a plan and its tasks. Data persists in planning.db (SQLite) with foreign keys enforced and indexed columns. Schema: plans(id, title, description, status, timestamps) and tasks(id, plan_id, title, description, status, order_index, depends_on JSON, timestamps). All functions use @safe_tool decorator. No external dependencies — uses Python's built-in sqlite3 and json. Registered all seven tools in core.py. Added "Task Planning and Decomposition" section to prompts.py with guidance on when to use planning and best practices. Updated architecture.md with new component description, directory listing, data flow step, and detailed tool documentation. Also fixed minor indentation inconsistency in core.py's tools list. Verified all tools end-to-end with create/add/update/dependency/cascade/cleanup cycle.
**Files changed:** tools/planning_tools.py, core.py, prompts.py, architecture.md

### 2026-03-09 17:45:15 UTC
**Summary:** Batch #1: Implemented cap-014 (File analysis — PDF, CSV, images, and structured data). Created tools/file_analysis_tools.py with four tools: `analyze_csv(file_path, max_rows, query)` loads and analyzes tabular data files (CSV, TSV, Excel, JSON, Parquet) showing shape, column types with non-null/unique counts, numeric statistics via pandas describe, missing value summary with percentages, and sample data — supports optional pandas query filtering; `analyze_pdf(file_path, max_pages, page_range)` extracts text from PDFs using PyMuPDF with metadata extraction (title, author, subject, creator, producer), page-by-page text output with word/character counts, configurable page ranges ("1-5", "1,3,7"), and detection of scanned/image-based pages; `analyze_image(file_path)` analyzes image files (PNG, JPEG, GIF, BMP, TIFF, WebP via Pillow) reporting format, mode, dimensions, file size, DPI, animation info, EXIF metadata (camera make/model, exposure, focal length, GPS), color analysis with dominant colors via quantized palette and channel statistics, plus brightness estimation; `csv_query(file_path, query)` runs arbitrary pandas expressions on data files using a restricted eval namespace (no builtins) for safety, with helpful error messages showing column names and query tips. All tools use smart file path resolution that checks agent dir, user files dir, and absolute paths. Installed four dependencies: pymupdf, pandas, openpyxl, Pillow. All functions use @safe_tool decorator for graceful error handling. Registered all four tools in core.py. Added "File Analysis and Data Processing" section to prompts.py with guidance on when and how to use each tool. Updated architecture.md with new component description, directory listing, data flow step, and detailed tool documentation. Updated README.md to reflect cap-014 completion, new tool count (35+), file analysis features, and updated capability status table. Verified all tools end-to-end with test CSV/PDF/image creation, analysis, querying, and cleanup.
**Files changed:** tools/file_analysis_tools.py, core.py, prompts.py, architecture.md, README.md

### 2026-03-09 17:52:46 UTC
**Summary:** Batch #2: Implemented cap-015 (API integration framework). Created tools/api_tools.py with four tools: `http_request(url, method, headers, body, params, auth_type, auth_value, timeout, include_headers)` — a full-featured HTTP client supporting all HTTP methods (GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS), custom headers and query parameters via JSON strings, request bodies with automatic JSON detection and Content-Type handling, four authentication modes (Bearer token, Basic auth, API key in header, API key in query param), automatic response parsing for JSON/XML/HTML/plain text, configurable timeout (1-120s), response truncation for large payloads (5000 char limit), and custom User-Agent; `api_get(url, params, headers)` — convenience wrapper for quick GET requests; `api_post(url, body, headers)` — convenience wrapper for POST with auto JSON detection; `api_quickstart(service, query)` — pre-built integrations for 10 free, no-API-key-required services: weather conditions via wttr.in (temperature, humidity, wind, UV, precipitation), IP geolocation via ip-api.com (city, region, country, ISP, coordinates, timezone), currency exchange rates via Frankfurter API using ECB data (with amount conversion), random programming jokes via official-joke-api, UUID generation via httpbin.org, request header inspection via httpbin.org, current time in any timezone via worldtimeapi.org (with fuzzy timezone matching on 404), country information via restcountries.com (population, area, languages, currencies, flag emoji), and GitHub user profiles via GitHub API (repos, followers, bio, location). All response output is beautifully formatted with markdown tables. Installed `requests` as a dependency. All functions use @safe_tool decorator for graceful error handling and lazy-import `requests` to avoid startup overhead. Registered all four tools in core.py. Added "API Integration and HTTP Client" section to prompts.py with usage guidance. Updated architecture.md with new component description (tools/api_tools.py), directory listing, data flow step #11, and detailed tool documentation. Updated README.md to reflect cap-015 completion, 40+ tool count, API integration features, new tool category table row, and updated capability status table. Verified all tools end-to-end: import check, quickstart list, GET/POST with httpbin.org, bearer auth with query params, exchange rate conversion, GitHub user lookup, country info lookup, IP geolocation, error handling for unknown services and invalid methods, and full agent instantiation (40 tools loaded).
**Files changed:** tools/api_tools.py, core.py, prompts.py, architecture.md, README.md

### 2026-03-10 11:17:12 UTC
**Summary:** Batch #1: Implemented cap-017 (Evolve into Agno Team with sub-agent delegation). Refactored Miguel from a single Agent into an Agno Team in `coordinate` mode. Created `team.py` with three specialized sub-agents: **Coder** (6 tools: Python execution, shell commands, filesystem, validation), **Researcher** (7 tools: web search, news, HTTP client, API integrations), and **Analyst** (6 tools: CSV/Excel analysis, PDF extraction, image analysis, pandas queries). The main coordinator keeps all 44 tools and can either handle tasks directly or delegate to sub-agents via Agno's built-in `delegate_task_to_member` tool. Updated `core.py` with two factory functions: `create_agent()` (plain Agent for batch mode) and `create_team()` (Team with sub-agents for interactive mode). Extracted `COORDINATOR_TOOLS` as a shared list. Updated `server.py` to use Team for interactive mode and plain Agent for batch mode — both share the same SSE streaming interface. Updated `prompts.py` with delegation guidance section. Updated `__init__.py` to export `create_team`. Updated `architecture.md` with team architecture diagram and component descriptions. Updated `README.md` with team architecture documentation, updated capability table (cap-017 marked done), and team architecture diagrams. All files validated with health_check — no syntax errors. Before/after: core.py 150→198 lines (+48), prompts.py 190→208 lines (+18), new file team.py 146 lines, server.py unchanged at 84 lines.
**Files changed:** core.py, team.py, server.py, prompts.py, __init__.py, architecture.md, README.md

### 2026-03-10 11:23:10 UTC
**Summary:** Batch #2: Implemented cap-018 (Context-aware execution strategy). Added permanent rules to prompts.py for strategic context management and delegation. Three key changes to the system prompt:

1. **New section: "Context-Aware Execution Strategy"** (19 lines) — Encodes the 4 Rules of Context Management: (1) primary work first, secondary work last; (2) delegate heavy lifting to sub-agents; (3) use memory as external storage via `remember()`; (4) plan before executing complex tasks. Includes a complexity assessment framework (simple/medium/complex/project-scale) and explicit anti-patterns to avoid.

2. **Enhanced "Self-Improvement Process" section** (19 lines, up from 12) — Added context-aware batch rules: always write primary implementation code first, delegate heavy code generation to Coder, use memory for intermediate results across sub-agent boundaries, never let documentation crowd out primary work.

3. **Enhanced "Team Architecture and Sub-Agent Delegation" section** (15 lines, down from 17 — more concise) — Replaced vague delegation guidance with a concrete decision framework: delegate when >50 lines of code or >20% context consumption; handle directly when <5 tool calls or needs orchestration/memory/planning. Added the key principle that context = cognitive capacity and delegation buys fresh context.

Updated architecture.md with context-aware execution strategy documentation, complexity tiers, and revised data flow. Updated README.md with cap-018 marked done, context-aware features highlighted, complexity tier table, and updated improvement loop diagram showing primary-work-first ordering.

Before/after metrics: prompts.py 197→224 lines (+27 net), 44 tools (unchanged — this is a prompt/judgment improvement, not a tool addition). The +27 lines encode decision-making judgment that should make future batches more efficient by preventing context exhaustion.
**Files changed:** prompts.py, architecture.md, README.md

### 2026-03-10 11:35:06 UTC
**Summary:** Batch #1: Implemented cap-019 (Context window awareness and auto-compaction). Created `tools/context_tools.py` with two new tools:

1. **`check_context(conversation_chars, model_id)`** — Estimates context window usage based on character count (3.5 chars/token heuristic). Returns a traffic-light status report:
   - ✅ COMFORTABLE (<60%): continue normally
   - ⚠️ WARNING (60-80%): delegate heavy work, be concise, use memory
   - 🔴 CRITICAL (>80%): auto-compact immediately, delegate or finish primary work

2. **`auto_compact(task_description, progress_summary, remaining_work, key_decisions)`** — Saves structured task state to persistent memory (via memory.db) for seamless recovery. Produces a compact snapshot that can be recalled in a new conversation with `recall('compacted_state', category='context')`.

Design decisions:
- Character-based token estimation (3.5 chars/token) — conservative for mixed content (code + natural language)
- 15k token system overhead deducted from 200k model limit = 185k effective tokens
- Uses existing memory.db infrastructure (no new dependencies)
- Both tools wrapped with `@safe_tool` for error handling

Updated `core.py`: Added import for `check_context` and `auto_compact`, added them to `COORDINATOR_TOOLS` list.
Updated `prompts.py`: Added new "Context Window Awareness" section (14 lines) with usage instructions, char estimation guide, threshold behaviors, and recovery instructions.
Updated `architecture.md`: Added context_tools.py to directory tree, updated tool count to 46, documented the context awareness tools and their role in the error handling strategy.
Updated `README.md`: Updated tool count (44→46), added cap-019 to capabilities table as ✅ done, added "Context Awareness" row to tools table, updated architecture diagrams, added context monitoring to feature lists.

Before/after metrics: core.py 198→204 lines (+6), prompts.py 235→252 lines (+17), new file tools/context_tools.py 176 lines. Total: +199 lines of new functionality.
**Files changed:** tools/context_tools.py, core.py, prompts.py, architecture.md, README.md

### 2026-03-10 11:39:38 UTC
**Summary:** Batch #2: Implemented cap-020 (Reddit integration — browse, post, and interact). Created `tools/reddit_tools.py` with 6 new tools:

1. **`reddit_browse(subreddit, sort, limit)`** — Browse posts in a subreddit with sort options (hot/new/top/rising), returns formatted post listings with scores, comment counts, and links.

2. **`reddit_read(post_url_or_id, comment_limit)`** — Read a full post with body text and top comments (with one level of reply nesting). Accepts URLs, fullnames (t3_xxx), or bare IDs.

3. **`reddit_search(query, subreddit, sort, limit)`** — Search all of Reddit or a specific subreddit with sort options (relevance/hot/top/new/comments).

4. **`reddit_post(subreddit, title, body, url, flair_id)`** — Submit text or link posts to any subreddit.

5. **`reddit_comment(thing_id, body)`** — Reply to posts (t3_) or comments (t1_) with Reddit markdown support.

6. **`reddit_user(username)`** — Get user profile info including karma, account age, verification status.

Design decisions:
- Uses Reddit's OAuth2 API directly via `urllib.request` — no PRAW dependency needed
- Credentials from environment variables (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD)
- Token caching with automatic refresh (tokens valid for ~1 hour)
- Graceful error messages when credentials are missing with setup instructions
- All tools wrapped with `@safe_tool` for consistent error handling
- Post/comment formatting with scores, authors, links, and body text truncation
- Prompt instructions include "always confirm with user before posting" safety rule

Updated `core.py`: Added 6 Reddit tool imports and registration in COORDINATOR_TOOLS.
Updated `prompts.py`: Added new "Reddit Integration" section with tool docs and usage guidelines.
Updated `architecture.md`: Added reddit_tools.py to directory tree, updated tool count to 52, documented Reddit tools architecture.
Updated `README.md`: Updated tool count (46→52), added cap-020 as ✅ done, added Reddit row to tools table, added Reddit setup instructions, updated feature lists and architecture diagrams.

Before/after metrics: core.py 204→214 lines (+10), prompts.py 251→270 lines (+19), new file tools/reddit_tools.py 410 lines. Total: +439 lines of new functionality. No new dependencies added — uses only stdlib urllib.request.
**Files changed:** tools/reddit_tools.py, core.py, prompts.py, architecture.md, README.md

### 2026-03-10 11:48:26 UTC
**Summary:** Batch #3: Implemented cap-021 (Architecture consolidation and cleanup). Comprehensive codebase cleanup reducing total lines by 512 (10%) and system prompt by 170 lines (63%).

**Changes made:**

1. **Streamlined prompts.py (270→100 lines, -63%)** — The highest-impact change. Removed all tool documentation sections that duplicated what Agno already sends as tool schemas. The prompt now encodes *judgment and priorities* rather than restating tool docstrings. This saves ~170 lines of context on EVERY request — the single biggest context efficiency gain possible.

2. **Deduplicated validate_python** — `tool_creator.py` had its own `_validate_python()` that was identical to `error_utils.validate_python()`. Replaced with a shared import. Removed unused `re` import and `import re` from tool_creator.py.

3. **Removed unused code** — Removed `format_error()` from `error_utils.py` (was imported by capability_tools.py but never called since `@safe_tool` handles errors). Removed that unused import from capability_tools.py.

4. **Cleaned up config.py (12→22 lines)** — Removed unused `MAX_TOOL_RETRIES` setting. Added `MODEL_CONTEXT_LIMITS` dict (was hardcoded in context_tools.py). Bumped version to 0.2.0. Config is now the single source of truth for model settings.

5. **Centralized model context limits** — `context_tools.py` now imports `MODEL_CONTEXT_LIMITS` from config.py instead of hardcoding them. This follows the DRY principle and makes model changes a single-point update.

6. **Streamlined architecture.md (240→69 lines, -71%)** — Removed content that duplicated README.md. Now a lean quick-reference focused on structure and design decisions.

7. **Updated README.md (411→296 lines, -28%)** — Removed redundant sections, tightened wording, updated cap-021 to ✅ done, updated metrics and capability count to 20/20.

Before/after: Total codebase 5131→4619 lines (-512, -10%). Prompt 270→100 lines (-170, -63%). No functionality removed — all 52 tools and 14 tool modules preserved. All files pass syntax validation. Full integration test (agent creation, team creation, all imports) passes.
**Files changed:** prompts.py, config.py, tools/error_utils.py, tools/tool_creator.py, tools/capability_tools.py, tools/context_tools.py, architecture.md, README.md
