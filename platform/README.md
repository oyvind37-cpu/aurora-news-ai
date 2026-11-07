# Aurora på Cloudflare

Status: utviklet og lokalt testet. **Ikke publisert eller godkjent i produksjon.**
Eksisterende GitHub Pages-app og nyhetsjobber er uendret.

## Komponenter

- Worker `aurora-news-platform`: app, API og tidsstyrt innhenting.
- D1 `aurora-news`: siste gode resultat per kilde, status og daglig KI-budsjett.
- Workers AI: én generering per norsk kalenderdag fra kl. 07, etter kildekontroll.
- Statiske flater: `/` (app) og `/status.html` (drift).
- `GET /api/news`, `GET /api/brief`, `GET /api/status` har ingen genereringsbivirkninger.
- Valgfritt eier-endepunkt: `POST /api/refresh` med bearer ADMIN_TOKEN og
  `{"source_id":"0"}`. Én kilde per forespørsel, minst ett minutt mellom forsøk.
  Ingen hemmeligheter legges i appen. Endepunktet er deaktivert uten secret.

15 RSS-strømmer kontrolleres én per minutt, slik at hver kilde normalt kontrolleres
hvert kvarter. Fordelingen begrenser CPU-arbeid per invokasjon på Workers Free.
Tidspunkter er beste innsats, ikke garanti for publisering nøyaktig 07.00.
Appens oppdateringsknapp leser siste publiserte data. Den lover ikke ny innhenting.

## Kontroll av innhold og feil

Kun artikler med gyldig dato innen 48 timer vises. KI får maksimalt 12 utdrag fra
siste 24 timer, fordelt på Oslo/Norge/Verden, maks to per utgiver og 350 tegn per
utdrag. Kilder som feiler eller er gamle utelates fra KI-grunnlaget. Kun faste
RSS-adresser hentes; ingen vilkårlig URL fra klienten. CNN hentes via Google News,
og mellomleddet er synlig. Utgivernes betalingsmurer omgås ikke.

Ved kildefeil beholdes forrige data og opprinnelig tidspunkt. Ved KI-feil beholdes
forrige brief med opprinnelig dato og tydelig varsel. Ugyldige kilde-ID-er eller
ugyldig JSON avvises. Dette verifiserer struktur og referanser, **ikke at hver
KI-påstand er faktuelt korrekt**. Norsk språk og faktisk kvalitet må vurderes ved
første ekte kjøring. Tomt/for gammelt kildegrunnlag utløser ikke KI-kall.

D1 reserverer én KI-attempt atomisk før modellkallet. Feil gir ikke automatiske
nye betalte forsøk samme dag. AI_ENABLED er false inntil kontoen er kontrollert.
Modellen er `@cf/meta/llama-3.1-8b-instruct-fp8`, maks 1000 ut-tokens.
Ingen betalt plan, kredittkjøp eller oppgradering inngår. Gratisgrensene gjelder
hele kontoen og må verifiseres; koden alene er ingen faktureringsgaranti på en
allerede betalt konto. Ingen KI-nøkkel trengs mellom Worker og AI-bindingen.

## Lokal kontroll

Node 24 kreves for testadapterens innebygde SQLite.

```sh
cd platform
npm ci
npm test
npm run check
npm run db:local
npm run dev
```

`AI_ENABLED=false` hindrer ekte KI-kall i utvikling. Lokal database er isolert fra
produksjon. Ikke bruk `wrangler dev --remote` for vanlige tester.

## Opprettelse etter Cloudflare-innlogging

1. Bekreft riktig konto og Workers Free. Ikke endre eksisterende refresh-Worker.
2. Opprett D1 med `npx wrangler d1 create aurora-news`.
3. Erstatt null-ID-en i wrangler.jsonc med returnert database-ID. Dette er ikke en
   hemmelighet. Sett eventuelt account_id for eksplisitt kontovalg.
4. Kjør `npm run db:remote`. Publiser med `npm run deploy` (KI fortsatt av).
5. Kontroller `/api/status`, at RSS-kildene blir oppdatert, CPU-tid/kvoter og
   tilgjengelighet for lokale kilder. Alle kilder bør ha et forsøk innen 15 min.
6. Aktiver AI_ENABLED=true på samme gratisplan og publiser. Verifiser én ekte
   kjøring etter kl. 07. Bekreft dato, lenker, norsk språk og kildegrunnlag.
7. Test mobilvisning og at oppdatering viser reelle data/tidsstempler.
8. Først etter godkjent ende-til-ende-test: koble den eksisterende GitHub Pages-
   appen til bekreftet Cloudflare-URL, slik at iPhone-ikonet fortsatt kan brukes.
   Alternativt installer den nye Cloudflare-appen. Ingen adresse gjettes i koden.
9. Stans gamle tidsstyrte GitHub-jobber først etter fungerende overgang.

## Tilbakerulling

Eksisterende app fortsetter under opprettelsen. Ved senere overgang kan den
forrige index.html gjenopprettes fra git. Deaktiver AI_ENABLED og cron på den nye
Worker ved driftsproblemer; behold D1 for historikk. Ikke slett eksisterende
Cloudflare-ressurser eller hemmeligheter som del av migreringen.

## Kjente gjenstående kontroller

- Cloudflare-innlogging og faktisk ressursopprettelse.
- Deploy, reelle RSS-kall, CPU-grense på Free og eventuell justering av parsing.
- Ekte modellkall, redaksjonell kvalitetsvurdering og mobilvisuell kontroll.
- Eksisterende app-overgang og opprydding i gamle jobber.
- Én AI-attempt per dag kan gi en dag uten ny brief ved modellfeil. Dette er en
  bevisst kostnadsgrense. Driftsstatus viser feilen, ikke et nytt genereringstidspunkt.
