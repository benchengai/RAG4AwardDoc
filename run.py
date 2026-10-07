
import json, os, sys
from rag import ask

CONFIGS = {
    "v1": dict(collection="retail_v1"),
    "v2": dict(collection="retail_v2"),
    "v3": dict(collection="retail_v3"),
    "v4": dict(collection="retail_v3", retrieval="hybrid"),
    "v5": dict(collection="retail_v3", retrieval="hybrid_rerank"),
}

version = sys.argv[1]
questions = json.load(open("questions.json", encoding="utf-8"))
os.makedirs("runs", exist_ok=True)

results = []
for q in questions:
    answer, docs, metas = ask(q["question"], **CONFIGS[version])
    results.append({**q, "answer": answer, "chunks": docs, "metas": metas})
    print(f"Q{q['id']:>2} {q['type']:<12} {answer[:90]!r}")

with open(f"runs/{version}.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)