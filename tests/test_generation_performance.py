from app import GENERATION_RETRIEVAL_CHAR_BUDGET, GENERATION_RETRIEVAL_TOP_K


def test_web_generation_uses_compact_retrieval_context() -> None:
    assert GENERATION_RETRIEVAL_TOP_K == 3
    assert GENERATION_RETRIEVAL_CHAR_BUDGET == 2200
