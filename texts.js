// Henter texts.json (genereret af scripts/sync_texts.py ud fra Google Doc'et)
// og tegner tekstlisten på siden. Genbruger samme CSS-klasser som
// nyhedssiden (news.js) — samme visuelle behandling, andet indhold.

const DANISH_MONTHS_LONG = [
  "januar", "februar", "marts", "april", "maj", "juni",
  "juli", "august", "september", "oktober", "november", "december"
];

async function loadTexts() {
  const listEl = document.getElementById("texts-list");

  try {
    const response = await fetch("../texts.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`texts.json svarede med status ${response.status}`);

    const posts = await response.json();
    renderTexts(listEl, posts);
  } catch (err) {
    console.error("Kunne ikke hente tekster:", err);
    listEl.innerHTML = `<li class="news-empty">kunne ikke hente teksterne lige nu 🎷</li>`;
  }
}

function renderTexts(listEl, posts) {
  if (posts.length === 0) {
    listEl.innerHTML = `<li class="news-empty">ingen tekster endnu — check tilbage snart!</li>`;
    return;
  }

  // nyeste først; indlæg uden dato holdes til sidst i deres oprindelige rækkefølge
  const sorted = [...posts].sort((a, b) => {
    if (!a.date) return 1;
    if (!b.date) return -1;
    return new Date(b.date) - new Date(a.date);
  });

  listEl.innerHTML = sorted.map(postToHtml).join("");
}

function postToHtml(post) {
  const dateHtml = post.date ? `<p class="news-date">${formatDate(post.date)}</p>` : "";

  return `
    <li class="news-post">
      <h2 class="news-title">${escapeHtml(post.title)}</h2>
      ${dateHtml}
      <div class="news-body">${post.body_html || ""}</div>
    </li>
  `;
}

function formatDate(isoDate) {
  const d = new Date(isoDate);
  if (isNaN(d)) return isoDate;
  return `${d.getDate()}. ${DANISH_MONTHS_LONG[d.getMonth()]} ${d.getFullYear()}`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

document.addEventListener("DOMContentLoaded", loadTexts);
