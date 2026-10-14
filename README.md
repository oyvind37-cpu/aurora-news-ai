# Aurora News AI v0.2

Mobiltilpasset nyhetsleser for iPhone med særskilt fokus på Avisa Oslo, Sagene Avis og Nordre Aker Budstikke. Et originalt mørkt nordlysdesign.

## Kom i gang
1. Opprett et **offentlig** GitHub-repository, for eksempel `aurora-news-ai`.
2. Last opp **innholdet** i denne mappen, inkludert `.github/workflows/news.yml` (behold mappestrukturen).
3. Gå til **Actions** → **Oppdater nyheter** → **Run workflow**. Sjekk loggen. Ikke alle kilder tilbyr tilgjengelig RSS.
4. Gå til **Settings → Pages**, velg **Deploy from a branch**, `main` og `/ (root)`.
5. Åpne `https://DITT-BRUKERNAVN.github.io/aurora-news-ai/` på iPhone i Safari, trykk Del → Legg til på Hjem-skjermen.

## Viktig
- RSS-adressene er kandidatadresser; de testes under kjøring. Kilder som avviser forespørselen blir ikke vist. Det betyr ikke at avisen mangler nyheter.
- Denne versjonen viser RSS-overskrifter og utdrag, **ikke KI-genererte oppsummeringer**. Ingen modellnøkkel trengs.
- Ingen artikler bak betalingsmur hentes. Kontroller utgivernes vilkår før offentlig distribusjon av sammendrag.
- GitHub Actions planlagte jobber kan bli forsinket; oppdatering er ikke sanntid.
- Neste versjon: valgfri KI-agent for sammendrag av lovlig tilgjengelige tekster, tydelig kildegrunnlag og kostnadstak.
