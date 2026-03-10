"""Configuration for Miguel agent. Central place for all settings."""

import os
from pathlib import Path

AGENT_VERSION = "0.2.0"
MODEL_ID = "claude-opus-4-6"

# User files directory — set by Docker env var, or defaults to <project>/user_files
USER_FILES_DIR = os.environ.get(
    "USER_FILES_DIR",
    str(Path(__file__).parent.parent.parent / "user_files"),
)

# Context window limits per model (tokens)
MODEL_CONTEXT_LIMITS = {
    "claude-opus-4-6": 200_000,
    "claude-sonnet-4-20250514": 200_000,
    "claude-sonnet-4-6": 200_000,
    "claude-haiku-3-5-20241022": 200_000,
    "default": 200_000,
}