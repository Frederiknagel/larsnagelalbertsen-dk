/**
 * trigger-sync.js
 * ================
 *
 * Lille Cloudflare Worker der fungerer som "opdater"-knappen fra
 * Google Sheet'et. Modtager et simpelt GET-request (klik på et link)
 * og trigger derefter GitHub Action'en "sync-events.yml" via GitHub's
 * API — den hemmelige GitHub-nøgle ligger sikkert i Workerens secrets,
 * aldrig i selve linket.
 *
 * Opsætning (gøres i Cloudflare-dashboardet, ikke her i koden):
 *   1. Opret en ny Worker, indsæt denne fil som koden
 *   2. Under Worker-projektets "Settings -> Variables and Secrets":
 *      - Tilføj secret GITHUB_TOKEN = <din fine-grained PAT>
 *      - (valgfrit) Tilføj secret TRIGGER_KEY = en selvvalgt hemmelig
 *        streng, hvis du vil beskytte linket mod tilfældige klik
 *   3. Deploy
 *   4. Brug Worker-URL'en (evt. med ?key=TRIGGER_KEY) som linket i
 *      Google Sheet'et
 */

const GITHUB_OWNER = "Frederiknagel";
const GITHUB_REPO = "larsnagelalbertsen-dk";
const WORKFLOW_FILE = "sync-events.yml";

export default {
  async fetch(request, env) {
    // valgfrit: simpel beskyttelse mod tilfældige/ondsindede klik
    if (env.TRIGGER_KEY) {
      const url = new URL(request.url);
      if (url.searchParams.get("key") !== env.TRIGGER_KEY) {
        return new Response("Forkert eller manglende nøgle.", { status: 403 });
      }
    }

    const githubUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`;

    const response = await fetch(githubUrl, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
        "Accept": "application/vnd.github+json",
        "User-Agent": "larsnagelalbertsen-dk-sync-trigger",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: "main" }),
    });

    if (response.status === 204) {
      return new Response(
        "✅ Koncertlisten opdateres nu — der kan gå op til 10 minutter, før ændringen er live på hjemmesiden.",
        { headers: { "Content-Type": "text/plain; charset=utf-8" } }
      );
    }

    const errorText = await response.text();
    return new Response(
      `❌ Noget gik galt (status ${response.status}): ${errorText}`,
      { status: 500, headers: { "Content-Type": "text/plain; charset=utf-8" } }
    );
  },
};
