from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
import chromadb
from openai import OpenAI

PDF = "retail.pdf"
EMBED_MODEL = "text-embedding-3-small"
PROMPT = ("Answer using only the context below. Cite the clause number.\n\n"
          "Context:\n{context}\n\nQuestion: {question}")

oa = OpenAI()
db = chromadb.PersistentClient(path="./db")
USAGE = {"in": 0, "out": 0}


def embed(texts):
    out = []
    for i in range(0, len(texts), 100):
        r = oa.embeddings.create(model=EMBED_MODEL, input=texts[i:i + 100])
        out += [d.embedding for d in r.data]
    return out


def build(name, chunks, metadatas=None):
    try:
        db.delete_collection(name)
    except Exception:
        pass
    col = db.create_collection(name)
    col.add(ids=[str(i) for i in range(len(chunks))],
            embeddings=embed(chunks), documents=chunks, metadatas=metadatas)
    print(f"{name}: {len(chunks)} chunks")


def retrieve_dense(col, question, k):
    r = col.query(query_embeddings=embed([question]), n_results=k)
    return r["documents"][0], r["metadatas"][0]


def generate(prompt, generator):
    r = oa.chat.completions.create(model=generator, temperature=0,
                                   messages=[{"role": "user", "content": prompt}])
    USAGE["in"] += r.usage.prompt_tokens
    USAGE["out"] += r.usage.completion_tokens
    return r.choices[0].message.content


def ask(question, collection, retrieval="dense", generator="gpt-4o-mini", k=3):
    col = db.get_collection(collection)
    if retrieval == "dense":
        docs, metas = retrieve_dense(col, question, k)
    else:
        from hybrid import retrieve_hybrid
        docs, metas = retrieve_hybrid(col, question, k, rerank=(retrieval == "hybrid_rerank"))
    context = "\n\n---\n\n".join(docs)
    answer = generate(PROMPT.format(context=context, question=question), generator)
    return answer, docs, metas