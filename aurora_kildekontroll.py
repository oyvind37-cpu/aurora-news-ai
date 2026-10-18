"""Aurora Kildekontroll: conservative, source-attributed extractive brief.

No generative model is used. Never infer facts beyond the RSS source.
"""
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent

def build(data):
    now = dt.datetime.now(dt.timezone.utc)
    eligible = []
    for item in data.get("items", []):
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        source = str(item.get("source") or "").strip()
        summary = str(item.get("summary") or "").strip()
        try:
            stamp = float(item.get("timestamp", 0))
            published = dt.datetime.fromtimestamp(stamp, dt.timezone.utc)
        except (TypeError, ValueError, OverflowError, OSError):
            continue
        if not (title and source and urlparse(url).scheme in ("https", "http") and urlparse(url).netloc):
            continue
        if not (0 <= (now - published).total_seconds() <= 48 * 3600):
            continue
        eligible.append({
            "title": title,
            "source": source,
            "url": url,
            "published": published.isoformat(),
            "excerpt": summary,
            "evidence_type": "rss_excerpt" if summary else "headline_only",
            "verification": "source_attributed_not_independently_verified",
            "category": item.get("category", "annet")
        })
    # Prioritize freshness, but ensure Oslo and Norway get representation.
    groups = ("lokalt", "norge", "verden")
    selected = []
    for group in groups:
        selected.extend([x for x in eligible if x["category"] == group][:2])
    for item in eligible:
        if len(selected) >= 10:
            break
        if item not in selected:
            selected.append(item)
    return {
        "generated": now.isoformat(),
        "method": "extractive_rss_no_ai_generation",
        "notice": "Overskrifter og korte utdrag er hentet fra RSS. Ikke uavhengig faktaverifisert. Åpne originalkilden for full sammenheng.",
        "items": selected[:10]
    }

def main():
    data = json.loads((ROOT / "news.json").read_text(encoding="utf-8"))
    result = build(data)
    (ROOT / "brief.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Aurora Kildekontroll: {len(result['items'])} kildeattribuerte saker.")

if __name__ == "__main__":
    main()
