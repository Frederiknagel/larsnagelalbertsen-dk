// Henter events.json (genereret af scripts/sync_events.py ud fra Google Sheet'et)
// og tegner koncertlisten på siden.

const DANISH_MONTHS_SHORT = [
  "jan", "feb", "mar", "apr", "maj", "jun",
  "jul", "aug", "sep", "okt", "nov", "dec"
];

async function loadEvents() {
  const listEl = document.getElementById("events-list");

  try {
    const response = await fetch("events.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`events.json svarede med status ${response.status}`);

    const events = await response.json();
    renderEvents(listEl, events);
  } catch (err) {
    console.error("Kunne ikke hente koncerter:", err);
    listEl.innerHTML = `<li class="events-empty">kunne ikke hente koncertlisten lige nu 🎷</li>`;
  }
}

function renderEvents(listEl, events) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Nyligt afholdte koncerter bliver stående på listen i 2 måneder — så
  // siden ikke virker tom lige efter en optræden. Ældre end det droppes.
  const cutoff = new Date(today);
  cutoff.setMonth(cutoff.getMonth() - 2);

  const inWindow = events.filter((e) => e.date && new Date(e.date) >= cutoff);

  // kommende først (nærmeste dato øverst), derefter de afholdte (nyeste først)
  const upcoming = inWindow
    .filter((e) => new Date(e.date) >= today)
    .sort((a, b) => new Date(a.date) - new Date(b.date));
  const past = inWindow
    .filter((e) => new Date(e.date) < today)
    .sort((a, b) => new Date(b.date) - new Date(a.date));

  if (upcoming.length === 0 && past.length === 0) {
    listEl.innerHTML = `<li class="events-empty">ingen kommende koncerter lige nu — check tilbage snart!</li>`;
    return;
  }

  listEl.innerHTML = [
    ...upcoming.map((e) => eventToHtml(e, false)),
    ...past.map((e) => eventToHtml(e, true)),
  ].join("");
}

function eventToHtml(event, isPast) {
  const date = new Date(event.date);
  const day = date.getDate();
  const month = DANISH_MONTHS_SHORT[date.getMonth()];

  // kun rigtige URL'er bliver et link — Lars skriver fx "Ikke offentligt"
  // i Sheet'et for lukkede arrangementer, og det skal ikke blive et
  // (i øvrigt ødelagt) hyperlink
  const linkHtml = /^https?:\/\//i.test(event.link || "")
    ? `<a class="event-link" href="${event.link}" target="_blank" rel="noopener">Link →</a>`
    : "";

  // valgfrit projekt-mærke (fx "STGYE") — udelades for løsere/frilance-optrædener
  const projectHtml = event.project
    ? `<span class="event-project">${escapeHtml(event.project)}</span>`
    : "";

  return `
    <li class="event-card${isPast ? " event-card--past" : ""}">
      <div class="event-date">${day}<small>${month}</small></div>
      <div class="event-info">
        <p class="event-venue">${escapeHtml(event.venue)}${event.title ? " · " + escapeHtml(event.title) : ""}${projectHtml}</p>
        <p class="event-city">${escapeHtml(event.city)}${event.time ? " · kl. " + event.time : ""}</p>
      </div>
      ${linkHtml}
    </li>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

document.addEventListener("DOMContentLoaded", loadEvents);
