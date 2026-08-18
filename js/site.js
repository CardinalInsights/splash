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
          <form action="${p.formAction}" method="post" target="_blank" style="display:flex; flex-wrap:wrap; gap:8px; width:100%;">
            <input type="email" name="email" placeholder="you@example.com" required aria-label="Email address" />
            <button type="submit" class="btn btn-secondary">Verify &amp; email me the link</button>
          </form>
        </div>
        <p class="form-note" id="note-${p.id}" style="display:none;">
          Check your inbox to confirm your email — once confirmed you'll land on a page with the download link.
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
  const note = document.getElementById(`note-${id}`);
  if (!form) return;
  const showing = form.style.display !== "none";
  form.style.display = showing ? "none" : "block";
  note.style.display = showing ? "none" : "block";
}

/* ---------- Unlock page (after confirmed email redirect) ---------- */

async function renderUnlock() {
  const target = document.getElementById("unlock-result");
  if (!target) return;
  const params = new URLSearchParams(window.location.search);
  const docId = params.get("doc");
  if (!docId) {
    target.innerHTML = '<p class="status-message">No report specified. Return to the <a href="publications.html">Publications</a> page.</p>';
    return;
  }
  try {
    const pubs = await loadJSON("data/publications.json");
    const pub = pubs.find(p => p.id === docId);
    if (!pub) {
      target.innerHTML = '<p class="status-message">We could not find that report. Return to the <a href="publications.html">Publications</a> page.</p>';
      return;
    }
    target.innerHTML = `
      <h2>${pub.title}</h2>
      <p>Thanks for confirming your email — your report is ready.</p>
      <a class="btn" href="${pub.pdf}" download>Download PDF</a>
    `;
  } catch (err) {
    target.innerHTML = '<p class="status-message">Something went wrong loading your report.</p>';
    console.error(err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  renderExperts();
  renderCommentary();
  renderPublications();
  renderUnlock();
});
