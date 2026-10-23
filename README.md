# rag4awarddoc

A small RAG system over an Australian modern award, plus a hand-built benchmark
that shows **where and why it fails**.

The interesting part is not the pipeline — it is the failure analysis. Naive
fixed-size chunking over a document whose substance lives in **pay rate tables**
breaks in specific, diagnosable ways.

**Scope:** the General Retail Industry Award 2020 (MA000004) only. Other awards are left
out on purpose — they would repeat the same table problems without needing a new
technique.

---

## Benchmark

40 questions about the General Retail Industry Award in [`questions.json`](questions.json).
Each one has an `expected` value and the `expected_clause` list that holds it.

| Type | Count | What it asks |
|---|---:|---|
| `lookup` | 12 | One value read straight from the award, e.g. a weekly rate or a penalty percentage |
| `combined` | 16 | An hourly rate that depends on several conditions at once — employment type, age, day or time, overtime |
| `calculation` | 8 | A total for a shift, so the right rate has to be found *and* multiplied by the hours |
| `out_of_scope` | 4 | Something the award doesn't answer (another award, a future rate, a Level 9). The right answer is to refuse |

Questions spell out every condition that changes the answer — adult or junior,
full-time, part-time or casual, shiftworker or not. Early versions left some of
these out, so a question could have two valid answers; [`NOTES.md`](NOTES.md)
records how that was found and fixed.

---

## Results on the 40 questions

Auto-scored with `score.py` from the answers in `runs/<version>.json`
([`runs/v1.json`](runs/v1.json) so far). The 40 questions are frozen, so every version
is scored on exactly the same set, and a row is added each time a version is run.

| version | lookup | combined | calculation | out_of_scope | citation | value in ctx | clause in ctx |
|---|---|---|---|---|---|---|---|
| v1 | 9/12 | 0/16 | 0/8 | 4/4 | 7/36 | 20/28 | – |

What the columns mean:

- **lookup / combined / calculation** — the expected number appears in the answer.
- **out_of_scope** — the answer contains a refusal phrase ("does not", "not provided", …).
- **citation** — a clause cited in the answer is in `expected_clause`. Not scored for `out_of_scope`.
- **value in ctx** — the expected number appears in at least one retrieved chunk. Only
  scored for `lookup` and `combined`, since a calculated total isn't printed in the award.
- **clause in ctx** — a retrieved chunk carries one of the expected clauses in its
  metadata. v1 chunks have no metadata, so this is blank until a version stores a
  `clause` field.

The scoring is a heuristic, not a grader: a number anywhere in the answer counts, and
refusals are spotted by keyword. It is lenient, so these numbers are a ceiling.

### Version log

One line per version: what changed, how the score moved, and why.

- **v1** — The baseline splits PyMuPDF text into fixed 500-character chunks and
  retrieves the top 3 by vector similarity. It gets 9/12 lookups but 0/16 combined
  questions, because the 500-character boundaries cut rate tables away from their
  column headers, so even when the right figure is retrieved the model reads the wrong
  row or column.

### What stands out in v1

- **`combined` scores 0/16 even though the expected number was in the retrieved
  chunks for 11 of them.** The table is often there, and the model reads the wrong row
  or column. (Rates repeat across tables, so a match in context doesn't prove the right
  row was retrieved — 11/16 is an upper bound too.)
- **Right answers are rarely grounded.** `lookup` gets 9/12 answers but only 4/12
  citations.
- **Refusing works.** All four out-of-scope questions were declined rather than guessed.

---

## Original 10-question run (manually graded)

The first version of the benchmark had 10 questions. They are now Q1–Q10, since
reworded to name age, employment type and shiftwork. Every answer was graded by hand
in [`results_v1_manual.json`](results_v1_manual.json), with the retrieved chunks, a
failure label and a note explaining what went wrong. The analysis below comes from
that run, and question numbers refer to it.

| Metric | Result |
|---|---:|
| Answer accuracy | **4 / 10** |
| Citation accuracy | **0 / 5** *(of those judged)* |

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

The failures in the 10-question run cluster by layer, which suggests different fixes:

| Layer | Failure | Direction |
|---|---|---|
| Chunking | `table_broken` | Table-aware splitting — keep headers with rows, treat a table as one unit |
| Retrieval | `not_retrieved` | Metadata filters (adult vs junior, casual vs full-time); the award labels its tables `B.1.1`, `B.2.1`, `B.3.1` |
| Generation | `retrieved_not_used` | Give the model a calculator tool instead of letting it multiply rates in prose |

### Planned versions

Only v1 has been run. `run.py` already has configs for v2–v5; the build scripts,
`hybrid.py` and the agent are not written yet, so there are no results for them.

