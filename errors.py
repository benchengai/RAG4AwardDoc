"""Print the questions a run got wrong: `python errors.py v2 combined`

Reads runs/<version>_scored.json (written by score.py, so run that first). For
every wrong answer it shows the expected value, the model's answer, and where
in the retrieved chunks each value appears:
  expected  the right value. If it is in no chunk, retrieval failed.
  answered  a value the model gave instead. If it is in a chunk, the model
            read the wrong row or column of what it was given.
The optional second argument limits the output to one question type.
"""
import json, os, re, sys, textwrap

version = sys.argv[1]
qtype = sys.argv[2] if len(sys.argv) > 2 else None
path = f"runs/{version}_scored.json"
if not os.path.exists(path):
    sys.exit(f"{path} not found: run `python score.py {version}` first.")
results = json.load(open(path, encoding="utf-8"))
# Characters of chunk text to show on each side of a match.
WINDOW = 250
# Money and percentages in an answer, e.g. "$41.72", "1,097.80", "150%".
# Clause numbers like "22.1" have one decimal place, so they are skipped.
VALUE = re.compile(r"\d[\d,]*\.\d{2}|\d+(?:\.\d+)?%")


def spellings(value):
    """Ways a value can be written: 1097.80 can also appear as 1,097.80."""
    v = value.replace("$", "").replace(",", "")
    out = {v}
    if not v.endswith("%") and float(v) >= 1000:
        out.add(f"{float(v):,.2f}")
    return out


def find(value, chunks):
    """Return (chunk number, start, end) of the first place value appears, or None."""
    for n, chunk in enumerate(chunks, 1):
        for s in spellings(value):
            # Not part of a longer number: 42.68 shouldn't match 142.68 or 42.685.
            m = re.search(r"(?<![\d.])" + re.escape(s) + r"(?!\d)", chunk)
            if m:
                return n, m.start(), m.end()
    return None


def show(label, value, chunks):
    """Print where value appears in the chunks, with the text around it."""
    hit = find(value, chunks)
    if not hit:
        print(f"  {label} {value}: not in any retrieved chunk")
        return
    n, a, b = hit
    chunk = chunks[n - 1]
    snippet = chunk[max(0, a - WINDOW):a] + ">>>" + chunk[a:b] + "<<<" + chunk[b:b + WINDOW]
    print(f"  {label} {value}: in chunk {n}")
    print(textwrap.indent(snippet.strip(), "    | "))


def mark(x):
    return "–" if x is None else ("yes" if x else "no")


in_scope = [q for q in results if qtype is None or q["type"] == qtype]
wrong = [q for q in in_scope if not q["auto"]["answer"]]
print(f"{version}, {qtype or 'all types'}: {len(wrong)} wrong out of {len(in_scope)}\n")

for q in wrong:
    print("=" * 100)
    print(f"Q{q['id']} [{q['type']}] {q['question']}")
    print(f"  expected: {q['expected']}   clauses: {', '.join(q['expected_clause']) or '–'}   "
          f"citation ok: {mark(q['auto']['citation'])}   value in ctx: {mark(q['auto']['value_in_context'])}")
    print("  answer:")
    print(textwrap.indent(textwrap.fill(" ".join(q["answer"].split()), 96), "    "))
    if q["type"] == "out_of_scope":
        print()
        continue  # nothing to look up: the model should have refused
    # A calculated total isn't printed in the award, so there's nothing to find.
    if q["type"] != "calculation":
        show("expected", q["expected"], q["chunks"])
    expected = q["expected"].replace(",", "")
    for v in dict.fromkeys(VALUE.findall(q["answer"])):  # each value once, in order
        if v.replace(",", "") != expected:
            show("answered", v, q["chunks"])
    print()
