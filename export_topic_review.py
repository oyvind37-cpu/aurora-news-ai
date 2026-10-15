"""Create a reviewable, source-balanced CSV of the current news snapshot.

Predictions are deliberately not treated as ground truth. Human reviewers
fill gold_topic after reading the headline, summary and source article.
"""
import csv
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
data = json.loads((root / "news.json").read_text(encoding="utf-8"))
items = data.get("items", [])
out = root / "topic_review_180.csv"
fields = ["id", "source", "title", "summary", "url", "predicted_topic",
          "topic_method", "gold_topic", "review_notes"]
with out.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for i, item in enumerate(items, 1):
        writer.writerow({
            "id": i, "source": item.get("source", ""),
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "url": item.get("url", ""),
            "predicted_topic": item.get("topic", ""),
            "topic_method": item.get("topic_method", ""),
            "gold_topic": "", "review_notes": ""
        })
print(f"Exported {len(items)} stories to {out.name}.")
print("Methods:", dict(Counter(x.get("topic_method", "missing") for x in items)))
print("NOTE: gold_topic is empty until independently reviewed.")
