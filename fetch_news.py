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
    ('BBC World', 'verden', 'https://feeds.bbci.co.uk/news/world/rss.xml'),
]
TAG = re.compile(r'<[^>]+>')

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
    for entry in entries[:35]:
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
        result.append(dict(source=source, category=category, title=title, url=link, summary=summary, date_label=date_label, timestamp=stamp))
    return result

def main():
    items = []
    for source, category, url in FEEDS:
        try:
            fetched = fetch(source, category, url)
            print(f'{source}: {len(fetched)} saker')
            items.extend(fetched)
        except Exception as exc:
            print(f'{source}: utilgjengelig ({exc})')
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
    output = {'updated':dt.datetime.now(dt.timezone.utc).isoformat(), 'items':unique[:150]}
    (ROOT/'news.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Publisert {len(output["items"])} saker')

if __name__ == '__main__': main()
