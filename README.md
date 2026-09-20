# rag4awarddoc

A small RAG system over an Australian modern award, plus a hand-annotated benchmark
that shows **where and why it fails**.

The interesting part is not the pipeline — it is the failure analysis. Naive
fixed-size chunking over a document whose substance lives in **pay rate tables**
breaks in specific, diagnosable ways.

---

## Results

10 questions about the General Retail Industry Award, each with a verified expected
value taken from the award's pay tables.

| Metric | Result |
|---|---:|
| Answer accuracy | **4 / 10** |
| Citation accuracy | **0 / 5** *(of those judged)* |

Every answer is annotated in [`results.json`](results.json) with the retrieved chunks,
a failure label and a note explaining what went wrong.

### Failure modes

| Label | Count | What it means |
|---|---:|---|
| `not_retrieved` | 4 | The table holding the answer never made the top-3. Queries matched *junior* rate tables instead of adult ones, because headers like "after 6.00 pm" appear in both. |
| `table_broken` | 1 | The right chunk was retrieved, but 500-char splitting had severed the column headers from the data rows — so the model read the weekly rate as the hourly rate. |
| `retrieved_not_used` | 1 | All the ingredients were present across chunks, but the model combined the wrong ones and then did the arithmetic itself. |

### What the numbers hide

- **Q5 answered correctly but cited the wrong clause.** The heading `22.1 Penalty rates`
  had been cut into the previous chunk, so the model cited `22.2` — the clause *after*
  the table. A right answer is not the same as a grounded one, which is why citations
  are scored separately.
- **Q8 refused to answer** rather than guess, and that is the desirable behaviour —
  contrast it with Q6, Q9 and Q10, which confidently returned wrong dollar figures
  drawn from the wrong table.
- **Q6 fabricated a citation**, quoting `55.62` as a clause number when it is a dollar
  amount lifted from the table body.
- Whether a table survives chunking is luck: in Q4 the column headers happened to land
  inside the chunk, in Q1 and Q5 they did not. The 500-char boundary decides.

---

## Where this points

The failures cluster by layer, which suggests different fixes:

| Layer | Failure | Direction |
|---|---|---|
| Chunking | `table_broken` | Table-aware splitting — keep headers with rows, treat a table as one unit |
| Retrieval | `not_retrieved` | Metadata filters (adult vs junior, casual vs full-time); the award labels its tables `B.1.1`, `B.2.1`, `B.3.1` |
| Generation | `retrieved_not_used` | Give the model a calculator tool instead of letting it multiply rates in prose |

---

## Setup

```bash
git clone https://github.com/benchengai/rag4awarddoc.git
cd rag4awarddoc
pip install -r requirements.txt
cp .env.example .env     # then edit .env and set OPENAI_API_KEY
```

**Get the source document.** The award PDF is not redistributed here. Download the
*General Retail Industry Award 2020* (MA000004) from the Fair Work Commission and
save it as `retail.pdf` in the project root:

<https://www.fwc.gov.au/agreements-awards/awards/modern-award-list>

---

## Usage

**Interactive** — builds the index on first run, then answers questions:

```bash
python run.py
```

```
> What is the casual loading percentage under this award?
> show          # print the chunks that were retrieved
> q             # quit
```

**Batch evaluation** — runs every question in `questions.json`, skips ones already
answered, and appends to `results.json`:

```bash
python batch.py
```

Grading is manual: open `results.json` and fill in `correct`, `citation_correct`,
`failure` and `note` for each entry. Those fields are what the tables above are
computed from.

---

## How it works

```
retail.pdf
    │  PyMuPDF text extraction
    ▼
500-character chunks          ← the source of most failures
    │  text-embedding-3-small
    ▼
ChromaDB (persistent, ./db)
    │  top-3 by vector similarity
    ▼
gpt-4o-mini  +  "answer using only the context, cite the clause number"
```

Deliberately minimal: no reranking, no query rewriting, no table parsing. The point
was to establish a baseline and find out what breaks first.

---

## Files

| File | Purpose |
|---|---|
| `run.py` | Index building + interactive Q&A loop |
| `batch.py` | Batch evaluation harness, resumable |
| `questions.json` | 10-question benchmark with expected values |
| `results.json` | Answers, retrieved chunks, failure labels, analysis notes |

---

## Note on the data

Pay rates in the benchmark reflect the award as published at the time of testing and
are used here only to check retrieval accuracy. **This is not legal or payroll
advice** — consult the Fair Work Commission for current rates.
