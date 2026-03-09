"""Miguel CLI entry point. PROTECTED — the agent cannot modify this file."""

import json
import uuid

from dotenv import load_dotenv

load_dotenv()

import typer
from rich.console import Console

from miguel.display import print_banner, print_error, print_success, render_stream
from miguel.runner import run_improvement_loop

app = typer.Typer(
    name="miguel",
    help="Miguel — a self-improving AI agent.",
    invoke_without_command=True,
    no_args_is_help=False,
)
console = Console()


def _show_capabilities() -> None:
    """Display the capabilities checklist."""
    from pathlib import Path

    caps_path = Path(__file__).parent / "agent" / "capabilities.json"
    data = json.loads(caps_path.read_text())

    checked = sum(1 for c in data["capabilities"] if c["status"] == "checked")
    total = len(data["capabilities"])
    console.print(f"\n[bold]Capabilities ({checked}/{total}):[/bold]")

    for cap in sorted(data["capabilities"], key=lambda c: c["priority"]):
        mark = "[green][x][/green]" if cap["status"] == "checked" else "[ ]"
        console.print(f"  {mark} {cap['id']}: {cap['title']}")
    console.print()


def _show_history() -> None:
    """Display the improvement log."""
    from pathlib import Path

    log_path = Path(__file__).parent / "agent" / "improvements.md"
    content = log_path.read_text()
    console.print(content)


def _show_help() -> None:
    """Display available REPL commands."""
    console.print(
        """
[bold]Commands:[/bold]
  /help          Show this help message
  /capabilities  Show the capabilities checklist
  /improve N     Run N improvement batches
  /history       Show the improvement log
  /quit          Exit Miguel
"""
    )


def interactive_mode() -> None:
    """Run Miguel in interactive REPL mode."""
    print_banner()

    # Load agent
    try:
        from miguel.agent import create_agent

        agent = create_agent()
    except Exception as e:
        print_error(f"Failed to load agent: {e}")
        raise typer.Exit(1)

    session_id = f"interactive-{uuid.uuid4().hex[:8]}"
    print_success("Agent loaded. Ready.\n")

    while True:
        try:
            user_input = input("miguel> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Handle slash commands
        if user_input == "/quit":
            console.print("Goodbye!")
            break
        elif user_input == "/help":
            _show_help()
            continue
        elif user_input == "/capabilities":
            _show_capabilities()
            continue
        elif user_input == "/history":
            _show_history()
            continue
        elif user_input.startswith("/improve"):
            parts = user_input.split()
            n = int(parts[1]) if len(parts) > 1 else 1
            run_improvement_loop(n)
            # Reload agent after improvements
            try:
                import importlib
                import sys

                modules_to_clear = [k for k in sys.modules if k.startswith("miguel.agent")]
                for mod in modules_to_clear:
                    del sys.modules[mod]
                from miguel.agent import create_agent

                agent = create_agent()
                print_success("Agent reloaded after improvements.")
            except Exception as e:
                print_error(f"Failed to reload agent: {e}")
            continue

        # Send to agent
        try:
            stream = agent.run(user_input, stream=True, stream_events=True, session_id=session_id)
            render_stream(stream)
        except Exception as e:
            print_error(f"Error: {e}")

        console.print()


@app.callback()
def main(ctx: typer.Context) -> None:
    """Miguel — a self-improving AI agent."""
    if ctx.invoked_subcommand is None:
        interactive_mode()


@app.command()
def improve(
    cycles: int = typer.Argument(1, help="Number of improvement cycles to run"),
) -> None:
    """Run improvement batches to make Miguel better."""
    console.print(f"[bold cyan]Starting {cycles} improvement batch(es)...[/bold cyan]\n")
    run_improvement_loop(cycles)
