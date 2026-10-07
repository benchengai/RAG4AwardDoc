import json, re, sys

version = sys.argv[1]
results = json.load(open(f"runs/{version}.json", encoding="utf-8"))
TYPES = ["lookup", "combined", "calculation", "out_of_scope"]
REFUSE = ["not mention", "not provided", "not contain", "not specified", "not available",
          "cannot be determined", "cannot find", "unable to", "no information", "does not"]
CLAUSE = re.compile(r"\b(?:[A-H]\.\d{1,2}\.\d{1,2}|\d{1,2}\.\d(?!\d))")
NUM = re.compile(r"(\d+(?:\.\d+)?)\s*(%)?")


def numbers(text):
    text = text.replace(",", "").replace("$", "")
    return {(float(n), bool(p)) for n, p in NUM.findall(text)}


def target(q):
    e = q["expected"].replace(",", "").replace("$", "")
    return float(e.rstrip("%")), e.endswith("%")


def answer_ok(q):
    if q["type"] == "out_of_scope":
        return any(p in q["answer"].lower() for p in REFUSE)
    return target(q) in numbers(q["answer"])


def citation_ok(q):
    if q["type"] == "out_of_scope":
        return None
    return bool(set(CLAUSE.findall(q["answer"])) & set(q["expected_clause"]))


def value_in_context(q):
    if q["type"] in ("calculation", "out_of_scope"):
        return None
    return any(target(q) in numbers(c) for c in q["chunks"])


def clause_in_context(q):
    if q["type"] == "out_of_scope" or not any(q["metas"]):
        return None
    return any(m and m.get("clause") in q["expected_clause"] for m in q["metas"])


def frac(xs):
    xs = [x for x in xs if x is not None]
    return f"{sum(xs)}/{len(xs)}" if xs else "–"


for q in results:
    q["auto"] = {"answer": answer_ok(q), "citation": citation_ok(q),
                 "value_in_context": value_in_context(q), "clause_in_context": clause_in_context(q)}

row = [version]
row += [frac(q["auto"]["answer"] for q in results if q["type"] == t) for t in TYPES]
row += [frac(q["auto"][k] for q in results) for k in ("citation", "value_in_context", "clause_in_context")]
print("| version | lookup | combined | calculation | out_of_scope | citation | value in ctx | clause in ctx |")
print("|---|---|---|---|---|---|---|---|")
print("| " + " | ".join(row) + " |")

with open(f"runs/{version}_scored.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)