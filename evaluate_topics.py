"""Evaluate topic predictions against a manually reviewed gold set.

Missing benchmark cases are failures of test coverage, not correct predictions.
"""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
data = json.loads((root / "news.json").read_text(encoding="utf-8"))
gold = json.loads((root / "tests/topic_gold.json").read_text(encoding="utf-8"))["cases"]

by_title = {item["title"]: item for item in data["items"]}
matched = [(case, by_title[case["title"]]) for case in gold if case["title"] in by_title]
missing = [case for case in gold if case["title"] not in by_title]

if not gold:
    raise SystemExit("Benchmark has no labelled cases")

correct = sum(case["topic"] == item.get("topic") for case, item in matched)
classified = sum(bool(item.get("topic")) for _, item in matched)
total = len(gold)
evaluated = len(matched)
accuracy = correct / evaluated if evaluated else 0.0
match_coverage = evaluated / total
classification_coverage = classified / evaluated if evaluated else 0.0

print(
    f"Benchmark: {evaluated}/{total} matched ({match_coverage:.1%} dataset coverage); "
    f"accuracy {correct}/{evaluated} ({accuracy:.1%}); "
    f"classification coverage {classified}/{evaluated} ({classification_coverage:.1%})"
)
for case in missing:
    print(f"MISSING topic={case['topic']} | {case['title']}")
for case, item in matched:
    if case["topic"] != item.get("topic"):
        print(f"MISS expected={case['topic']} predicted={item.get('topic', 'unclassified')} | {case['title']}")

# A benchmark must never silently skip labelled cases and claim full success.
if missing:
    raise SystemExit(f"Benchmark incomplete: {len(missing)} of {total} gold cases absent from news.json")
if correct != evaluated:
    raise SystemExit(f"Benchmark classification errors: {evaluated - correct} of {evaluated}")
