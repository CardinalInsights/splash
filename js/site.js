// Cardinal Insights — shared front-end logic.
// Each page calls the relevant render function once its DOM is ready.
// All content lives in /data/*.json so it can be updated without touching
// this file.

async function loadJSON(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

function formatDate(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
}

/* ---------- Experts page ---------- */

async function renderExperts() {
  const grid = document.getElementById("experts-grid");
  if (!grid) return;
  try {
    const experts = await loadJSON("data/experts.json");
    if (!experts.length) {
      grid.innerHTML = '<p class="status-message">No experts listed yet.</p>';
      return;
    }
    grid.innerHTML = experts.map(e => `
      <div class="card expert-card">
        <img class="expert-photo" src="${e.photo}" alt="${e.name}" loading="lazy"
             onerror="this.onerror=null;this.src='assets/expert-placeholder.svg';" />
        <h3>${e.name}</h3>
        <div class="expert-role">${e.role}</div>
        <p class="expert-bio">${e.bio}</p>
        ${e.profile ? `<a class="expert-linkedin" href="${e.profile}" target="_blank" rel="noopener">View profile ↗</a>` : ""}
      </div>
    `).join("");
  } catch (err) {
    grid.innerHTML = '<p class="status-message">Experts could not be loaded right now.</p>';
    console.error(err);
  }
}

/* ---------- Commentary / blog page ---------- */

async function renderCommentary() {
  const list = document.getElementById("post-list");
  if (!list) return;
  try {
    const posts = await loadJSON("data/posts.json");
    if (!posts.length) {
      list.innerHTML = '<p class="status-message">No posts yet — check back soon, or visit our <a href="https://medium.com/@cardinalinsights">Medium page</a> directly.</p>';
      return;
    }
    const sorted = [...posts].sort((a, b) => new Date(b.date) - new Date(a.date));
    list.innerHTML = sorted.map(p => `
      <article class="post-card">
        <div class="post-date">${formatDate(p.date)}</div>
        <h3><a href="${p.url}" target="_blank" rel="noopener">${p.title}</a></h3>
      </article>
    `).join("");
  } catch (err) {
    list.innerHTML = '<p class="status-message">Commentary could not be loaded right now.</p>';
    console.error(err);
  }
}

/* ---------- Publications page ---------- */

async function renderPublications() {
  const list = document.getElementById("pub-list");
  if (!list) return;
  try {
    const pubs = await loadJSON("data/publications.json");
    if (!pubs.length) {
      list.innerHTML = '<p class="status-message">No publications listed yet.</p>';
      return;
    }
    const sorted = [...pubs].sort((a, b) => new Date(b.date) - new Date(a.date));
    list.innerHTML = sorted.map(p => `
      <article class="card pub-card">
        <div class="pub-meta">${formatDate(p.date)}</div>
        <h3>${p.title}</h3>
        <p class="pub-summary">${p.summary}</p>
        <button class="btn" onclick="togglePubForm('${p.id}')">Get the report</button>
        <div class="email-form" id="form-${p.id}" style="display:none; margin-top:12px;">
          <form onsubmit="return requestReport(event, '${p.id}', '${p.title.replace(/'/g, "\\'")}')" style="display:flex; flex-wrap:wrap; gap:8px; width:100%;">
            <input type="email" id="email-${p.id}" placeholder="you@example.com" required aria-label="Email address" />
            <button type="submit" class="btn btn-secondary">Request report</button>
          </form>
        </div>
        <p class="form-note" id="note-${p.id}" style="display:none;">
          Your email app should open with a message ready to send — hit send and we'll get the report over to you directly.
        </p>
      </article>
    `).join("");
  } catch (err) {
    list.innerHTML = '<p class="status-message">Publications could not be loaded right now.</p>';
    console.error(err);
  }
}

function togglePubForm(id) {
  const form = document.getElementById(`form-${id}`);
  if (!form) return;
  form.style.display = form.style.display !== "none" ? "none" : "block";
}

function requestReport(event, pubId, title) {
  event.preventDefault();
  const emailInput = document.getElementById(`email-${pubId}`);
  const visitorEmail = emailInput.value.trim();
  const subject = `Request ${title} Report`;
  const body = `Please could you send me a copy of the report "${title}".\n\nMy email address: ${visitorEmail}`;
  const mailto = `mailto:info@cardinalinsights.co.uk?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  window.location.href = mailto;
  const note = document.getElementById(`note-${pubId}`);
  if (note) note.style.display = "block";
  return false;
}



document.addEventListener("DOMContentLoaded", () => {
  renderExperts();
  renderCommentary();
  renderPublications();
});
