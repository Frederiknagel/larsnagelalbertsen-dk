// Henter news.json (genereret af scripts/sync_news.py ud fra Google Doc'et)
// og tegner nyhedslisten på siden.

const DANISH_MONTHS_LONG = [
  "januar", "februar", "marts", "april", "maj", "juni",
  "juli", "august", "september", "oktober", "november", "december"
];

async function loadNews() {
  const listEl = document.getElementById("news-list");

  try {
    const response = await fetch("../news.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`news.json svarede med status ${response.status}`);

    const posts = await response.json();
    renderNews(listEl, posts);
  } catch (err) {
    console.error("Kunne ikke hente nyheder:", err);
    listEl.innerHTML = `<li class="news-empty">kunne ikke hente nyhederne lige nu 🎷</li>`;
  }
}

function renderNews(listEl, posts) {
  if (posts.length === 0) {
    listEl.innerHTML = `<li class="news-empty">ingen nyheder endnu — check tilbage snart!</li>`;
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

  // titel-formatering overtaget fra Google Doc'et (se scripts/sync_news.py)
  const titleClass = ["news-title",
    post.title_align === "center" ? "center" : "",
    post.title_serif ? "serif" : ""].filter(Boolean).join(" ");

  return `
    <li class="news-post">
      <h2 class="${titleClass}">${escapeHtml(post.title)}</h2>
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

document.addEventListener("DOMContentLoaded", loadNews);
