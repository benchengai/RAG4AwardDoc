import fitz, chromadb
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
from openai import OpenAI
client = OpenAI()
db = chromadb.PersistentClient(path="./db").get_or_create_collection("retail")
       # 重建空的
# 建库（只在第一次）
if db.count() == 0:
    text = "".join(p.get_text() for p in fitz.open("retail.pdf"))
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    vs = client.embeddings.create(model="text-embedding-3-small", input=chunks).data
    db.add(ids=[str(i) for i in range(len(chunks))],
           embeddings=[x.embedding for x in vs],
           documents=chunks)
    print(f"Indexed {len(chunks)} chunks.")

def ask(q):
    qv = client.embeddings.create(model="text-embedding-3-small", input=q).data[0].embedding
    hits = db.query(query_embeddings=[qv], n_results=3)["documents"][0]
    prompt = f"Answer using only the context below. Cite the clause number.\n\nContext:\n{hits}\n\nQuestion: {q}"
    r = client.chat.completions.create(model="gpt-4o-mini",
                                       messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content, hits

# 循环
print("Ask about the Retail Award. Type 'q' to quit, 'show' to see retrieved chunks.\n")
last_hits = []
while True:
    q = input("> ").strip()
    if q.lower() == "q":
        break
    if q.lower() == "show":
        for i, h in enumerate(last_hits, 1):
            print(f"\n--- chunk {i} ---\n{h[:400]}...")
        continue
    answer, last_hits = ask(q)
    print(f"\n{answer}\n")