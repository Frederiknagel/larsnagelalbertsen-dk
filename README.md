# Lars Albertsen — website (prototype)

Prototype til en ny hjemmeside til jazzmusiker Lars Albertsen. Statisk
forside (HTML/CSS/JS) + et lille Python-script, der henter kommende
koncerter fra et Google Sheet, så Lars selv kan opdatere koncertlisten
uden at røre kode.

## Struktur

```
index.html         forside: hero, Spotify-embed, koncertliste
style.css           styling (mørk, "krøllet" jazz-æstetik)
script.js            henter events.json og tegner koncertlisten
events.json          koncertdata (genereres af scriptet nedenfor)
scripts/
  sync_events.py      henter Google Sheet -> skriver events.json
  requirements.txt    Python-afhængigheder
.env.sample           skabelon til lokal konfiguration
```

## Kør sitet lokalt

Statisk site, ingen build-step nødvendig:

```bash
python3 -m http.server 8000
```

Åbn derefter <http://localhost:8000> i browseren.

## Opdatér koncertlisten fra Google Sheets

1. Opret et Google Sheet med kolonnerne (præcis disse navne i første række):
   `date | time | venue | city | title | project | link`
   - `date` skal være `YYYY-MM-DD`, fx `2026-09-12`
   - `project` er valgfri — skriv `STGYE` for Stan Gets In Your Eyes,
     eller lad stå tomt for løsere/frilance-gigs
2. **Filer → Del → Publicer til web** → vælg arket → format **CSV** → Udgiv
3. Kopiér den genererede URL
4. `cp .env.sample .env` og indsæt URL'en i `GOOGLE_SHEET_CSV_URL`
5. Installer Python-afhængigheder og kør scriptet:

```bash
cd scripts
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 sync_events.py
```

Scriptet skriver en opdateret `events.json` i projektets rod. Genindlæs
siden i browseren for at se ændringerne.

## Deploy-idé (senere)

Samme mønster som det eksisterende `wavyswavy-autopull-app`-repo: en
cronjob på serveren kører `sync_events.py` med jævne mellemrum og
committer/pusher `events.json`, hvis den er ændret — det trigger den
eksisterende autopull-webhook og opdaterer sitet automatisk.

## Status

🚧 Prototype — Spotify-embed, billeder og farver/skrifttyper er
placeholders og skal erstattes med Lars' rigtige indhold.
