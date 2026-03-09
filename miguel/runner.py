"""Outer improvement loop for Miguel. PROTECTED — the agent cannot modify this file."""

import re
import subprocess
from pathlib import Path

from miguel.client import reload_agent, stream_from_container
from miguel.container import ensure_container
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

# Container path the agent sees inside Docker
CONTAINER_AGENT_DIR = "/app/miguel/agent"


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


def _git_commit_runner_changes() -> None:
    """Commit any pending changes made by the runner itself (outside miguel/agent/).

    This catches things like pyproject.toml modifications from _merge_added_deps()
    so they never leak into the next batch's scope check.
    """
    _git("add", "--all")
    # Unstage agent files — those are handled separately by _git_snapshot/_git_commit_batch
    _git("reset", "HEAD", "--", "miguel/agent/")
    result = _git("diff", "--cached", "--quiet")
    if result.returncode != 0:
        _git("commit", "-m", "chore: runner-managed file updates")


def _git_snapshot(label: str) -> None:
    # First, commit any stray runner-side changes so they don't pollute this batch
    _git_commit_runner_changes()
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

    return f"""You are running improvement batch #{batch_num}.

YOUR AGENT DIRECTORY (absolute path): {CONTAINER_AGENT_DIR}
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

def _merge_added_deps():
    """If the agent added dependencies via dep_tools, merge them into pyproject.toml."""
    added_deps_path = AGENT_DIR / "added_deps.txt"
    if not added_deps_path.exists():
        return

    new_deps = [d.strip() for d in added_deps_path.read_text().splitlines() if d.strip()]
    if not new_deps:
        added_deps_path.unlink()
        return

    pyproject_path = PROJECT_DIR / "pyproject.toml"
    content = pyproject_path.read_text()

    for dep in new_deps:
        # Check if already present (normalize hyphens/underscores)
        base_name = dep.split("[")[0]
        normalized = base_name.lower().replace("-", "[-_]").replace("_", "[-_]")
        if re.search(rf'"{normalized}', content, re.IGNORECASE):
            continue

        # Insert after the last dependency line
        lines = content.split("\n")
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('"') and lines[i].strip().endswith('",'):
                lines.insert(i + 1, f'    "{dep}",')
                content = "\n".join(lines)
                break

    pyproject_path.write_text(content)
    added_deps_path.unlink()

    # Commit pyproject.toml immediately so it doesn't leak into the next batch's scope check
    _git("add", "pyproject.toml")
    _git("commit", "-m", f"Add dependencies: {', '.join(new_deps)}")
    print_success(f"Merged {len(new_deps)} new dependency(ies) into pyproject.toml.")


def run_improvement_loop(n_batches: int) -> None:
    """Run n improvement batches."""
    _git_init_if_needed()

    # Ensure Docker container is running
    console.print("[dim]Starting Docker container...[/dim]")
    if not ensure_container():
        print_error("Docker container failed to start. Is Docker running?")
        return

    console.print("[dim]Running agent in Docker container.[/dim]")

    succeeded = 0
    failed = 0

    for batch_num in range(1, n_batches + 1):
        print_batch_header(batch_num, n_batches)

        # 1. Snapshot current state
        _git_snapshot(f"pre-batch-{batch_num}")

        # 2. Reload agent in container
        try:
            reload_agent()
        except Exception as e:
            print_error(f"Failed to reload agent: {e}")
            _git_rollback()
            failed += 1
            continue

        # 3. Build meta-prompt
        meta_prompt = _build_meta_prompt(batch_num)

        # 4. Run agent with streaming
        try:
            stream = stream_from_container(meta_prompt)
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

        if not errors:
            # Merge any new dependencies the agent added
            _merge_added_deps()

            # Extract summary from improvements.md (last entry)
            improvements_text = _read_file_safe(AGENT_DIR / "improvements.md")
            lines = improvements_text.strip().split("\n")
            summary_line = "improvement"
            for line in reversed(lines):
                if line.startswith("**Summary:**"):
                    summary_line = line.replace("**Summary:**", "").strip()
                    break

            _git_commit_batch(batch_num, summary_line)
            _git_push()
            print_success(f"Batch {batch_num} succeeded: {summary_line}")
            succeeded += 1
        else:
            print_error(f"Batch {batch_num} failed validation:")
            for err in errors:
                print_error(f"  - {err}")
            _git_rollback()
            print_warning("Rolled back to previous state.")
            failed += 1

    console.print()
    console.rule("[bold]Summary[/bold]", style="cyan")
    console.print(f"  Completed: {succeeded + failed}/{n_batches}")
    console.print(f"  [green]Succeeded: {succeeded}[/green]")
    console.print(f"  [red]Failed: {failed}[/red]")
    console.print()
