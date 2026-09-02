# larsnagelalbertsen.dk

Hjemmeside for saxofonisten **Lars Stan Albertsen**. Bygget af hans søn
Frederik. Domænet er hans navn — sitet skal handle om *ham*, ikke kun
om ét projekt.

## Sitestruktur (besluttet)

Lars' primære, faste projekt er bandet **Stan Gets In Your Eyes**
("STGYE") — Danmarks ældste Bossa Nova-orkester, debut ved Copenhagen
Jazzfestival 1986. Men han spiller også med andre bands/i andre
sammenhænge, uden at det nødvendigvis er navngivne, faste projekter.

**Fem sider, tydeligt forskellige formål, delt topnavigation:**
`LARS STAN ALBERTSEN` (wordmark) · `Stan Gets In Your Eyes` ·
`Historien` · `Nyheder` · `Tekster`

### `/` — forsiden (Lars som hub)
Skal være **lige så simpelt og redaktionelt som albertewinding.dk**
— ikke bare samme farve/font, men samme **layout**:
- To-kolonne sektion: portræt af Lars til venstre, kort bio-tekst til
  højre (præcis som Albertes side)
- **Koncerter**-sektion nedenunder — én samlet liste, ALLE Lars'
  gigs (STGYE + løsere/frilance-optrædener), ikke kun STGYE
- Ingen Spotify-embed, intet billedgalleri her — det hører til på
  STGYE-siden

### `/stan-gets-in-your-eyes/` — bandsiden
- Hero-sektion, infotekst om bandet
- Billedgalleri (ensartet grid — nutidige, kuraterede fotos)
- Spotify-embed
- **Ingen egen koncertliste** — koncerter vises kun samlet på
  forsiden

### `/historien/` — arkiv
- Mindetekst om en tidligere æra af bandet, inkl. Lars Bo Enselmann
  (afdød tidligere bandmedlem — tekst skrevet med varsomhed, kun
  bekræftede grundfakta, ikke opdigtet biografisk indhold)
- Billedgalleri i **masonry-layout** (`.gallery--masonry`, ren CSS
  `columns`) — bevarer billedernes naturlige format i stedet for at
  beskære til ensartede bokse. Vigtigt her specifikt, fordi samlingen
  er en blandet pose (fotos, avisudklip, koncertprogrammer) hvor
  beskæring ville skjule indhold (fx gøre et program ulæseligt)

### `/nyheder/` — nyhedsopslag
- Lars skriver selv opslag i et Google Doc (se "Nyhedsdata" nedenfor)
- Viser nyeste øverst, ingen egen koncertliste eller galleri

### `/tekster/` — tekster/digte
- Samme mønster og genbrugte CSS/HTML-struktur som `/nyheder/` (se
  "Tekstdata" nedenfor), bare et separat Google Doc og separat
  indhold — Lars' egne tekster/digte, ikke nyhedsopdateringer

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
  `cloudflare-worker/README.md` for fuld opsætning. Samme knap
  opdaterer også nyheder (se nedenfor) i samme kørsel.
- **Nyt felt**: et valgfrit `project`-felt per event (fx
  `"project": "STGYE"`), så et event kan mærkes med hvilket
  band/projekt det hører til. Udelades feltet, er det bare en
  løsere/frilance-optræden uden fast bandnavn. Vises som et lille
  mærke/tag på hvert event-kort i den samlede liste på forsiden.
  (STGYE-siden viser ikke sin egen koncertliste — se sitestruktur
  ovenfor — så feltet bruges udelukkende til visning, ikke filtrering
  mellem sider.)

## Nyhedsdata (`news.json`)

Samme mønster som koncerter, men fra et **Google Doc** i stedet for et
Sheet (fri tekst passer bedre til nyhedsopslag end regneark-celler):

- `scripts/sync_news.py` henter et **publiceret** Google Doc (som
  webside/HTML), parser det med BeautifulSoup, og skriver `news.json`
