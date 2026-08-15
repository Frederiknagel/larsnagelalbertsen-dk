# Opsætning: "Opdater koncerter"-linket

Dette er den fulde kæde: **Google Sheet-link → Cloudflare Worker →
GitHub Action → `events.json` opdateret → Cloudflare Pages deployer**.

## 1. GitHub Personal Access Token

Opret en **fine-grained** token, scoped kun til dette repo:

1. Gå til **github.com/settings/personal-access-tokens/new**
2. Token name: `larsnagelalbertsen-dk sync trigger`
3. Expiration: vælg fx 1 år (husk at forny den, når den udløber)
4. Repository access: **Only select repositories** → vælg `larsnagelalbertsen-dk`
5. Permissions → **Repository permissions** → **Actions**: sæt til
   **Read and write**
6. Generate token → **kopiér den med det samme** (den vises kun én gang)

## 2. Repo-secret til Google Sheet-URL'en

GitHub Action'en (`sync-events.yml`) skal kende jeres CSV-URL:

1. Gå til `github.com/Frederiknagel/larsnagelalbertsen-dk` → **Settings →
   Secrets and variables → Actions → New repository secret**
2. Name: `GOOGLE_SHEET_CSV_URL`
3. Value: jeres publicerede CSV-link (samme som i lokal `.env`)
4. Add secret

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

Indsæt linket i en celle i Google Sheet'et (fx en note øverst: **"Klik
her for at opdatere hjemmesiden med det samme"**), eller tegn en rigtig
knap/figur i arket og sæt linket som dens hyperlink.

## 6. Test det

Klik på linket → du bør se en bekræftelsesbesked i browseren
("✅ Koncertlisten opdateres nu..."). Tjek derefter:
- `github.com/Frederiknagel/larsnagelalbertsen-dk/actions` — en ny
  kørsel af "Sync koncerter fra Google Sheet" skulle dukke op
- Efter ca. et halvt minut: den live side skulle vise ændringen
