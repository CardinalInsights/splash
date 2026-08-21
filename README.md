# Cardinal Insights website

A static site — no build step, no server, no framework. Every page is plain
HTML/CSS/JS, and everyday content updates (new blog posts, experts,
publications) happen by editing a JSON file, not code.

Live at **https://cardinalinsights.co.uk** (custom domain, HTTPS enforced —
the underlying host is still GitHub Pages, repo `CardinalInsights/splash`).

```
/
├── index.html              Landing / About page — nav: Home, Commentary, Experts
├── commentary.html         Blog index (auto-pulled from Beehiiv) + newsletter signup
├── experts.html            Headshots + bios
├── publications.html       Request-a-report page — built and working, but not
│                           linked from the nav on any page (see section 4)
├── favicon.ico             Favicon — must stay at repo root
├── CNAME                   Contains "cardinalinsights.co.uk" — auto-created by
│                           GitHub when the custom domain was set up; don't delete
├── css/style.css           Shared styles (fonts, palette, graph-paper bg)
├── js/site.js               Renders experts/commentary/publications from JSON
├── data/
│   ├── experts.json         <- edit to add/remove an expert
│   ├── publications.json    <- edit to add/remove a report
│   └── posts.json           Auto-generated cache of Beehiiv posts — don't hand-edit
├── scripts/fetch_posts.py  Pulls the Beehiiv RSS feed into data/posts.json
├── .github/workflows/fetch-posts.yml   Runs the script daily (06:00 UTC) + on demand
├── assets/                  Logo, tagline, expert headshots, favicon PNGs, placeholder
├── logo.png, tagline.png    Brand assets — logo is wrapped in a link to index.html
```

Look and feel — font (Helvetica), the blue/green/orange/red/purple accent
palette, and the graph-paper background — all live as CSS variables at the
top of `css/style.css`, so a colour tweak only needs to happen in one place.
Current brand red is `#a22617` (`--button-red`).

---

## 1. Hosting and domain

Hosted on **GitHub Pages**, free, from the `CardinalInsights/splash` repo.
The custom domain `cardinalinsights.co.uk` points at it via DNS (four A
records at your registrar pointing to GitHub's servers, plus a CNAME for
`www`) — set up once, no ongoing maintenance needed. If DNS or HTTPS ever
needs revisiting: repo → **Settings → Pages**, custom domain field, "Enforce
HTTPS" checkbox.

**Important:** the same domain also handles `info@cardinalinsights.co.uk`
email via MX records at the registrar. Those are separate from the site's A/
CNAME records — if you ever touch DNS settings again, leave anything with
"MX" in the record type alone.

To deploy any change: edit files directly on GitHub (pencil icon → edit →
commit), or upload files via **Add file → Upload files**. GitHub keeps full
history, so any change can be undone via the **Revert** option on that
commit if something goes wrong. Hard refresh (`Ctrl/Cmd+Shift+R`) after
deploying — GitHub Pages caches aggressively, especially for CSS, JSON, and
favicons.

---

## 2. Updating content (no code required)

All of these are plain-text edits via GitHub's web editor (pencil icon on
the file). Save/commit and the live site updates within a minute or two
(plus your own browser cache — hard refresh to check).

### Add or remove an expert
Edit `data/experts.json`. Each entry:
```json
{
  "id": "unique-slug",
  "name": "Full Name",
  "role": "Their title",
  "photo": "assets/experts/filename.jpg",
  "bio": "Two or three sentences. Use \n\n inside the string for a paragraph break.",
  "profile": "https://www.linkedin.com/in/their-profile"
}
```
Upload the headshot to `assets/experts/`. If a photo is missing or fails to
load, a neutral placeholder silhouette shows automatically. `profile` is
optional and doesn't have to be LinkedIn — a personal site works too; leave
it out for anyone who'd rather not be linked, and always get permission
before adding one. To remove someone, delete their whole `{ }` block.

