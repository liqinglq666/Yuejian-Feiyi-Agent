"""Backward-compatible facade for the refactored retrieval service."""
from __future__ import annotations

from pathlib import Path

from core.models import RetrievalBundle
from services import retrieval as _retrieval

KnowledgeBaseError = _retrieval.KnowledgeBaseError
DEFAULT_DATA_DIR = _retrieval.DEFAULT_DATA_DIR
DATA_DIR = DEFAULT_DATA_DIR


def build_index(data_dir: Path | None = None):
    return _retrieval.build_index(data_dir or DATA_DIR)


def load_knowledge_base(data_dir: Path | None = None) -> str:
    return _retrieval.load_knowledge_base(data_dir or DATA_DIR)


def retrieve(
    query: str,
    *,
    top_k: int = 4,
    max_total_chars: int = 3200,
    data_dir: Path | None = None,
) -> RetrievalBundle:
    return _retrieval.retrieve(
        query,
        top_k=top_k,
        max_total_chars=max_total_chars,
        data_dir=data_dir or DATA_DIR,
    )


def retrieve_context(
    query: str,
    top_k: int = 4,
    max_total_chars: int = 3200,
    data_dir: Path | None = None,
) -> str:
    return _retrieval.retrieve_context(
        query,
        top_k=top_k,
        max_total_chars=max_total_chars,
        data_dir=data_dir or DATA_DIR,
    )


def clear_cache() -> None:
    _retrieval.clear_cache()
