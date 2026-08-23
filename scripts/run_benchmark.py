from __future__ import annotations

import json
from pathlib import Path

from core.models import TaskRequest
from services.retrieval import KnowledgeBaseError, retrieve

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cases = json.loads((ROOT / "evaluation" / "benchmark.json").read_text(encoding="utf-8"))
    routing_passed = 0
    retrieval_passed = 0

    for case in cases:
        request = TaskRequest(scene=case["scene"], raw_request=case["query"])
        routing_ok = request.task_type.value == case["expected_task_type"]
        routing_passed += int(routing_ok)

        try:
            bundle = retrieve(request.retrieval_query)
            combined = " ".join(chunk.content for chunk in bundle.chunks)
            retrieval_ok = any(term in combined for term in case["expected_terms"])
        except KnowledgeBaseError:
            retrieval_ok = False
        retrieval_passed += int(retrieval_ok)

        print(
            f"{case['id']}: routing={'PASS' if routing_ok else 'FAIL'} "
            f"retrieval={'PASS' if retrieval_ok else 'FAIL'}"
        )

    total = len(cases)
    print(f"Routing: {routing_passed}/{total}")
    print(f"Retrieval: {retrieval_passed}/{total}")


if __name__ == "__main__":
    main()