- Konvention Lars skal følge: hvert opslag starter med Docs-stilen
  **"Overskrift 2"** (titel, evt. med `YYYY-MM-DD —`-præfiks der
  udtrækkes som dato), efterfulgt af brødtekst indtil næste
  "Overskrift 2"
- Kræver `GOOGLE_DOC_HTML_URL` lokalt i `.env` — eller som GitHub
  repo-secret (samme sted som `GOOGLE_SHEET_CSV_URL`)
- Håndterer to Google-specifikke kvirks: samme UTF-8-encoding-fælde
  som Sheets-CSV'en, samt at Docs pakker links ind i
  `google.com/url?q=...`-redirects, som pakkes ud til det rigtige
  mål-link (`unwrap_google_redirect()`)
- Tilladt HTML i indlæg begrænset til en hvidliste (`ALLOWED_TAGS`) —
  luger Google Docs' egne `<span class="c12">`-styling-rester væk
- **Billeder i indlæg understøttes** (indsæt direkte i Google Doc'et,
  HEIC konverteres automatisk af Google ved upload). VIGTIGT: Googles
  interne billed-URL'er (`docs.google.com/docs-images-rt/...`) har en
  `cross-origin-resource-policy: same-site`-header, som forhindrer dem
  i at blive vist indlejret på et andet site — derfor downloader
  `download_image()` billedet og gemmer det som en rigtig fil i
  `images/nyheder/` (filnavn = content-hash, så gentagne kørsler ikke
  skaber dubletter), og `src` skrives om til den lokale sti. GitHub
  Action'en committer også disse filer, ikke kun `news.json`.
- **Kvirk (rettet 2026-09-02)**: når man indsætter et billede i sit eget
  afsnit i Doc'et, kan afsnittet arve "Overskrift 2"-stilen fra linjen
  omkring — i den publicerede HTML bliver det en *tom* `<h2>` der kun
  rummer `<img>`. `parse_html_to_posts()` behandlede alt `<h1>/<h2>` som
  en indlægs-overskrift og tabte billedet. Nu: en overskrift uden tekst
  er ikke en indlægs-grænse; dens indhold behandles som brødtekst i det
  aktuelle indlæg (`is_heading = ... and el.get_text(strip=True) != ""`).
- **Formatering fra Doc'et (tilføjet 2026-09-02)**: Google Docs lægger AL
  formatering i CSS-klasser (`.c3{font-family:"Times New Roman"}`), ikke i
  tags — så tag-hvidlisten smed det hele væk. `parse_doc_style_classes()`
  parser nu Docs' `<style>`-tabel, og et lille **kurateret** udvalg
  oversættes: `text-align:center` → `<p class="center">`, serif-familie →
  `<p class="serif">` (vist i Lora, webfont kun på Tekster-siden), fed/
  kursiv fra span-klasser → `<strong>/<em>`, tom linje mellem strofer →
  `<p class="gap">`. Titlens egen justering/serif → `title_align`/
  `title_serif` i JSON, sat på `<h2>` af `news.js`/`texts.js`. **Vilkårlige
  fonte slippes bevidst ikke løs** — kun serif/ikke-serif, for at bevare
  det monokrome udtryk. Styling-CSS ligger på `.news-body`-klasserne i
  `style.css` (deles med Tekster).
