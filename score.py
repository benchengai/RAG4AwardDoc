"""Score one benchmark run offline: `python score.py v1`

Reads runs/<version>.json (written by run.py), checks every answer with
simple rules and no API calls, prints one markdown table row for the README,
and writes runs/<version>_scored.json with an "auto" field per question.

These are heuristics, not a grader: a number anywhere in the answer counts as
correct, so the scores are an upper bound.
"""
import json, re, sys

version = sys.argv[1]
results = json.load(open(f"runs/{version}.json", encoding="utf-8"))
# Question types, in the order of the table columns.
TYPES = ["lookup", "combined", "calculation", "out_of_scope"]
# An out_of_scope answer counts as a correct refusal if it contains any of these.
REFUSE = ["not mention", "not provided", "not contain", "not specified", "not available",
          "cannot be determined", "cannot find", "unable to", "no information", "does not"]
# Clause numbers as the award writes them: schedule clauses like "B.1.1" or body
# clauses like "22.1". (?!\d) stops it matching dollar amounts such as "55.62".
CLAUSE = re.compile(r"\b(?:[A-H]\.\d{1,2}\.\d{1,2}|\d{1,2}\.\d(?!\d))")
# Any number, with an optional % sign after it.
NUM = re.compile(r"(\d+(?:\.\d+)?)\s*(%)?")


def numbers(text):
    """Return the set of (value, is_percent) pairs found in text.

    "$1,234.50" and "1234.5" both become (1234.5, False), so formatting
    differences don't matter, but 25 and 25% stay different.
    """
    text = text.replace(",", "").replace("$", "")
    return {(float(n), bool(p)) for n, p in NUM.findall(text)}


def target(q):
    """The expected answer as a (value, is_percent) pair, in the same form as numbers()."""
    e = q["expected"].replace(",", "").replace("$", "")
    return float(e.rstrip("%")), e.endswith("%")


def answer_ok(q):
    """True if the expected number appears in the answer, or, for out_of_scope, if it refuses."""
    if q["type"] == "out_of_scope":
        return any(p in q["answer"].lower() for p in REFUSE)
    return target(q) in numbers(q["answer"])


def citation_ok(q):
    """True if any clause cited in the answer is an expected clause. None (not scored) for out_of_scope."""
    if q["type"] == "out_of_scope":
        return None
    return bool(set(CLAUSE.findall(q["answer"])) & set(q["expected_clause"]))


def value_in_context(q):
    """Retrieval check: is the expected number in any retrieved chunk?

    Only scored for lookup and combined. A calculated shift total isn't printed
    in the award, and out_of_scope questions have no number to find.
    """
    if q["type"] in ("calculation", "out_of_scope"):
        return None
    return any(target(q) in numbers(c) for c in q["chunks"])


def clause_in_context(q):
    """Retrieval check: does any retrieved chunk's metadata name an expected clause?

    None when the chunks have no metadata (as in v1), so the column shows "–".
    """
    if q["type"] == "out_of_scope" or not any(q["metas"]):
        return None
    return any(m and m.get("clause") in q["expected_clause"] for m in q["metas"])


def frac(xs):
    """Format True/False results as "correct/scored", skipping None (not scored)."""
    xs = [x for x in xs if x is not None]
    return f"{sum(xs)}/{len(xs)}" if xs else "–"


# Run every check on every question and keep the results with the question.
for q in results:
    q["auto"] = {"answer": answer_ok(q), "citation": citation_ok(q),
                 "value_in_context": value_in_context(q), "clause_in_context": clause_in_context(q)}

# One table row: answer accuracy per question type, then the three checks
# across all questions.
row = [version]
row += [frac(q["auto"]["answer"] for q in results if q["type"] == t) for t in TYPES]
row += [frac(q["auto"][k] for q in results) for k in ("citation", "value_in_context", "clause_in_context")]
print("| version | lookup | combined | calculation | out_of_scope | citation | value in ctx | clause in ctx |")
print("|---|---|---|---|---|---|---|---|")
print("| " + " | ".join(row) + " |")

# Per-question results, so wrong answers can be looked at one by one.
with open(f"runs/{version}_scored.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
