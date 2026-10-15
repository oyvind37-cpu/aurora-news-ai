"""Optional semantic topic classification. Run manually; no paid API required."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "news.json"
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOPICS = {
    "politikk": "Politikk, valg, regjering, storting, diplomati, political elections and government",
    "kultur": "Kultur, kunst, litteratur, museum, teater, archaeology, arts and cultural heritage",
    "sport": "Sport, fotball, ski, tennis, konkurranser, football and sporting events",
    "teknologi": "Teknologi, kunstig intelligens, data, forskning, cybersikkerhet, science and technology",
    "underholdning": "Underholdning, kjendiser, TV, film, musikk, celebrity and entertainment",
    "sosiale-medier": "Sosiale medier, TikTok, Instagram, YouTube, influencers and social media platforms",
}

def main():
    from sentence_transformers import SentenceTransformer, util
    data = json.loads(DATA.read_text(encoding="utf-8"))
    items = data.get("items", [])
    if not items:
        print("Ingen artikler å klassifisere")
        return
    model = SentenceTransformer(MODEL)
    labels = list(TOPICS)
    topic_vectors = model.encode(list(TOPICS.values()), convert_to_tensor=True, normalize_embeddings=True)
    texts = [(str(x.get("title", "")) + ". " + str(x.get("summary", ""))[:180]) for x in items]
    article_vectors = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True, batch_size=16)
    similarities = util.cos_sim(article_vectors, topic_vectors)
    assigned = 0
    for item, scores in zip(items, similarities):
        best = int(scores.argmax().item())
        confidence = float(scores[best].item())
        # Keep rule-based topic when semantic evidence is weak.
        if confidence >= 0.36:
            item["topic"] = labels[best]
            item["topic_method"] = "semantic-ai"
            assigned += 1
        else:
            item["topic_method"] = "rules"
    data["ai_model"] = MODEL
    data["ai_classified_count"] = assigned
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"KI klassifiserte {assigned} av {len(items)} saker")

if __name__ == "__main__":
    main()
