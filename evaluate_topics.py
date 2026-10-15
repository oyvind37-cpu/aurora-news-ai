"""Measure topic accuracy and coverage on manually labelled headlines."""
import json
from pathlib import Path
root=Path(__file__).resolve().parent
data=json.loads((root/"news.json").read_text(encoding="utf-8"))
gold=json.loads((root/"tests/topic_gold.json").read_text(encoding="utf-8"))["cases"]
by_title={x["title"]:x for x in data["items"]}
matched=[(g,by_title[g["title"]]) for g in gold if g["title"] in by_title]
if not matched:
    raise SystemExit("No benchmark headlines in news.json")
correct=sum(g["topic"]==x.get("topic") for g,x in matched)
covered=sum(bool(x.get("topic")) for _,x in matched)
print(f"Benchmark: {len(matched)}/{len(gold)} matched; accuracy {correct}/{len(matched)} ({correct/len(matched):.1%}); coverage {covered}/{len(matched)} ({covered/len(matched):.1%})")
for g,x in matched:
    if g["topic"]!=x.get("topic"):
        print(f"MISS expected={g['topic']} predicted={x.get('topic','unclassified')} | {g['title']}")
