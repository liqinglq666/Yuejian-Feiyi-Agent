"""Backward-compatible prompt exports."""
from services.prompt_builder import (  # noqa: F401
    SYSTEM_PROMPT,
    TASK_INSTRUCTIONS,
    WEB_OUTPUT_RULES,
    build_initial_messages,
    build_revision_messages,
)
