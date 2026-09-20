import json, os, chromadb
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
from openai import OpenAI
client = OpenAI()

db = chromadb.PersistentClient(path="./db").get_or_create_collection("retail")
assert db.count() > 0, "库是空的，先跑原脚本建库"

def ask(q):
    qv = client.embeddings.create(model="text-embedding-3-small", input=q).data[0].embedding
    hits = db.query(query_embeddings=[qv], n_results=3)["documents"][0]
    prompt = f"Answer using only the context below. Cite the clause number.\n\nContext:\n{hits}\n\nQuestion: {q}"
    r = client.chat.completions.create(model="gpt-4o-mini",
                                       messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content, hits

# ---- 读题 ----
with open("questions.json", encoding="utf-8") as f:
    raw = json.load(f)
questions = [x if isinstance(x, dict) else {"question": x} for x in raw]
for n, q in enumerate(questions, 1):
    q.setdefault("id", n)

# ---- 读已有结果，跳过答过的 ----
results = []
if os.path.exists("results.json"):
    with open("results.json", encoding="utf-8") as f:
        results = json.load(f)
done = {r["question"] for r in results}
todo = [q for q in questions if q["question"] not in done]
print(f"{len(done)} already answered, {len(todo)} new.\n")

# ---- 只跑新的 ----
for q in todo:
    answer, hits = ask(q["question"])
    print(f"{'='*70}\nQ{q['id']}: {q['question']}")
    if q.get("expected"):
        print(f"EXPECTED: {q['expected']}")
    print(f"ANSWER:   {answer}")
    for i, h in enumerate(hits, 1):
        print(f"\n--- chunk {i} ---\n{h[:400]}")
    print()
    results.append({**q, "answer": answer, "chunks": hits,
                    "correct": None, "citation_correct": None, "failure": None, "note": ""})

results.sort(key=lambda r: r["id"])
with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"Done. results.json now has {len(results)} questions.")