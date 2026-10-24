"""Shared RAG pipeline: embed, store, retrieve, generate.

Every version of the experiment goes through this module:
  build_v*.py  calls build() to turn chunks into a Chroma collection
  run.py       calls ask() for each benchmark question
Between versions only the chunking (in the build script) and the retrieval
mode (in run.py's CONFIGS) change. The prompt and the generator stay fixed,
so score differences come from chunking and retrieval.
"""
from pathlib import Path
from dotenv import load_dotenv
# Load OPENAI_API_KEY from .env before the OpenAI client below is created.
load_dotenv(Path(__file__).parent / ".env")
import chromadb
from openai import OpenAI

PDF = "retail.pdf"
EMBED_MODEL = "text-embedding-3-small"
# The same instruction for every version. {context} is filled with the
# retrieved chunks, {question} with the benchmark question.
PROMPT = ("Answer using only the context below. Cite the clause number.\n\n"
          "Context:\n{context}\n\nQuestion: {question}")

# Created once at import time and shared by every function below.
oa = OpenAI()
# The vector store lives in ./db, relative to the current directory, so run the
# scripts from the project root.
db = chromadb.PersistentClient(path="./db")
# Running token count across all generate() calls, for estimating cost.
USAGE = {"in": 0, "out": 0}


def embed(texts):
    """Return one embedding vector per text, in the same order."""
    out = []
    # Send 100 texts per API request to keep each request small.
    for i in range(0, len(texts), 100):
        r = oa.embeddings.create(model=EMBED_MODEL, input=texts[i:i + 100])
        out += [d.embedding for d in r.data]
    return out


def build(name, chunks, metadatas=None):
    """(Re)create the collection `name` from a list of text chunks.

    An existing collection with that name is deleted first, so re-running a
    build script always starts clean. `metadatas` is an optional list of dicts,
    one per chunk, e.g. {"clause": "B.1.1"}; score.py's "clause in ctx" column
    reads the "clause" key.
    """
    try:
        db.delete_collection(name)
    except Exception:
        pass  # the collection didn't exist yet
    col = db.create_collection(name)
    # Chunk ids are just "0", "1", "2", ... in document order.
    col.add(ids=[str(i) for i in range(len(chunks))],
            embeddings=embed(chunks), documents=chunks, metadatas=metadatas)
    print(f"{name}: {len(chunks)} chunks")


def retrieve_dense(col, question, k):
    """Return the k chunks whose embeddings are closest to the question's, plus their metadata."""
    r = col.query(query_embeddings=embed([question]), n_results=k)
    # query() takes a list of queries and returns one result list per query.
    # We sent one, so take [0].
    return r["documents"][0], r["metadatas"][0]


def generate(prompt, generator):
    """Send the prompt to the chat model `generator` and return its reply."""
    # temperature=0 makes answers as repeatable as possible, so a rerun of the
    # same version gives (nearly) the same score.
    r = oa.chat.completions.create(model=generator, temperature=0,
                                   messages=[{"role": "user", "content": prompt}])
    USAGE["in"] += r.usage.prompt_tokens
    USAGE["out"] += r.usage.completion_tokens
    return r.choices[0].message.content


def ask(question, collection, retrieval="dense", generator="gpt-4o-mini", k=3):
    """Answer one question end to end: retrieve k chunks, then generate.

    collection  which Chroma collection to search, e.g. "retail_v1"
    retrieval   "dense" (vectors only), "hybrid" or "hybrid_rerank"
    generator   chat model name
    Returns (answer, chunks, metadatas), so run.py can save what the model saw
    next to what it said.
    """
    col = db.get_collection(collection)
    if retrieval == "dense":
        docs, metas = retrieve_dense(col, question, k)
    else:
        # hybrid.py is for v4/v5 and doesn't exist yet. Importing it only here,
        # when it's needed, lets the dense versions run without it.
        from hybrid import retrieve_hybrid
        docs, metas = retrieve_hybrid(col, question, k, rerank=(retrieval == "hybrid_rerank"))
    # A visible separator so the model can tell where one chunk ends.
    context = "\n\n---\n\n".join(docs)
    answer = generate(PROMPT.format(context=context, question=question), generator)
    return answer, docs, metas
