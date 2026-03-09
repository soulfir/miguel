import os
from pathlib import Path

AGENT_VERSION = "0.1.0"
MODEL_ID = "claude-opus-4-6"
MAX_TOOL_RETRIES = 3

# User files directory — set by Docker env var, or defaults to <project>/user_files
USER_FILES_DIR = os.environ.get(
    "USER_FILES_DIR",
    str(Path(__file__).parent.parent.parent / "user_files"),
)
