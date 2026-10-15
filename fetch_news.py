"""Free, conservative RSS aggregation. No paywall scraping or invented summaries."""
import datetime as dt
import email.utils
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Feeds are probed at runtime; inaccessible feeds are omitted, not fabricated.
FEEDS = [
    ('Avisa Oslo', 'lokalt', 'https://www.ao.no/service/rss'),
    ('Sagene Avis', 'lokalt', 'https://www.sageneavis.no/service/rss'),
    ('Nordre Aker Budstikke', 'lokalt', 'https://www.nab.no/service/rss'),
    ('NRK', 'norge', 'https://www.nrk.no/toppsaker.rss'),
    ('NRK Sport', 'norge', 'https://www.nrk.no/sport/toppsaker.rss'),
    ('BBC Technology', 'verden', 'https://feeds.bbci.co.uk/news/technology/rss.xml'),
    ('BBC Entertainment', 'verden', 'https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml'),
    ('BBC Politics', 'verden', 'https://feeds.bbci.co.uk/news/politics/rss.xml'),
    ('BBC Sport', 'verden', 'https://feeds.bbci.co.uk/sport/rss.xml'),
    ('The Guardian Culture', 'verden', 'https://www.theguardian.com/culture/rss'),
    ('The Guardian Technology', 'verden', 'https://www.theguardian.com/uk/technology/rss'),
    ('BBC World', 'verden', 'https://feeds.bbci.co.uk/news/world/rss.xml'),
    ('The Guardian', 'verden', 'https://www.theguardian.com/world/rss'),
    ('Deutsche Welle', 'verden', 'https://rss.dw.com/xml/rss-en-all'),
    ('Al Jazeera English', 'verden', 'https://www.aljazeera.com/xml/rss/all.xml'),
    # CNN's own RSS feeds are stale; Google News supplies CNN-only headlines.
    ('CNN', 'verden', 'https://news.google.com/rss/search?q=site%3Acnn.com%20when%3A1d&hl=en-US&gl=US&ceid=US%3Aen'),
]
FALLBACK_FEEDS = {
    'Deutsche Welle': 'https://news.google.com/rss/search?q=site%3Adw.com%2Fen%2F%20when%3A2d&hl=en-US&gl=US&ceid=US%3Aen',
}
TAG = re.compile(r'<[^>]+>')
TOPIC_SOURCES = {
    'NRK Sport': 'sport', 'BBC Sport': 'sport',
    'BBC Technology': 'teknologi', 'The Guardian Technology': 'teknologi',
    'BBC Entertainment': 'underholdning', 'BBC Politics': 'politikk',
    'The Guardian Culture': 'kultur',
}
TOPIC_RULES = [
    ('sosiale-medier', r'\\b(tiktok|instagram|facebook|snapchat|youtube|influencer|influensere|social media|sosiale medier|reddit|meta platforms)\\b'),
    ('teknologi', r'\\b(artificial intelligence|kunstig intelligens|chatgpt|openai|teknologi|technology|cyber|software|apple|microsoft|google|ai model|databrudd)\\b'),
    ('sport', r'\\b(fotball|football|soccer|premier league|champions league|olympic|olympiske|tennis|ski|håndball|handball|fifa|uefa|sport)\\b'),
    ('politikk', r'\\b(storting|regjering|statsminister|president|parlament|election|elections|valgkamp|politikk|political|congress|senate|minister)\\b'),
    ('kultur', r'\\b(kultur|culture|museum|kunst|art exhibition|utstilling|teater|theatre|litteratur|literature|arkeologi|archaeology|festival)\\b'),
    ('underholdning', r'\\b(underholdning|entertainment|celebrity|kjendis|tv-serie|netflix|hollywood|film premiere|music video|musikkvideo)\\b'),
]
def classify_topic(source, title, summary):
    text = (title + ' ' + summary).casefold()
    # Prefer a clear headline match to avoid labelling unrelated articles.
    for topic, pattern in TOPIC_RULES:
        if re.search(pattern, title.casefold(), re.I):
            return topic
    return TOPIC_SOURCES.get(source, 'annet')


def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(TAG.sub(' ', value or ''))).strip()[:350]

def fetch(source, category, url):
    request = urllib.request.Request(url, headers={'User-Agent':'AuroraNewsAI/0.2 (+personal RSS reader)', 'Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml'})
    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read(1_500_000)
    root = ET.fromstring(data)
    entries = root.findall('.//item')
    if not entries:
        entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
    result = []
    for entry in entries[:25]:
        def field(*names):
            for name in names:
                node = entry.find(name)
                if node is not None:
                    return node.attrib.get('href', '') if name.endswith('link') and node.attrib.get('href') else ''.join(node.itertext()).strip()
            return ''
        title = clean(field('title','{http://www.w3.org/2005/Atom}title'))
        link = field('link','{http://www.w3.org/2005/Atom}link')
        if not title or not link.startswith(('https://','http://')):
            continue
        raw_date = field('pubDate','{http://www.w3.org/2005/Atom}updated','{http://www.w3.org/2005/Atom}published')
        try:
            parsed = email.utils.parsedate_to_datetime(raw_date)
            stamp = parsed.timestamp()
            date_label = parsed.astimezone(dt.timezone.utc).strftime('%d.%m.%Y')
        except (TypeError, ValueError, OverflowError):
            stamp = 0
            date_label = 'Dato ukjent'
        summary = clean(field('description','{http://www.w3.org/2005/Atom}summary'))
        result.append(dict(source=source, category=category, topic=classify_topic(source,title,summary), title=title, url=link, summary=summary, date_label=date_label, timestamp=stamp))
    return result

def main():
    items = []
    for source, category, url in FEEDS:
        fetched = []
        try:
            fetched = fetch(source, category, url)
            print(f'{source}: {len(fetched)} saker fra hovedkilden')
        except Exception as exc:
            print(f'{source}: hovedkilden utilgjengelig ({exc})')
        if not fetched and source in FALLBACK_FEEDS:
            try:
                fetched = fetch(source, category, FALLBACK_FEEDS[source])
                print(f'{source}: {len(fetched)} saker fra reservekilden')
            except Exception as exc:
                print(f'{source}: reservekilden utilgjengelig ({exc})')
        items.extend(fetched)
    if not items:
        print('Ingen tilgjengelige kilder. Beholder eksisterende news.json.')
        return
    seen = set()
    unique = []
    for item in sorted(items, key=lambda x:x['timestamp'], reverse=True):
        key = re.sub(r'\W+', '', item['title'].casefold())
        if key in seen: continue
        seen.add(key)
        unique.append(item)
    output = {'updated':dt.datetime.now(dt.timezone.utc).isoformat(), 'items':unique[:240]}
    (ROOT/'news.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Publisert {len(output["items"])} saker')

if __name__ == '__main__': main()
