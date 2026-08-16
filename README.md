# larsnagelalbertsen.dk

Hjemmeside for saxofonisten Lars Stan Albertsen. Statisk site
(HTML/CSS/JS, intet framework/build-step) hostet på Cloudflare Pages.
Se [`CLAUDE.md`](CLAUDE.md) for fuld projektkontekst og designbeslutninger.

## Struktur

```
index.html                  forside: Lars som hub, samlet koncertliste
stan-gets-in-your-eyes/     bandsiden: hero, Spotify, billedgalleri
historien/                  arkivbilleder + mindetekst (masonry-galleri)
nyheder/                    nyhedsopslag skrevet af Lars
style.css                    delt styling for hele sitet
script.js                    henter events.json (kun forsiden)
news.js                      henter news.json (kun nyhedssiden)
lightbox.js                  klik-for-at-forstørre galleribilleder
events.json                  koncertdata (fra scripts/sync_events.py)
news.json                    nyhedsdata (fra scripts/sync_news.py)
images/
  lars/                       billeder af Lars
  stgye/                      bandfotos (nutidige)
  historien/                  arkivbilleder, avisudklip, programmer
scripts/
  sync_events.py              Google Sheet -> events.json
  sync_news.py                Google Doc -> news.json
  requirements.txt
.github/workflows/sync-events.yml   kører begge sync-scripts on-demand
cloudflare-worker/                  "opdater nu"-trigger, se dens README
.env.sample                        skabelon til lokal konfiguration
```

## Kør sitet lokalt

```bash
python3 -m http.server 8000
```
Åbn <http://localhost:8000>.

## Opdatér koncertlisten (Google Sheets)

1. Google Sheet med kolonnerne (præcis disse navne i første række):
   `date | time | venue | city | title | project | link`
   - `date` som `YYYY-MM-DD`
   - `project` er valgfri (fx `STGYE`) — udelades for løsere/frilance-gigs
2. **Filer → Del → Publicer til web** → vælg arket → format **CSV** → Udgiv
3. `cp .env.sample .env`, indsæt URL'en i `GOOGLE_SHEET_CSV_URL`
4. Kør scriptet (se "Kør Python-scripts lokalt" nedenfor)

## Opdatér nyheder (Google Docs)

1. Google Doc, hvor hvert indlæg skrives som:
   - Titel formateret med Docs-stilen **"Overskrift 2"** — skriv gerne
     en dato først, fx `2026-09-01 — Ny koncert i støbeskeen`
   - Almindelig brødtekst nedenunder (fed/kursiv/links bevares)
   - Næste "Overskrift 2" starter automatisk et nyt indlæg
2. **Filer → Del → Publicer til web** → "Hele dokumentet" → Udgiv
   (standard webside-format, ikke CSV)
3. Indsæt URL'en i `GOOGLE_DOC_HTML_URL` i `.env`
4. Kør scriptet (se nedenfor)

## Kør Python-scripts lokalt

```bash
cd scripts
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 sync_events.py
python3 sync_news.py
```
Skriver/overskriver `events.json` og `news.json` i projektets rod.

## Automatisk opdatering (produktion)

Der er sat en **"opdater nu"-knap** op i selve Google Sheet'et/Doc'et,
som trigger begge sync-scripts uden at nogen skal røre kode. Se
[`cloudflare-worker/README.md`](cloudflare-worker/README.md) for hele
kæden (Sheet/Doc-link → Cloudflare Worker → GitHub Action → commit →
Cloudflare Pages deployer automatisk).

## Deploy

**Cloudflare Pages**, forbundet direkte til dette GitHub-repo. Push til
`main` (manuelt, eller automatisk via GitHub Action ovenfor) → Cloudflare
bygger og deployer automatisk, ingen build command nødvendig.
