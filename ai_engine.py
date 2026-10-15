"""Optional multilingual semantic topic classifier. No paid AI API.

Run manually via GitHub Actions. This is experimental, not a fact checker.
Topic examples describe editorial subject matter rather than isolated keywords.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "news.json"
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Separate prototype sentences help a short-text embedding model recognize
# different kinds of stories within each editorial section.
TOPICS = {
    "politikk": [
        "Nyhet om politiske vedtak, regjering, Stortinget, kommunestyret og offentlig politikk.",
        "Reportasje om valg, partier, politiske konflikter, lovforslag og statsbudsjett.",
        "News about elections, government decisions, parliament, laws and public policy.",
        "Political negotiations, diplomacy, international relations and legislation.",
    ],
    "kultur": [
        "Nyhet om kunstutstilling, museum, teater, litteratur, bibliotek og kulturarv.",
        "Reportasje om arkeologiske funn, historiske kulturminner og kulturinstitusjoner.",
        "News about museums, archaeology, books, theatre, fine art and cultural heritage.",
        "Literary awards, art exhibitions, historical discoveries and cultural institutions.",
    ],
    "sport": [
        "Nyhet om fotballkamp, serieresultat, spiller, trener og idrettskonkurranse.",
        "Reportasje om ski, friidrett, håndball, tennis, sykkelritt og idrettsmesterskap.",
        "Sports news about match results, athletes, football clubs and championships.",
        "Tennis tournaments, skiing, Olympic events, league standings and sports transfers.",
    ],
    "teknologi": [
        "Nyhet om kunstig intelligens, programvare, datamaskiner og digital sikkerhet.",
        "Reportasje om teknologiselskaper, mobiltelefoner, forskning og cybersikkerhet.",
        "Technology news about artificial intelligence, software, cybersecurity and computing.",
        "New scientific technology, AI models, digital products and security vulnerabilities.",
    ],
    "underholdning": [
        "Nyhet om TV-program, film, strømmetjenester, kjendiser og populærmusikk.",
        "Reportasje om konsertturneer, reality-TV, filmpriser og underholdningsbransjen.",
        "Entertainment news about celebrities, movies, television shows and popular music.",
        "Streaming series, celebrity interviews, pop concerts and entertainment awards.",
    ],
    "sosiale-medier": [
        "Nyhet om TikTok, Instagram, Snapchat, YouTube og sosiale medieplattformer.",
        "Reportasje om influensere, virale trender, innholdsmoderering og sosiale medier.",
        "News about social media platforms, influencers, viral content and online creators.",
        "Social media algorithms, platform regulation, online communities and creator economy.",
    ],
}

# Similarity scores are not probabilities. These are provisional thresholds
# and must be evaluated against manually labelled examples.
MIN_SCORE = 0.32
MIN_MARGIN = 0.025

def main():
    from sentence_transformers import SentenceTransformer, util
    data = json.loads(DATA.read_text(encoding="utf-8"))
    items = data.get("items", [])
    if not items:
        print("Ingen artikler å klassifisere")
        return

    model = SentenceTransformer(MODEL)
    labels = list(TOPICS)
    examples = [example for label in labels for example in TOPICS[label]]
    example_labels = [label for label in labels for _ in TOPICS[label]]
    example_vectors = model.encode(
        examples, convert_to_tensor=True, normalize_embeddings=True
    )
    texts = [
        (str(item.get("title", "")) + ". " + str(item.get("summary", ""))[:220])
        for item in items
    ]
    article_vectors = model.encode(
        texts, convert_to_tensor=True, normalize_embeddings=True, batch_size=16
    )
    similarities = util.cos_sim(article_vectors, example_vectors)

    assigned = 0
    uncertain = 0
    counts = {label: 0 for label in labels}
    for item, scores in zip(items, similarities):
        # Best example per topic, rather than comparing against a long mixed
        # list of keywords. A clear margin is required to override fallback.
        ranked = sorted(
            ((label, max(float(scores[i]) for i, topic in enumerate(example_labels)
                         if topic == label)) for label in labels),
            key=lambda pair: pair[1], reverse=True,
        )
        winner, score = ranked[0]
        margin = score - ranked[1][1]
        if score >= MIN_SCORE and margin >= MIN_MARGIN:
            item["topic"] = winner
            item["topic_method"] = "semantic-ai"
            assigned += 1
            counts[winner] += 1
        else:
            # Preserve an existing rule-based topic, if any.
            item["topic_method"] = "rules" if item.get("topic") else "unclassified"
            uncertain += 1

    data["ai_model"] = MODEL
    data["ai_classified_count"] = assigned
    data["ai_uncertain_count"] = uncertain
    data["ai_topic_counts"] = counts
    data["ai_method"] = "multilingual-example-similarity-v2"
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"KI klassifiserte {assigned} av {len(items)} saker; {uncertain} usikre.")
    print("Emnefordeling:", counts)

if __name__ == "__main__":
    main()
