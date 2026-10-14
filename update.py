import json, re, html, hashlib, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT=Path(__file__).parent
SOURCES=[('NRK','https://www.nrk.no/toppsaker.rss','Norge'),('VG','https://www.vg.no/rss/feed/forsiden/','Norge'),('BBC','https://feeds.bbci.co.uk/news/world/rss.xml','Verden')]

def clean(value):
    value=re.sub(r'<[^>]*>', ' ', html.unescape(value or ''))
    return re.sub(r'\s+',' ',value).strip()

def get(node,name):
    e=node.find(name)
    return (e.text or '').strip() if e is not None else ''

def date_parse(value):
    try:return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except Exception:return datetime.now(timezone.utc).isoformat()

def fetch(source,url,category):
    req=urllib.request.Request(url,headers={'User-Agent':'AuroraNewsAI/0.1 (personal RSS reader)'})
    with urllib.request.urlopen(req,timeout=18) as response: raw=response.read(2_000_000)
    root=ET.fromstring(raw)
    items=[]
    for node in root.findall('.//item')[:35]:
        title=clean(get(node,'title')); link=get(node,'link'); desc=clean(get(node,'description'))
        parsed=urllib.parse.urlparse(link)
        if not title or parsed.scheme not in ('http','https') or not parsed.netloc:continue
        items.append({'id':hashlib.sha256(link.encode()).hexdigest()[:16], 'title':title[:240], 'source':source,'category':category,'url':link,'published':date_parse(get(node,'pubDate')),'summary':desc[:320] if desc else 'Åpne originalartikkelen for å lese mer.','summary_type':'RSS-utdrag – ikke KI-generert'})
    return items

def main():
    items=[]; errors=[]
    for source,url,category in SOURCES:
        try:items+=fetch(source,url,category)
        except Exception as exc:errors.append(f'{source}: {type(exc).__name__}')
    # Keep last successful data when every feed fails.
    target=ROOT/'data'/'news.json'
    if not items and target.exists():
        print('No feeds available; retaining previous data',errors);return
    seen=set(); unique=[]
    for item in sorted(items,key=lambda x:x['published'],reverse=True):
        norm=re.sub(r'\W+','',item['title'].lower())
        if norm in seen:continue
        seen.add(norm);unique.append(item)
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({'updated':datetime.now(timezone.utc).isoformat(),'articles':unique[:90],'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Wrote {len(unique[:90])} articles; errors: {errors}')
if __name__=='__main__':main()
