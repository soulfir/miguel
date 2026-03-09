"""Outer improvement loop for Miguel. PROTECTED — the agent cannot modify this file."""

import importlib
import subprocess
import sys
from pathlib import Path

from miguel.display import (
    console,
    print_batch_header,
    print_error,
    print_success,
    print_warning,
    render_stream,
)
from miguel.tests.test_agent_health import run_all_checks

MIGUEL_PKG_DIR = Path(__file__).parent
AGENT_DIR = MIGUEL_PKG_DIR / "agent"
PROJECT_DIR = MIGUEL_PKG_DIR.parent


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )


def _git_init_if_needed() -> None:
    if not (PROJECT_DIR / ".git").exists():
        subprocess.run(["git", "init"], cwd=PROJECT_DIR, capture_output=True, text=True)
        subprocess.run(["git", "add", "-A"], cwd=PROJECT_DIR, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "Initial Miguel v0"], cwd=PROJECT_DIR, capture_output=True, text=True)
        print_success("Initialized git repository.")


def _git_snapshot(label: str) -> None:
    _git("add", "miguel/agent/")
    result = _git("diff", "--cached", "--quiet")
    if result.returncode != 0:
        _git("commit", "-m", f"snapshot: {label}")


def _git_rollback() -> None:
    _git("checkout", "--", "miguel/agent/")
    # Also clean any new untracked files the agent may have created
    _git("clean", "-fd", "miguel/agent/")


def _git_commit_batch(batch_num: int, summary: str) -> None:
    _git("add", "miguel/agent/")
    result = _git("diff", "--cached", "--quiet")
    if result.returncode != 0:
        _git("commit", "-m", f"Batch {batch_num}: {summary}")


def _git_push() -> None:
    """Push to remote if one is configured."""
    result = _git("remote")
    if result.stdout.strip():
        push_result = _git("push")
        if push_result.returncode == 0:
            print_success("Pushed to remote.")
        else:
            print_warning(f"Push failed: {push_result.stderr.strip()}")


def _git_check_scope() -> list[str]:
    """Check that only files inside miguel/agent/ were modified."""
    result = _git("diff", "--name-only", "HEAD")
    if result.returncode != 0:
        return []
    changed = [f for f in result.stdout.strip().split("\n") if f]
    out_of_scope = [f for f in changed if not f.startswith("miguel/agent/")]
    if out_of_scope:
        return [f"Files modified outside miguel/agent/: {', '.join(out_of_scope)}"]
    return []


# ---------------------------------------------------------------------------
# Agent loading
# ---------------------------------------------------------------------------

def _load_agent_fresh():
    """Reload agent modules and create a fresh agent instance."""
    modules_to_clear = [key for key in sys.modules if key.startswith("miguel.agent")]
    for mod in modules_to_clear:
        del sys.modules[mod]

    import miguel.agent.core
    importlib.reload(miguel.agent.core)
    return miguel.agent.core.create_agent()


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------

def _read_file_safe(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError:
        return "(file not found)"


def _build_meta_prompt(batch_num: int) -> str:
    capabilities = _read_file_safe(AGENT_DIR / "capabilities.json")
    improvements = _read_file_safe(AGENT_DIR / "improvements.md")
    core_source = _read_file_safe(AGENT_DIR / "core.py")
    prompts_source = _read_file_safe(AGENT_DIR / "prompts.py")

    # Truncate improvements log to last 3000 chars to stay within context
    if len(improvements) > 3000:
        improvements = "...(truncated)...\n" + improvements[-3000:]

    agent_dir = str(AGENT_DIR.resolve())

    return f"""You are running improvement batch #{batch_num}.

YOUR AGENT DIRECTORY (absolute path): {agent_dir}
All file operations MUST use absolute paths under this directory.
Use write_file for writing files. NEVER use save_to_file_and_run to write files.

YOUR CURRENT SOURCE CODE (agent/core.py):
```python
{core_source}
```

YOUR CURRENT PROMPTS (agent/prompts.py):
```python
{prompts_source}
```

CAPABILITIES CHECKLIST:
{capabilities}

RECENT IMPROVEMENTS:
{improvements}

INSTRUCTIONS:
1. Use get_next_capability to find the highest-priority unchecked capability
2. If ALL_CHECKED: use add_capability to create 3 new capabilities first, then pick one
3. Implement the capability by modifying your files in agent/ using write_file with ABSOLUTE paths
4. Use check_capability to mark it as completed
5. Use log_improvement to record what you did and which files you changed
6. If ANY tool call fails: diagnose the root cause, fix it, do NOT retry the same thing

Make exactly ONE focused improvement this batch. Be precise and ensure valid Python syntax."""


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_improvement_loop(n_batches: int) -> None:
    """Run n improvement batches."""
    _git_init_if_needed()

    succeeded = 0
    failed = 0

    for batch_num in range(1, n_batches + 1):
        print_batch_header(batch_num, n_batches)

        # 1. Snapshot current state
        _git_snapshot(f"pre-batch-{batch_num}")

        # 2. Load fresh agent
        try:
            agent = _load_agent_fresh()
        except Exception as e:
            print_error(f"Failed to load agent: {e}")
            _git_rollback()
            failed += 1
            continue

        # 3. Build meta-prompt
        meta_prompt = _build_meta_prompt(batch_num)

        # 4. Run agent with streaming
        try:
            stream = agent.run(meta_prompt, stream=True, stream_events=True)
            render_stream(stream)
        except Exception as e:
            print_error(f"Agent execution failed: {e}")
            _git_rollback()
            failed += 1
            continue

        # 5. Validate
        console.print()
        console.print("[dim]Running validation checks...[/dim]")

        errors = run_all_checks()
        scope_errors = _git_check_scope()
        errors.extend(scope_errors)

        if not errors:
            # Extract summary from improvements.md (last entry)
            improvements_text = _read_file_safe(AGENT_DIR / "improvements.md")
            lines = improvements_text.strip().split("\n")
            summary_line = "improvement"
            for line in reversed(lines):
                if line.startswith("**Summary:**"):
                    summary_line = line.replace("**Summary:**", "").strip()
                    break

            _git_commit_batch(batch_num, summary_line)
            print_success(f"Batch {batch_num} succeeded: {summary_line}")
            succeeded += 1
        else:
            print_error(f"Batch {batch_num} failed validation:")
            for err in errors:
                print_error(f"  - {err}")
            _git_rollback()
            print_warning("Rolled back to previous state.")
            failed += 1

    # Push all batch commits to remote
    if succeeded > 0:
        _git_push()

    console.print()
    console.rule("[bold]Summary[/bold]", style="cyan")
    console.print(f"  Completed: {succeeded + failed}/{n_batches}")
    console.print(f"  [green]Succeeded: {succeeded}[/green]")
    console.print(f"  [red]Failed: {failed}[/red]")
    console.print()
