from __future__ import annotations
import json
from pathlib import Path
from core.models import TaskRequest
from services.retrieval import KnowledgeBaseError, retrieve
ROOT=Path(__file__).resolve().parents[1]
def main():
    cases=json.loads((ROOT/"evaluation"/"benchmark.json").read_text(encoding="utf-8"))
    counts={"routing":0,"retrieval":0,"official":0}
    for item in cases:
        req=TaskRequest(scene=item["scene"],raw_request=item["query"],city=item.get("city","自动判断"))
        ok=req.task_type.value==item["expected_task_type"]
        counts["routing"]+=int(ok)
        try:
            chunks=retrieve(req.retrieval_query).chunks
            term=item["expected_terms"][0]
            rel=any(term in c.content for c in chunks)
            official=any(term in c.title+" "+c.content and c.source_url.startswith("https://www.ihchina.cn/") for c in chunks)
        except KnowledgeBaseError:
            rel=official=False
        counts["retrieval"]+=int(rel); counts["official"]+=int(official)
        print(item["id"],"PASS" if ok and rel and official else "FAIL",f"routing={ok} retrieval={rel} official={official}")
    print("Summary:",counts,"of",len(cases))
    if any(value!=len(cases) for value in counts.values()):
        raise SystemExit(1)
if __name__=="__main__":
    main()
