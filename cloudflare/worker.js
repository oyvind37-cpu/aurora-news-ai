// Cloudflare Worker: secure manual trigger for Aurora News AI.
// Secrets: GITHUB_TOKEN (fine-grained Actions: write), REFRESH_SECRET (long random passphrase).
// AURORA_PIN is accepted for older configurations.
// Set ALLOWED_ORIGIN to the exact GitHub Pages origin, e.g. https://oyvind37-cpu.github.io
const OWNER = 'oyvind37-cpu';
const REPO = 'aurora-news-ai';
const WORKFLOW = 'news.yml';
export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const allowed = env.ALLOWED_ORIGIN || 'https://oyvind37-cpu.github.io';
    const cors = { 'Access-Control-Allow-Origin': allowed, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, X-Aurora-Pin', 'Vary': 'Origin', 'Cache-Control': 'no-store' };
    const reply = (body, status) => new Response(JSON.stringify(body), { status, headers: {...cors,'Content-Type':'application/json; charset=utf-8'} });
    const secret = env.REFRESH_SECRET || env.AURORA_PIN;
    if (new URL(request.url).pathname === '/health' && request.method === 'GET') {
      return reply({service:'aurora-news-refresh',configured:Boolean(env.GITHUB_TOKEN && secret)},200);
    }
    if (origin !== allowed) return new Response('Forbidden', {status:403});
    if (request.method === 'OPTIONS') return new Response(null, {status:204,headers:cors});
    if (request.method !== 'POST' || new URL(request.url).pathname !== '/refresh') return reply({error:'Not found'},404);
    if (!env.GITHUB_TOKEN || !secret) return reply({error:'Server not configured'},503);
    const pin = request.headers.get('X-Aurora-Pin') || '';
    // Fixed-length timing-safe comparison using Web Crypto.
    const digest = async s => new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)));
    const a = await digest(pin), b = await digest(secret);
    let mismatch = 0;
    for (let i=0;i<a.length;i++) mismatch |= a[i]^b[i];
    if (!pin || mismatch) return reply({error:'Ugyldig kode'},401);
    const response = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,{
      method:'POST',
      headers:{'Authorization':`Bearer ${env.GITHUB_TOKEN}`,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'Aurora-News-Worker'},
      body:JSON.stringify({ref:'main'})
    });
    if (response.status === 204) return reply({ok:true,message:'Innhenting startet'},202);
    return reply({error:'GitHub kunne ikke starte innhentingen',status:response.status},502);
  }
};
