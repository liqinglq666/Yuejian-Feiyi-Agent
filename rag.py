"""Backward-compatible exports for the refactored retrieval service."""
from services.retrieval import (  # noqa: F401
    KnowledgeBaseError,
    build_index,
    clear_cache,
    load_knowledge_base,
    retrieve,
    retrieve_context,
)
