"""Miguel agent factory. This file is the heart of what Miguel modifies."""

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from pathlib import Path

from agno.db.sqlite import SqliteDb
from agno.tools.local_file_system import LocalFileSystemTools

from miguel.agent.config import MODEL_ID, USER_FILES_DIR
from miguel.agent.prompts import get_system_prompt
from miguel.agent.tools.capability_tools import (
    get_capabilities,
    get_next_capability,
    check_capability,
    add_capability,
)
from miguel.agent.tools.self_tools import (
    read_own_file,
    list_own_files,
    get_architecture,
    log_improvement,
)
from miguel.agent.tools.prompt_tools import (
    get_prompt_sections,
    modify_prompt_section,
)
from miguel.agent.tools.tool_creator import (
    create_tool,
    add_functions_to_tool,
)
from miguel.agent.tools.recovery_tools import (
    recover_backup,
    list_recovery_points,
    validate_agent_file,
    health_check,
)
from miguel.agent.tools.dep_tools import (
    add_dependency,
    list_dependencies,
)


def create_agent(interactive: bool = False) -> Agent:
    """Create and return a configured Miguel agent instance.

    Args:
        interactive: If True, enable conversation history for chat sessions.
                     If False (default), no history — used for improvement batches.
    """
    return Agent(
        name="Miguel",
        model=Claude(
            id=MODEL_ID,
            retries=5,
            delay_between_retries=60,
            exponential_backoff=True,
        ),
        instructions=get_system_prompt(),
        tools=[
            PythonTools(base_dir=Path(__file__).parent),
            ShellTools(base_dir=Path(__file__).parent),
            LocalFileSystemTools(target_directory=str(Path(__file__).parent)),
            LocalFileSystemTools(target_directory=USER_FILES_DIR),
            get_capabilities,
            get_next_capability,
            check_capability,
            add_capability,
            read_own_file,
            list_own_files,
            get_architecture,
            log_improvement,
            get_prompt_sections,
            modify_prompt_section,
            create_tool,
            add_functions_to_tool,
            recover_backup,
            list_recovery_points,
            validate_agent_file,
            health_check,
            add_dependency,
            list_dependencies,
        ],
        markdown=True,
        **(
            {
                "db": SqliteDb(db_file=str(Path(__file__).parent / "miguel.db")),
                "add_history_to_context": True,
                "num_history_runs": 20,
            }
            if interactive
            else {}
        ),
    )