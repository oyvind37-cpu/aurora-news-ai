import { XMLParser } from 'fast-xml-parser';
const parser = new XMLParser({ignoreAttributes:false,removeNSPrefix:true,parseTagValue:false,processEntities:true});
const arr = x => x == null ? [] : Array.isArray(x) ? x : [x];
const val = x => typeof x === 'object' ? x?.['#text'] || '' : String(x || '');
export const clean = (x, max=450) => val(x).replace(/<[^>]*>/g,' ').replace(/&nbsp;/g,' ').replace(/\s+/g,' ').trim().slice(0,max);
export function safeUrl(value) { try { const u=new URL(value); return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password ? u.href : null; } catch { return null; } }
export function oslo(now=Date.now()) {
 const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Oslo',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',hourCycle:'h23'}).formatToParts(new Date(now)).map(x=>[x.type,x.value]));
 return {day:`${parts.year}-${parts.month}-${parts.day}`,hour:Number(parts.hour)};
}
export function topic(title, fallback='nyheter') {
 const rules=[['okonomi',/økonomi|rente|inflasjon|aksje|børs|economy|inflation|interest rate/i],['naeringsliv',/næringsliv|bedrift|konkurs|selskap|business|company/i],['sport',/fotball|football|tennis|håndball|premier league/i],['politikk',/regjering|storting|statsminister|president|election|parlament/i],['teknologi',/kunstig intelligens|chatgpt|teknologi|technology|cyber/i],['kultur',/museum|arkeologi|utstilling|teater|kultur/i],['sosiale-medier',/tiktok|instagram|influens|sosiale medier/i]];
 return rules.find(([,re])=>re.test(title))?.[0]||fallback;
}
export function parseFeed(xml, feed, now=Date.now()) {
 if(/<!DOCTYPE|<!ENTITY/i.test(xml)) throw Error('XML-deklarasjon støttes ikke');
 const doc=parser.parse(xml); const entries=arr(doc.rss?.channel?.item ?? doc.feed?.entry);
 const items=entries.slice(0,35).flatMap(e=>{
  const title=clean(e.title,240);
  const link=arr(e.link).find(x=>typeof x==='string'||!x['@_rel']||x['@_rel']==='alternate');
  const url=safeUrl(typeof link==='object'?link?.['@_href']:link);
  if(!title||!url)return [];
  const stamp=Date.parse(val(e.pubDate||e.published||e.updated||e.date));
  // Unknown/future dates are excluded from the fresh news service.
  if(!Number.isFinite(stamp)||stamp>now+300000||stamp<now-48*3600000)return [];
  return [{title,url,source:feed.source,category:feed.category,topic:topic(title,feed.topic),summary:clean(e.description||e.summary),published:new Date(stamp).toISOString(),timestamp:stamp/1000,via:feed.via||null}];
 });
 if(!entries.length)throw Error('Ingen RSS/Atom-artikler');
 return items;
}
export function selectSources(items, now=Date.now()) {
 const fresh=items.filter(x=>Date.parse(x.published)>=now-24*3600000&&Date.parse(x.published)<=now&&x.summary);
 const chosen=[];
 for(const category of ['lokalt','norge','verden']){
  const counts=new Map();
  for(const item of fresh.filter(x=>x.category===category)){
   if((counts.get(item.source)||0)>=2)continue;
   chosen.push(item); counts.set(item.source,(counts.get(item.source)||0)+1);
   if(chosen.filter(x=>x.category===category).length===4)break;
  }
 }
 return chosen.map((x,i)=>({id:`S${i+1}`,title:x.title,source:x.source,url:x.url,published:x.published,category:x.category,excerpt:x.summary.slice(0,350)}));
}
export function validateBrief(result,sources) {
 const parsed=typeof result==='string'?JSON.parse(result.trim().replace(/^```(?:json)?\s*/,'').replace(/\s*```$/,'')):result;
 if(!Array.isArray(parsed?.sections)||!parsed.sections.length||parsed.sections.length>4)throw Error('Ugyldige seksjoner');
 const ids=new Set(sources.map(x=>x.id));
 return parsed.sections.map(s=>{
  if(typeof s.title!=='string'||!s.title.trim()||s.title.length>80||typeof s.summary!=='string'||!s.summary.trim()||s.summary.length>900||!Array.isArray(s.source_ids)||!s.source_ids.length||s.source_ids.some(id=>!ids.has(id)))throw Error('Ugyldig kildehenvisning eller tekst');
  return {title:s.title,summary:s.summary,source_ids:[...new Set(s.source_ids)]};
 });
}
