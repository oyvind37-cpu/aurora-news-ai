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
    "nyheter": [
        "Skole evakuert etter brannalarm, ingen personer skadet.",
        "Ambulanse og politi rykket ut etter trafikkulykke.",
        "Politiet undersøker innbrudd, vold og lokale hendelser.",
        "A fire broke out in a school building and firefighters responded.",
        "Brannutrykning til skole, brannvesenet rykket ut etter brannalarm.",
        "Nyhet om brann, ulykke, politiutrykning, redningsaksjon eller trafikkhendelse.",
        "Politiet etterforsker vold, tyveri, kriminalsak eller en alvorlig hendelse.",
        "Breaking news about fires, accidents, emergency services and police incidents.",
        "Local news about a road collision, rescue operation, crime or public safety incident.",
    ],
    "politikk": [
        "Kommunestyret vedtar nytt skolebudsjett og endrer kommunale tjenester.",
        "The government proposes a new law on public education funding.",
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
MIN_SCORE = 0.30
MIN_MARGIN = 0.015

# High-precision guardrails for short, unambiguous emergency headlines.
# They are deliberately narrow; other stories still use semantic matching.
import re
EMERGENCY_HEADLINE = re.compile(
    r"\b(brannutrykning|brannalarm|brannvesenet rykket ut|politiutrykning|"
    r"trafikkulykke|redningsaksjon|firefighters respond|fire brigade called)\b", re.I
)
POLICY_HEADLINE = re.compile(
    r"\b(vedtak|forskrift|lovforslag|regjering|storting|kommunestyre|"
    r"policy|legislation|parliament|government)\b", re.I
)

# Specific editorial signals help distinguish a story's subject from a
# passing mention of a politician, company or platform.
EDITORIAL_RULES = [
    ("sport", re.compile(r"\b(LSK|FIFA|UEFA|formula 1|champions league|premier league|fotballkamp|football match|tennis tournament|olympic games|idrettsresultat)\b", re.I)),
    ("politikk", re.compile(r"\b(prime minister|president|government|parliament|storting|regjering|elections?|deportations?|statsbudsjett|kommunestyret)\b", re.I)),
    ("teknologi", re.compile(r"\b(OpenAI|ChatGPT|cybersecurity|spyware|malware|artificial intelligence|kunstig intelligens|databrudd)\b", re.I)),
    ("underholdning", re.compile(r"\b(band.s .*gig|concert tour|music awards|TV series|reality show|pop concert|film premiere)\b", re.I)),
]
# Do not treat every headline as political merely because a politician is
# mentioned. Event-first headlines take priority over broad political cues.
INCIDENT_RULE = re.compile(
    r"\b(brann|brannutrykning|brannalarm|trafikkulykke|råkjørte|innbrudd|"
    r"evakuert|police raid|drap|murder|killed|missing sailors|drone strike|"
    r"missile attack|bus stopped|bussen stoppet|firefighters|rescue operation)\b", re.I
)

def editorial_override(headline):
    if INCIDENT_RULE.search(headline) and not POLICY_HEADLINE.search(headline):
        return "nyheter"
    for topic, pattern in EDITORIAL_RULES:
        if pattern.search(headline):
            return topic
    return None

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
    guardrail_count = 0
    editorial_count = 0
    counts = {label: 0 for label in labels}
    for item, scores in zip(items, similarities):
        headline = str(item.get("title", ""))
        if EMERGENCY_HEADLINE.search(headline) and not POLICY_HEADLINE.search(headline):
            item["topic"] = "nyheter"
            item["topic_method"] = "headline-guardrail"
            counts["nyheter"] += 1
            guardrail_count += 1
            continue
        editorial = editorial_override(headline)
        if editorial:
            item["topic"] = editorial
            item["topic_method"] = "editorial-guardrail"
            counts[editorial] += 1
            editorial_count += 1
            continue
        # Best example per topic, rather than comparing against a long mixed
        # list of keywords. A clear margin is required to override fallback.
        ranked = sorted(
            ((label, max(float(scores[i]) for i, topic in enumerate(example_labels)
                         if topic == label)) for label in labels),
            key=lambda pair: pair[1], reverse=True,
        )
        winner, score = ranked[0]
        margin = score - ranked[1][1]
        # A generic story without convincing semantic evidence belongs in
        # general news rather than remaining invisible in topic filters.
        if score >= MIN_SCORE and margin >= MIN_MARGIN:
            item["topic"] = winner
            item["topic_method"] = "semantic-ai"
            assigned += 1
            counts[winner] += 1
        else:
            # Preserve an existing rule-based topic, if any.
            # Do not carry stale semantic classifications from earlier runs.
            item["topic"] = "nyheter"
            item["topic_method"] = "general-fallback"
            uncertain += 1

    data["ai_model"] = MODEL
    data["ai_classified_count"] = assigned
    data["ai_uncertain_count"] = uncertain
    data["ai_topic_counts"] = counts
    data["ai_guardrail_count"] = guardrail_count
    data["ai_editorial_count"] = editorial_count
    data["ai_method"] = "multilingual-example-similarity-v6"
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"KI klassifiserte {assigned} av {len(items)} saker; {uncertain} usikre.")
    print("Emnefordeling:", counts)

if __name__ == "__main__":
    main()