| Version | Change | Aimed at |
|---|---|---|
| v1 | 500-character chunks, dense top-3 retrieval | Baseline |
| v2 | Extract the PDF with `pymupdf4llm`, so tables come out as Markdown | `table_broken` |
| v3 | One chunk per clause, prefixed with its clause number and title; table headers repeated when a table is split | `table_broken`, citations |
| v4 | Hybrid retrieval over the v3 chunks: BM25 keyword search plus dense vectors | `not_retrieved` |
| v5 | v4 plus a reranker | `not_retrieved` |
| v6 *(optional)* | Matilda as the generator | — |
| v7 | Agent with a pay calculator tool (`paycalc.py`), so the model looks rates up instead of doing arithmetic in prose | `retrieved_not_used`, `calculation` |

Also planned:

- **Asking before answering.** A separate set of 8 questions in `clarify.json` that leave
  out something the answer depends on, such as employment type, age or shiftwork. The
  right response is a question, not a dollar amount, scored as "contains a question mark
  and no dollar figure". The 40 frozen questions are re-run afterwards to check the
  agent doesn't start asking when it has everything it needs.
- **Deployment.** FastAPI and Docker on Azure Container Apps, with P50/P95 latency and
  cost per 1,000 queries.

---

## Setup

Tested with Python 3.9 on macOS.

```bash
git clone https://github.com/benchengai/RAG4AwardDoc.git
cd RAG4AwardDoc
python3 -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # then edit .env and set OPENAI_API_KEY
```

**Get the source document.** The award PDF is not redistributed here. Download the
*General Retail Industry Award 2020* (MA000004) from the Fair Work Commission and
save it as `retail.pdf` in the project root:

<https://www.fwc.gov.au/agreements-awards/awards/modern-award-list>

---

## Usage

Run everything from the project root. `build_v1.py`, `run.py` and `chat.py` call the
OpenAI API, which costs money; `score.py` is offline.

**1. Build the index** — splits `retail.pdf` into 500-character chunks, embeds them and
stores them as the `retail_v1` collection in `./db`:

```bash
python build_v1.py
```

**2. Run the benchmark** — sends all 40 questions through the pipeline and writes the
answers, retrieved chunks and metadata to `runs/<version>.json`:

```bash
python run.py v1
```

**3. Score it** — prints a markdown row like the table above and writes
`runs/<version>_scored.json`, which adds an `auto` field with the per-question checks:

```bash
python score.py v1
```

`runs/v1.json` is committed, so you can re-score v1 straight after cloning, with no
API key.

**Interactive** — `chat.py` is a question loop over the same 500-character chunking.
It builds its own `retail` collection on first run, separate from `retail_v1`:

```bash
python chat.py
```

```
> What is the casual loading percentage under this award?
> show          # print the chunks that were retrieved
> q             # quit
```

---

## How it works

```
retail.pdf
    │  PyMuPDF text extraction                         (build_v1.py)
    ▼
500-character chunks          ← the source of most failures
    │  text-embedding-3-small
    ▼
ChromaDB collection retail_v1 (persistent, ./db)
    │  top-3 by vector similarity                      (rag.ask)
    ▼
gpt-4o-mini, temperature 0  +  "answer using only the context, cite the clause number"
```

Deliberately minimal: no reranking, no query rewriting, no table parsing. The point
was to establish a baseline and find out what breaks first.

`rag.py` holds the shared pipeline — embedding, collection building, retrieval and
generation. Each version is a build script that creates a collection, plus an entry
in the `CONFIGS` dict in `run.py` that says which collection and retrieval to use.

---

## Files

| File | Purpose |
|---|---|
| `rag.py` | Shared pipeline: embed, build a collection, retrieve, generate, `ask` |
| `build_v1.py` | Builds the `retail_v1` collection from 500-character chunks |
| `run.py` | `python run.py <version>` runs every question through `rag.ask`, writes `runs/<version>.json` |
| `score.py` | Offline auto-scoring; prints a markdown table, writes `runs/<version>_scored.json` |
| `chat.py` | Interactive Q&A loop |
| `questions.json` | 40-question benchmark with expected values and clauses |
| `runs/v1.json` | v1 answers, retrieved chunks and metadata for all 40 questions |
| `results_v1_manual.json` | The original 10-question run, graded by hand with failure labels and notes |
| `payguides.docx` | Fair Work pay guide for the award, used to check the expected values |
| `NOTES.md` | Lessons from making the test set precise |

---

## Note on the data

Pay rates in the benchmark reflect the award as published at the time of testing and
are used here only to check retrieval accuracy. **This is not legal or payroll
advice** — consult the Fair Work Commission for current rates.
