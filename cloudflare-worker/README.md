# Opsætning: "Opdater nu"-linket

Dette er den fulde kæde: **Google Sheet/Doc-link → Cloudflare Worker →
GitHub Action → `events.json`/`news.json`/`texts.json` opdateret →
Cloudflare Pages deployer**. Samme knap/link opdaterer koncerter,
nyheder og tekster i én kørsel.

## 1. GitHub Personal Access Token

Opret en **fine-grained** token, scoped kun til dette repo:

1. Gå til **github.com/settings/personal-access-tokens/new**
2. Token name: `larsnagelalbertsen-dk sync trigger`
3. Expiration: vælg fx 1 år (husk at forny den, når den udløber)
4. Repository access: **Only select repositories** → vælg `larsnagelalbertsen-dk`
5. Permissions → **Repository permissions** → **Actions**: sæt til
   **Read and write**
6. Generate token → **kopiér den med det samme** (den vises kun én gang)

## 2. Repo-secrets til Google Sheet + Doc-URL'erne

GitHub Action'en (`sync-events.yml`) skal kende alle tre URL'er. **Vigtigt:**
de skal være **repository secrets**, ikke "Environment secrets" (workflowet
definerer ingen `environment:`, så kun repo-secrets er synlige for det).

1. Gå til `github.com/Frederiknagel/larsnagelalbertsen-dk` → **Settings →
   Secrets and variables → Actions** → fanen **"Secrets"** →
   **"Repository secrets"** → **New repository secret**
2. Tilføj `GOOGLE_SHEET_CSV_URL` = jeres publicerede CSV-link
3. Tilføj `GOOGLE_DOC_HTML_URL` = jeres publicerede nyheds-Doc-link
   (webside-format, ikke CSV)
4. Tilføj `GOOGLE_TEXTS_DOC_HTML_URL` = jeres publicerede tekster-Doc-link
   (webside-format, ikke CSV)

## 3. Opret Cloudflare Worker

1. Cloudflare-dashboard → **Workers & Pages → Create application → Workers**
2. Giv den et navn, fx `larsnagelalbertsen-sync-trigger`
3. Når den er oprettet → **Edit code**
4. Slet standard-koden, indsæt indholdet af [`trigger-sync.js`](trigger-sync.js) i stedet
5. **Deploy**

## 4. Tilføj secrets til Workeren

Under Worker-projektet → **Settings → Variables and Secrets**:

- **Secret**: `GITHUB_TOKEN` = tokenet fra trin 1
- **Secret** (valgfrit, men anbefalet): `TRIGGER_KEY` = en selvvalgt
  hemmelig streng (fx en tilfældig kode), så linket ikke kan bruges af
  hvem som helst, der tilfældigvis finder URL'en

Gem/deploy igen efter du har tilføjet dem.

## 5. Find Worker-URL'en og læg den i Google Sheet

Din Worker-URL ser ud i stil med:
```
https://larsnagelalbertsen-sync-trigger.<din-cloudflare-subdomain>.workers.dev
```
Hvis du satte `TRIGGER_KEY`, skal linket være:
```
https://larsnagelalbertsen-sync-trigger.<...>.workers.dev/?key=DIN_HEMMELIGE_KODE
```

**Brug samme link i Sheet'et og begge Docs** — det er den samme knap,
der opdaterer alt. Sæt det som en **tegnet figur/knap med link** (ikke
tekst-i-celle — det kræver et ekstra, upålideligt klik på en pop-up-chip
i Google Sheets/Docs for rent faktisk at navigere).

## 6. Test det

Klik på linket → du bør se en bekræftelsesbesked i browseren
("✅ Koncertlisten opdateres nu — der kan gå op til 10 minutter...").
Tjek derefter:
- `github.com/Frederiknagel/larsnagelalbertsen-dk/actions` — en ny
  kørsel skulle dukke op
- Efter et par minutter: den live side skulle vise ændringen
