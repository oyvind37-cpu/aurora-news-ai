import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {parseFeed,oslo,validateBrief,selectSources} from '../src/core.js';
import worker,{claim,updateFeed,news,generate} from '../src/worker.js';
import {FEEDS} from '../src/feeds.js';
function database(){const db=new DatabaseSync(':memory:');db.exec(readFileSync(new URL('../migrations/0001_initial.sql',import.meta.url),'utf8'));return {prepare(sql){let args=[];const stmt=db.prepare(sql);return {bind(...values){args=values;return this;},async first(){return stmt.get(...args)||null;},async all(){return {results:stmt.all(...args)};},async run(){const r=stmt.run(...args);return {meta:{changes:Number(r.changes)}};}};},async batch(statements){db.exec('BEGIN');try{const result=[];for(const s of statements)result.push(await s.run());db.exec('COMMIT');return result;}catch(e){db.exec('ROLLBACK');throw e;}}};}
const now=Date.now();const rss=(title='Nyhet',date=new Date(now).toUTCString())=>`<rss><channel><item><title>${title}</title><link>https://example.org/news</link><pubDate>${date}</pubDate><description><![CDATA[<p>Et kildeutdrag om saken.</p>]]></description></item></channel></rss>`;
test('RSS and Atom parsing, timestamps, safe URLs and XML declarations',()=>{
 const items=parseFeed(rss(),FEEDS[0]);assert.equal(items.length,1);assert.equal(items[0].summary,'Et kildeutdrag om saken.');
 assert.equal(parseFeed(rss('Gammelt','Mon, 01 Jan 2024 10:00:00 GMT'),FEEDS[0]).length,0);
 assert.equal(parseFeed(rss().replace('https://example.org/news','javascript:alert(1)'),FEEDS[0]).length,0);
 assert.throws(()=>parseFeed('<!DOCTYPE rss>'+rss(),FEEDS[0]));
 const atom=`<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom</title><link href="https://example.org/a"/><published>${new Date(now).toISOString()}</published><summary>Tekst</summary></entry></feed>`;
 assert.equal(parseFeed(atom,FEEDS[0])[0].url,'https://example.org/a');
});
test('Norwegian clock handles summer/winter time',()=>{assert.equal(oslo(Date.parse('2026-07-01T05:00:00Z')).hour,7);assert.equal(oslo(Date.parse('2026-12-01T06:00:00Z')).hour,7);});
test('atomic lease blocks duplicate invocations and expires',async()=>{const env={DB:database()};const r=await Promise.all([claim(env,'one',100,1000),claim(env,'one',100,1000)]);assert.equal(r.filter(Boolean).length,1);assert.equal(await claim(env,'one',100,1100),true);});
test('source failure preserves last good data and truthful timestamps',async()=>{
 const env={DB:database()};await updateFeed(env,FEEDS[0],async()=>new Response(rss()));const first=await news(env);assert.equal(first.items.length,1);
 await env.DB.prepare('DELETE FROM leases').run();await updateFeed(env,FEEDS[0],async()=>new Response('',{status:503}));const second=await news(env);assert.equal(second.items.length,1);assert.equal(second.updated,first.updated);assert.match(second.sources[0].error,/503/);
});
test('brief validation rejects invented source IDs and empty prose',()=>{assert.throws(()=>validateBrief({sections:[{title:'Oslo',summary:'Hei',source_ids:['S999']}]},[{id:'S1'}]));assert.throws(()=>validateBrief({sections:[{title:'Oslo',summary:'',source_ids:['S1']}]},[{id:'S1'}]));});
test('AI budget permits one call a day including concurrent attempts; failed result cannot replace brief',async()=>{
 const env={DB:database(),AI_ENABLED:'true',AI:{run:async()=>{calls++;return {response:JSON.stringify({sections:[{title:'Oslo',summary:'Et sammendrag.',source_ids:['S1']}]})};}}};let calls=0;
 // Use today's noon in Oslo-independent UTC to exercise the real gate.
 const clock=Date.parse(new Date().toISOString().slice(0,10)+'T12:00:00Z');
 for(let i=0;i<3;i++){
  const items=[{title:`Sak ${i}`,url:`https://example.org/${i}`,source:FEEDS[i].source,category:'lokalt',summary:'Kildeutdrag.',published:new Date(clock-60000).toISOString(),timestamp:(clock-60000)/1000}];
  await env.DB.prepare('INSERT INTO feeds(id,payload,checked,succeeded) VALUES(?,?,?,?)').bind(String(i),JSON.stringify(items),new Date(clock).toISOString(),new Date(clock).toISOString()).run();
 }
 await Promise.all([generate(env,clock),generate(env,clock)]);assert.equal(calls,1);
 const saved=await env.DB.prepare("SELECT value FROM state WHERE key='brief'").first();assert.ok(saved);
 await env.DB.prepare("DELETE FROM state WHERE key LIKE 'ai-budget:%'").run();env.AI.run=async()=>{calls++;throw Error('provider outage');};await generate(env,clock);await generate(env,clock);assert.equal(calls,2);
 assert.equal((await env.DB.prepare("SELECT value FROM state WHERE key='brief'").first()).value,saved.value);
 assert.equal(JSON.parse((await env.DB.prepare("SELECT value FROM state WHERE key='ai-status'").first()).value).state,'failed');
});
test('public reads never run AI, refresh fails closed, CORS allowlist',async()=>{const env={DB:database(),ALLOWED_ORIGIN:'https://oyvind37-cpu.github.io',AI:{run(){throw Error('must not run');}}};assert.equal((await worker.fetch(new Request('https://app/api/refresh',{method:'POST',body:'{}'}),env)).status,401);const r=await worker.fetch(new Request('https://app/api/news',{headers:{Origin:'https://evil.example'}}),env);assert.equal(r.status,200);assert.equal(r.headers.get('Access-Control-Allow-Origin'),null);});
