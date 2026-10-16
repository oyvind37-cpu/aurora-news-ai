# Manuell oppdatering fra Aurora News AI

GitHub Pages er statisk og kan ikke starte en GitHub Actions-jobb alene. Denne Cloudflare Worker fungerer som en sikker mellomtjener.

## Oppsett (én gang)
1. Opprett en Cloudflare Worker (gratisnivå kan brukes innenfor gjeldende grenser) og lim inn innholdet i `worker.js`. Publiser den med en HTTPS-adresse.
2. Opprett et **fine-grained personal access token** i GitHub, avgrenset til **oyvind37-cpu/aurora-news-ai**, med repository permission **Actions: Read and write**. Oppbevar tokenet kun som Worker-secret `GITHUB_TOKEN`.
3. Opprett en lang tilfeldig privat kode som Worker-secret `AURORA_PIN`. Ikke legg koden i GitHub-repoet.
4. Sett Worker-variabelen `ALLOWED_ORIGIN` til `https://oyvind37-cpu.github.io` (eller den faktiske app-origin hvis annen).
5. Åpne Aurora News AI, velg «Koble til automatisk innhenting», legg inn Worker-adressen (med /refresh) og den private koden. Koden beholdes bare i nettleserfanens sesjon, ikke i repoet.
6. Trykk «Hent nye nyheter». Appen ber Worker starte `workflow_dispatch` og sjekker deretter publisert `news.json` i opptil to minutter.

Sikkerhet: En kodebasert Worker bør ikke brukes som en offentlig API-tjeneste. Beskytt koden og roter den ved mistanke om lekkasje. CORS er ikke autentisering; PIN kontrolleres på serveren. Vurder Cloudflare rate limiting for ytterligere beskyttelse. GitHub Actions kan bruke flere minutter, og en vellykket dispatch garanterer ikke at nye artikler er tilgjengelige. Automatisk cron-oppdatering fortsetter uavhengig av denne løsningen.