- **Status: sat op og testet med et rigtigt Google Doc**, inkl. billede
  (Lars' "Ny hjemmeside"-opslag har et saxofon-foto)

## Tekstdata (`texts.json`)

**Bogstaveligt talt samme kode som Nyhedsdata ovenfor**, kopieret 1:1
til `scripts/sync_texts.py` med navne skiftet ud (`GOOGLE_TEXTS_DOC_HTML_URL`,
`images/tekster/`, `texts.json`). Genbruger også samme CSS-klasser
(`.news-list`, `.news-post` osv.) i `tekster/index.html` — bevidst
ikke omdøbt til noget generisk fælles, for at holde de to features
nemme at ræsonnere om hver for sig, selvom det er lidt duplikeret kode.
- `texts.js` er en næsten identisk kopi af `news.js` (anden fetch-URL,
  andet element-id: `#texts-list`)
- Den tomme-overskrift-kvirk **og** formaterings-oversættelsen fra
  Nyhedsdata ovenfor gælder også her (samme 1:1-kopi). Serif-digte er
  primært hvorfor formaterings-delen blev lavet — se Nyhedsdata.
- **Status: live.** Lars' digt "FORÅR" er synket 2026-09-02 og vises
  centreret i serif (Lora), som han satte det op i Doc'et.
  `GOOGLE_TEXTS_DOC_HTML_URL` er sat som repository secret, så
  "opdater nu"-knappen virker hele vejen igennem.

## Lokal udvikling

```bash
python3 -m http.server 8000
```
Åbn `http://localhost:8000`. Ingen installation nødvendig for selve
sitet (kun for `sync_events.py`, se `README.md`).

## SEO

Domænet var i lang tid utilgængeligt (se "DNS-status" nedenfor), så
SEO-arbejdet startede først, da det gik live. Implementeret på alle
fire sider:

- Unikke `<meta name="description">` + Open Graph/Twitter-tags per side
- `<link rel="canonical">` peger altid på `larsnagelalbertsen.dk`
  (vigtigt: sitet er også tilgængeligt på `*.workers.dev` — canonical
  forhindrer duplicate-content-forvirring hos Google)
- JSON-LD structured data: `Person` (forsiden) med `alternateName` for
  at dække både "Lars Nagel Albertsen" (rigtige efternavn, matcher
  domænet) og "Lars Stan Albertsen" (visningsnavnet på selve siden);
  `MusicGroup` (STGYE-siden) med genre/stiftelsesår/`sameAs`-links til
  Spotify/Instagram/Facebook
- Skjult (`.visually-hidden`) `<h1>` på forsiden med "Lars Nagel
  Albertsen" — forsiden havde ingen `<h1>` overhovedet før, og det
  synlige navn er "Stan"-varianten, så den skjulte h1 dækker den
  anden navnevariant uden at ændre det visuelle design
  (`.visually-hidden` er en standard tilgængeligheds-klasse, se
  `style.css`)
- **Historien/Nyheder/Tekster har også `.visually-hidden` `<h1>`**
  (2026-09-02): den synlige "Historien"/"Nyheder"/"Tekster"-overskrift
  blev fjernet — den aktive fane i topnavigationen viser allerede
  hvilken side man er på, så den var visuel støj. `<h1>`'en er beholdt
  skjult, så hver side stadig har præcis én h1 for SEO/skærmlæsere.
- Lille disambiguerings-sætning på STGYE-siden ("ikke at forveksle med
  Stan Getz") — både for besøgende og for at fange den søgetrafik
- `robots.txt` + `sitemap.xml` i roden
- `favicon.svg`

**Bevidst navnestrategi**: det *viste* navn på siden er "Lars Stan
Albertsen" (Lars' eget ønske), men "Lars Nagel Albertsen" (det
egentlige efternavn, matcher domænet) er bevidst vævet ind i
meta-beskrivelser, alt-tekster og strukturerede data, så begge
navnevarianter er søgbare.

**Ikke gjort (kræver Lars/Frederik's egen handling, ikke noget jeg kan
klare fra kode)**:
- [ ] Opret Google Search Console og indsend `sitemap.xml`
- [ ] Opdatér Instagram/Facebook-bio til at linke til
      larsnagelalbertsen.dk (backlinks fra sociale profiler tæller
      mere for placering end noget teknisk på selve siden)
- [ ] Overvej at få jazzklubber/festivaller, der nævner bandet, til at
      linke til sitet

## Deploy

**Cloudflare Pages**, forbundet direkte til dette GitHub-repo:
- Push til `main` → Cloudflare bygger og deployer automatisk
  (ingen build command, output directory = `/`)
- Ingen webhook-secrets eller serveradgang nødvendig (modsat det
  DigitalOcean-autopull-setup til et andet, ikke-relateret projekt —
  se ikke det som skabelon her)
- Custom domain: `larsnagelalbertsen.dk`, DNS styret af Cloudflare
  (nameservere sat hos registrar dns.services)
- **DNS-status: LIVE.** Root cause for den lange forsinkelse var
  hverken nameservere, DNSSEC eller det (irrelevante, ubrugte) "DNS
  Hotel"-produkt hos dns.services — det var en obligatorisk
  **MitID-identitetsbekræftelse hos Punktum dk (DK Hostmaster)**,
  påkrævet inden for 4 dage efter registrering af ethvert nyt
  `.dk`-domæne. Domænet stod som "Reserved" indtil den blev
  gennemført. Værd at huske, hvis domænet nogensinde skal
  fornys/overføres igen.

## Næste skridt / kendt ufærdigt

- [x] Byg den nye forside (`/`) — to-kolonne hero + samlet koncertliste
- [x] Flyt den eksisterende `stan-gets-in-your-eyes`-prototype ind som
      `/stan-gets-in-your-eyes/`
- [x] Byg topnavigation med wordmark + faner (STGYE + Historien)
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
- [x] Omdøb Gennem tiden → Historien (side + billedmappe + URL)
- [x] Masonry-galleri på Historien (`.gallery--masonry`, ren CSS)
- [x] Skift visningsnavn til "Lars Stan Albertsen" overalt (domænet
      forbliver larsnagelalbertsen.dk)
- [x] Byg `/nyheder/` — ny fane, `sync_news.py` + Google Doc-flow,
      samme "opdater nu"-knap som koncerter (én kørsel opdaterer begge)
- [x] Google Doc til nyheder oprettet, publiceret, testet mod
      `sync_news.py` — inkl. billede-download (`images/nyheder/`)
- [x] `GOOGLE_DOC_HTML_URL` tilføjet som repository secret på GitHub
- [x] **DNS/domæne er live** — se "DNS-status" ovenfor for root cause
      (MitID-aktivering hos Punktum dk, ikke et teknisk fejl)
- [x] Grundlæggende SEO (meta/OG-tags, JSON-LD, sitemap, robots.txt) —
      se "SEO"-sektionen ovenfor for detaljer og resterende manuelle
      trin (Search Console, backlinks)
- [x] Erstat test-indlægget i news.json/Doc'et med et rigtigt
      nyhedsopslag — Lars har selv skrevet et rigtigt indlæg
- [x] Bekræft booking-mail/telefon i footer — rettet til
      lars_albertsen@hotmail.com + 26 85 34 62 på Lars' anmodning
- [x] Byg `/tekster/` — femte fane, `sync_texts.py` (kopi af
      `sync_news.py`), samme "opdater nu"-knap opdaterer nu koncerter/
      nyheder/tekster i én kørsel
- [x] Tilføj `GOOGLE_TEXTS_DOC_HTML_URL` som repository secret på
      GitHub — sat 2026-09-02 via `gh secret set` (værdi fra `.env`).
      Samtidig rettet en bug i `sync-events.yml`: `git add
      images/tekster/` fejlede med "pathspec did not match any files"
      (mappen fandtes ikke endnu), og `bash -e` dræbte hele steppet før
      `git push` — hver sync-kørsel havde fejlet siden 29. aug. Nu
      `mkdir -p images/nyheder images/tekster` før `git add`.
- [x] Lars har skrevet sin første tekst i tekster-Doc'et (digtet
      "FORÅR") — synket til `texts.json` 2026-09-02, siden er live.
      Centrering + serif fra Doc'et vises nu (se Tekstdata → Formatering)
- [ ] Billeder i `images/` er fra prototypen — bekræft med Lars om de
      skal bruges i den endelige version, eller om der kommer nye
- [ ] `images/nyheder/d0f8bd2ae933f049.png` er et forældreløst
      test-billede fra det oprindelige nyheds-testopslag (ikke længere
      refereret nogen steder) — kan slettes ved lejlighed
