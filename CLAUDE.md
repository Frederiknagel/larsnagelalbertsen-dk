# larsnagelalbertsen.dk

Hjemmeside for saxofonisten **Lars Nagel Albertsen**. Bygget af hans søn
Frederik. Domænet er hans navn — sitet skal handle om *ham*, ikke kun
om ét projekt.

## Sitestruktur (besluttet)

Lars' primære, faste projekt er bandet **Stan Gets In Your Eyes**
("STGYE") — Danmarks ældste Bossa Nova-orkester, debut ved Copenhagen
Jazzfestival 1986. Men han spiller også med andre bands/i andre
sammenhænge, uden at det nødvendigvis er navngivne, faste projekter.

**To sider, tydeligt forskellige formål:**

### `/` — forsiden (Lars som hub)
Skal være **lige så simpelt og redaktionelt som albertewinding.dk**
— ikke bare samme farve/font som vi lavede tidligere, men samme
**layout**:
- Topnavigation: **"LARS NAGEL ALBERTSEN"** (bold versaler, wordmark
  i toppen) — med en **fane ved siden af** der linker videre til
  **"STAN GETS IN YOUR EYES"** (undersiden)
- To-kolonne sektion: portræt af Lars til venstre, kort bio-tekst til
  højre (præcis som Albertes side)
- **Koncerter**-sektion nedenunder — én samlet liste, ALLE Lars'
  gigs (STGYE + løsere/frilance-optrædener), ikke kun STGYE
- Ingen Spotify-embed, intet billedgalleri her — det hører til på
  STGYE-siden

### `/stan-gets-in-your-eyes` — bandsiden
Beholder den rigere stil, vi allerede har bygget i prototypen:
- Hero-sektion, infotekst om bandet
- Billedgalleri
- Spotify-embed
- **Ingen egen koncertliste** — koncerter vises kun samlet på
  forsiden, denne side handler om musik/historie/billeder

Det meste af den eksisterende `stan-gets-in-your-eyes`-prototype
(Spotify-embed, galleri, monokrome tema fra albertewinding.dk) kan
genbruges næsten 1:1 som denne underside.

## Tech stack

Ren statisk side — **ingen build-step, intet framework**:
- `index.html` / `style.css` / `script.js`
- Skrifttype: **Inter** (Google Fonts, vægt 400–900)
- Ingen JS-afhængigheder udover et lille fetch-kald til `events.json`

## Design-konventioner

- **Farvetema**: monokromt, inspireret af albertewinding.dk — hvid
  baggrund, næsten-sort (`--ink`) til overskrifter/knapper, varm
  mørkegrå til sektionsoverskrifter, grå til brødtekst. Ingen
  farveaccenter (guld/bronze er bevidst fravalgt tidligere).
- **Layout**: fladt, skarpe hjørner (ingen runding på fotos/kort),
  sektioner adskilt af tynde linjer — ikke kort/skygger.
- Alle sti-referencer i HTML/CSS/JS skal være **relative** (ikke
  `/images/...`), så sitet kan flyttes mellem paths/domæner uden at
  gå i stykker. Ekstra vigtigt nu: STGYE-siden flytter til
  `/stan-gets-in-your-eyes/`, så dens egne asset-stier skal virke
  derfra, ikke kun fra roden.

## Koncertdata (`events.json`)

Tænkt til at blive opdateret automatisk fra et Google Sheet, så Lars
selv kan tilføje koncerter uden at røre kode:

- `scripts/sync_events.py` henter et **publiceret** Google Sheet (som
  CSV) og skriver `events.json`
- Kræver `GOOGLE_SHEET_CSV_URL` lokalt i `.env` (se `.env.sample`) —
  eller som GitHub repo-secret, når det køres via Action (se nedenfor)
- Encoding: `response.encoding = "utf-8"` er sat eksplicit i
  `fetch_sheet_csv()` — uden det bliver æøå til mojibake, fordi
  Googles CSV-endpoint ikke altid sender `charset=utf-8` i sin header
- **Status: sat op og virker** med et rigtigt Google Sheet, delt med
  Lars som redigerings-adgang
- **Automatisk opdatering**: `.github/workflows/sync-events.yml`
  (trigges via `workflow_dispatch`, ikke en tidsplan) + en Cloudflare
  Worker (`cloudflare-worker/trigger-sync.js`) som fungerer som et
  "opdater nu"-link i selve Google Sheet'et — se
  `cloudflare-worker/README.md` for fuld opsætning
- **Nyt felt**: et valgfrit `project`-felt per event (fx
  `"project": "STGYE"`), så et event kan mærkes med hvilket
  band/projekt det hører til. Udelades feltet, er det bare en
  løsere/frilance-optræden uden fast bandnavn. Vises som et lille
  mærke/tag på hvert event-kort i den samlede liste på forsiden.
  (STGYE-siden viser ikke sin egen koncertliste — se sitestruktur
  ovenfor — så feltet bruges udelukkende til visning, ikke filtrering
  mellem sider.)

## Lokal udvikling

```bash
python3 -m http.server 8000
```
Åbn `http://localhost:8000`. Ingen installation nødvendig for selve
sitet (kun for `sync_events.py`, se `README.md`).

## Deploy

**Cloudflare Pages**, forbundet direkte til dette GitHub-repo:
- Push til `main` → Cloudflare bygger og deployer automatisk
  (ingen build command, output directory = `/`)
- Ingen webhook-secrets eller serveradgang nødvendig (modsat det
  DigitalOcean-autopull-setup til et andet, ikke-relateret projekt —
  se ikke det som skabelon her)
- Custom domain: `larsnagelalbertsen.dk`, DNS styret af Cloudflare
  (nameservere sat hos registrar dns.services)
- DNS-status ved sidste tjek: afventer nameserver-propagering fra
  registrar (kan tage op til 24 timer fra domænekøb)

## Næste skridt / kendt ufærdigt

- [x] Byg den nye forside (`/`) — to-kolonne hero + samlet koncertliste
- [x] Flyt den eksisterende `stan-gets-in-your-eyes`-prototype ind som
      `/stan-gets-in-your-eyes/`
- [x] Byg topnavigation med wordmark + faner (STGYE + Gennem tiden)
- [x] Tilføj `project`-felt til `events.json` og vis det som mærke på
      event-kortene
- [x] Skriv Lars' bio-tekst til forsiden
- [x] Vælg portrætfoto af Lars (beskåret til højkant/3:4)
- [x] Forbinde `sync_events.py` til et rigtigt Google Sheet
- [x] Cloudflare Worker-opsætningen for "opdater nu"-linket — testet
      end-to-end (Sheet-link → Worker → GitHub Action → `events.json`
      → live side). Linket ligger i selve Google Sheet'et til Lars.
      Husk: `GOOGLE_SHEET_CSV_URL`-secret skal være et **repository
      secret**, ikke et environment secret (workflowet definerer ingen
      `environment:`, så kun repo-secrets er synlige for det)
- [ ] Bekræft DNS er slået igennem (`larsnagelalbertsen.dk` skal give
      HTTP 200, ikke DNS-fejl)
- [ ] Billeder i `images/` er fra prototypen — bekræft med Lars om de
      skal bruges i den endelige version, eller om der kommer nye
- [ ] Bekræft booking-mail i footer er den rigtige