**Every entry except the last one in the array needs a comma after its
closing `}`. No entry should have a trailing comma after its last property
line.** This has been the single most common editing mistake across this
project — when in doubt, paste the file into
[jsonlint.com](https://jsonlint.com) before committing.

### Add or remove a publication
Edit `data/publications.json`:
```json
{
  "id": "unique-slug",
  "title": "Report title",
  "date": "2026-06-01",
  "summary": "One or two sentence summary."
}
```
No PDF to upload — reports aren't hosted on the site (see section 4). Same
comma rules as above apply.

### Landing page and Commentary page intro copy
Body paragraphs on `index.html` and the intro text on `commentary.html` are
plain HTML — edit the text between `<p>...</p>` tags directly, leave tags
and attributes alone.

### Commentary posts
Nothing to do manually — pulled automatically from Beehiiv (see section 3).

---

## 3. Newsletter and Commentary (Beehiiv)

Beehiiv (free plan, up to 2,500 subscribers) runs both the newsletter
signup and the Commentary content — **Medium is not used anywhere in this
site.**

**Newsletter signup box** (appears on both `index.html` and
`commentary.html`): Beehiiv embeds are a `<script>` snippet, not a plain
HTML form. To change the form itself, go to Beehiiv → **Subscribers →
Subscribe forms**, edit or create a form, **Save & get embed code**, then
paste the `<script>...</script>` it gives you into the
`<div id="beehiiv-embed-placeholder">` on each page. Styling (colours,
fonts, padding) is controlled inside Beehiiv's own form builder Style tab,
not by this site's CSS — the form renders in an iframe your stylesheet
can't reach into.

**Commentary posts**: write and publish normally in Beehiiv. A GitHub
Action (`.github/workflows/fetch-posts.yml`) runs `scripts/fetch_posts.py`
once a day, which fetches your Beehiiv RSS feed and writes the result to
`data/posts.json` — that's what `commentary.html` displays, including each
post's **subtitle** as a short preview line beneath the title (set the
Subtitle field in Beehiiv's post editor to control this).

**To pull a new post in immediately** rather than waiting for the daily
run: repo → **Actions** tab → "Fetch Beehiiv posts" → **Run workflow**. If
a freshly-published post doesn't show up right away even after running it,
Beehiiv's RSS feed can lag a few minutes behind the publish action — wait a
bit and run again rather than assuming something's broken.

The feed URL is hardcoded in `scripts/fetch_posts.py` (the `FEED_URL`
line) — only needs changing if you ever regenerate the RSS feed URL in
Beehiiv's settings.

---

## 4. Publications page — currently hidden, fully functional

`publications.html` works end to end, but isn't linked from the site
navigation on any page — it's reachable only by direct URL
(`cardinalinsights.co.uk/publications.html`). This was a deliberate choice
to take the section offline for now without losing any of the underlying
work.

**How the page itself works:** given low expected request volume, there's
no PDF hosting or email-gating service involved at all. A visitor clicks
"Request report," enters their email, and it opens a pre-filled `mailto:`
to `info@cardinalinsights.co.uk` with the subject `Request <Title> Report`
— they hit send in their own email app, it lands in your inbox as a normal
email, and you reply with the PDF attached manually. Zero third-party
services, nothing that can silently break.

**To bring the section back into the nav:** add this line to the
`<nav class="site-nav">` block in `index.html`, `commentary.html`, and
`experts.html` (and ideally `publications.html` itself, for consistency):
```html
<a href="publications.html">Publications</a>
```
Nothing else needs to change — the data file, JS rendering logic, and CSS
were never removed, only the links pointing to the page.

---

## 5. Favicon

`favicon.ico` lives at the **repo root** (same level as `index.html`) —
browsers check that exact location by default. The PNG variants
(`favicon-16x16.png`, `favicon-32x32.png`, `apple-touch-icon.png`, etc.)
live in `assets/`. Every page's `<head>` needs these four lines for the
favicon to show — if a new page is ever added, copy them in from an
existing page:
```html
<link rel="icon" href="favicon.ico" sizes="any" />
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32x32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="assets/favicon-16x16.png" />
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png" />
```
The icon is a white "C" (Liberation Sans Bold, a Helvetica-metric match) on
the exact red sampled from `logo.png` (`#a81102`).

---

## 6. Resource summary (all free tiers)

| Need | Tool | Cost |
|---|---|---|
| Hosting | GitHub Pages | Free |
| Domain | cardinalinsights.co.uk (existing registration) | — |
| Newsletter + blog | Beehiiv (up to 2,500 subs) | Free |
| Blog auto-sync | GitHub Actions (scheduled workflow) | Free (public repo) |
| Publication requests | `mailto:` link, sent manually | Free |

No paid services are required for anything currently live on the site.

---

## 7. Responsiveness

Two-column layout (fixed sidebar + content) at ≥768px width, stacking to a
single column below that. The experts grid reflows 1 → 2 → 3 columns as
width increases. All forms and cards use fluid widths.
