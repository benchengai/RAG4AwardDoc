"""Run the 40-question benchmark against one version: `python run.py v1`

Sends every question in questions.json through rag.ask() with that version's
settings, and writes runs/<version>.json: each question's own fields plus the
answer, the retrieved chunks and their metadata. Scoring is a separate,
offline step (score.py), so a run can be re-scored without paying for new
API calls.
"""
import json, os, sys
from rag import ask

# Version name -> keyword arguments for rag.ask(). The build script decides
# what is inside a collection; this table decides which collection to search
# and how. v4 and v5 reuse v3's chunks, so only the retrieval changes.
CONFIGS = {
    "v1": dict(collection="retail_v1"),
    "v2": dict(collection="retail_v2"),
    "v3": dict(collection="retail_v3"),
    "v4": dict(collection="retail_v3", retrieval="hybrid"),
    "v5": dict(collection="retail_v3", retrieval="hybrid_rerank"),
}

version = sys.argv[1]  # e.g. "v1"
questions = json.load(open("questions.json", encoding="utf-8"))
os.makedirs("runs", exist_ok=True)

results = []
for q in questions:
    # ** unpacks the config into keyword arguments,
    # e.g. ask(question, collection="retail_v1").
    answer, docs, metas = ask(q["question"], **CONFIGS[version])
    # Keep the question's fields (id, type, expected, ...) and add what the
    # model saw and what it said.
    results.append({**q, "answer": answer, "chunks": docs, "metas": metas})
    # Progress line: question id, type and the first 90 characters of the answer.
    print(f"Q{q['id']:>2} {q['type']:<12} {answer[:90]!r}")

with open(f"runs/{version}.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
