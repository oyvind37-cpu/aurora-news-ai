# Aurora Intelligence Engine

Selvstendig KI-modul for Aurora Morgenbrief. Status: arkitektur/prototyp; ingen betalt API aktivert.

## Mål
- En grundig norsk Morgenbrief med publiseringsmål kl. 07:00 Europe/Oslo.
- Sporbare originalkilder, lenker og eksplisitt usikkerhet.
- Skille mellom dokumenterte fakta, sammenstilling og KI-tolkning.
- Behold eksisterende news.json, brief.json og nyhetsoppdatering uendret frem til testen er godkjent.

## Komponenter
1. Inntak: les news.json og eventuelt originale åpne artikler der lovlig og tilgjengelig.
2. Utvalg: grupper duplikater, prioriter Oslo/Norge/verden, økonomi, næringsliv, politikk, forskning og kultur.
3. Kildekontroll: bevar URL, publiseringstid, kildetittel; krev kilde for hver påstand. Merk RSS-utdrag som uverifisert.
4. Modelladapter: `cloudflare` (åpen modell) eller `openai` (valgfritt), valgt via konfigurasjon.
5. Kontroll: valider struktur, kildereferanser, dato og at ingen ukjente URL-er er funnet på.
6. Publisering: skriv egen `morgenbrief.json` atomisk ved godkjent resultat. Behold forrige utgave ved feil.

## Sikkerhet og kostnader
- Aldri API-nøkler i kildekode, nettleser eller offentlige JSON-filer. Bruk GitHub Actions secrets.
- Standardmodus: ingen betalt leverandør; ingen automatiske OpenAI-kall.
- OpenAI må aktiveres eksplisitt, med fast tokenbudsjett per kjøring og ekstern kostnadsgrense.
- Cloudflare Workers AI har gratis dagskvote, men kapasitet og modellkvalitet må testes.
- Ingen påstand om full faktaverifisering kun basert på språkmodell.
- Ingen betalingsmur omgås.

## Tidspunkt
- GitHub Actions cron bruker UTC og kan forsinkes. Planlegg kjøring med eksplisitt Europe/Oslo-håndtering (sommertid/vintertid).
- Merk faktisk publiseringstid; ikke lov nøyaktig 07:00 før drift er testet.

## Akseptansekriterier
- Samme kildegrunnlag kan kjøres mot minst to modeller for sammenligning.
- Alle faktapåstander støttes av synlige kildehenvisninger.
- Feil eller kvoteoverskridelse påvirker ikke den eksisterende nyhetsappen.
- Første publisering skjer først etter manuell gjennomgang av testbrief.
