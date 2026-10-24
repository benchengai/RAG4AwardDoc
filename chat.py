"""Interactive Q&A over the award: `python chat.py`

The original standalone script, from before the pipeline was split into rag.py.
It does its own chunking and keeps its own "retail" collection, separate from
the benchmark's "retail_v1", so trying things here never touches benchmark runs.
Type a question, "show" to see the chunks behind the last answer, or "q" to quit.
"""
import fitz, chromadb
from pathlib import Path
from dotenv import load_dotenv
# Load OPENAI_API_KEY from .env before the OpenAI client is created.
load_dotenv(Path(__file__).parent / ".env")
from openai import OpenAI
client = OpenAI()
db = chromadb.PersistentClient(path="./db").get_or_create_collection("retail")

# Build the index only on the first run, while the collection is still empty.
if db.count() == 0:
    text = "".join(p.get_text() for p in fitz.open("retail.pdf"))
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    # All chunks in a single embeddings request (rag.embed() sends them in batches instead).
    vs = client.embeddings.create(model="text-embedding-3-small", input=chunks).data
    db.add(ids=[str(i) for i in range(len(chunks))],
           embeddings=[x.embedding for x in vs],
           documents=chunks)
    print(f"Indexed {len(chunks)} chunks.")

def ask(q):
    """Embed the question, fetch the 3 closest chunks and ask the model. Returns (answer, chunks)."""
    qv = client.embeddings.create(model="text-embedding-3-small", input=q).data[0].embedding
    hits = db.query(query_embeddings=[qv], n_results=3)["documents"][0]
    # {hits} is a Python list, so the context arrives as "['chunk 1', 'chunk 2', ...]"
    # rather than the "---"-separated text that rag.py sends.
    prompt = f"Answer using only the context below. Cite the clause number.\n\nContext:\n{hits}\n\nQuestion: {q}"
    # No temperature=0 here (unlike rag.py), so the same question can get different answers.
    r = client.chat.completions.create(model="gpt-4o-mini",
                                       messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content, hits

# Question loop
print("Ask about the Retail Award. Type 'q' to quit, 'show' to see retrieved chunks.\n")
last_hits = []  # chunks behind the last answer, for "show"
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
