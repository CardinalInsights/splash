# Cardinal Insights website

A static site — no build step, no server, no framework. Every page is plain
HTML/CSS/JS, and everyday content updates (new blog posts, experts,
publications) happen by editing a JSON file, not code.

```
/
├── index.html                 Landing / About page
├── commentary.html            Blog index (auto-pulled from Medium)
├── experts.html                Headshots + bios
├── publications.html          Reports, gated behind a verified email
├── publications-unlocked.html Shown after a subscriber confirms their email
├── css/style.css              Shared styles (fonts, palette, graph-paper bg)
├── js/site.js                 Renders experts/publications/commentary from JSON
├── data/
│   ├── experts.json           <- edit to add/remove an expert
│   ├── publications.json      <- edit to add/remove a report
│   └── posts.json             Auto-generated cache of Medium posts — don't hand-edit
├── scripts/fetch_medium.py    Pulls the Medium RSS feed into data/posts.json
├── .github/workflows/fetch-medium.yml   Runs the script on a daily schedule
├── publications/              PDF files live here
├── assets/                    Images (logo, tagline, expert headshots, placeholder)
├── logo.png, tagline.png      Existing brand assets (unchanged)
```

Look and feel — font (Helvetica), the blue/green/orange/red/purple accent
palette, and the graph-paper background — are all carried over exactly from
the current site's `index.html` into `css/style.css`, so every new page
matches automatically.

---

## 1. Hosting (free — GitHub Pages, same as today)

You're already on GitHub Pages, so there's nothing new to sign up for.

1. Replace the contents of the `CardinalInsights/splash` repo with these
   files (keep `logo.png` and `tagline.png` at the repo root, as they are
   now — the pages reference them there).
2. Commit and push to `main`.
3. In the repo: **Settings → Pages → Build and deployment → Source** should
   already be set to "Deploy from a branch" with branch `main` / root. If
   not, set it — this is free for public repos.
4. Your site is live at the same URL: `https://cardinalinsights.github.io/splash/`.

**Optional custom domain** (e.g. `cardinalinsights.co.uk`): add a `CNAME`
file at the repo root containing the domain, and add a `CNAME` DNS record
with your domain registrar pointing to `cardinalinsights.github.io`. Free —
GitHub Pages issues an HTTPS certificate automatically.

Housekeeping: the repo currently has several stray files (`backup.html`,
`bu2.html`, `bu3.html`, `index working.html`, `oldalternate.html`,
`taglineold.png`, `logo cap.png`). Worth deleting these once the new site is
live so `git clone` / Pages builds stay clean — none of the new pages
reference them.

---

## 2. Updating content (no code required)

All of these are plain-text edits via GitHub's web editor (pencil icon on
the file) or any text editor if you clone the repo. Save/commit and the
live site updates within a minute or two.

### Add or remove an expert
Edit `data/experts.json`. Each entry:
```json
{
  "id": "unique-slug",
  "name": "Full Name",
  "role": "Their title",
  "photo": "assets/experts/filename.jpg",
  "bio": "Two or three sentences."
}
```
Upload the headshot to `assets/experts/`. If a photo is missing or fails to
load, a neutral placeholder silhouette shows automatically so the page never
breaks. To remove someone, delete their JSON block.

*If you'd like a proper visual admin panel instead of editing JSON directly*
(useful if someone non-technical will maintain this), **Decap CMS** is a
free, open-source option that adds a `/admin` login screen backed by your
GitHub repo — form fields instead of raw JSON, image upload built in. Happy
to wire this up as a follow-up if useful.

### Add or remove a publication
Edit `data/publications.json`:
```json
{
  "id": "unique-slug",
  "title": "Report title",
  "date": "2026-06-01",
  "summary": "One or two sentence summary.",
  "pdf": "publications/filename.pdf",
  "formAction": "https://your-provider-form-url-for-this-report"
}
```
Upload the PDF to `publications/`. See section 4 below for what
`formAction` needs to point to.

### Blog / Commentary posts
Nothing to do — `commentary.html` reads `data/posts.json`, which a GitHub
Action refreshes daily from your Medium RSS feed
(`medium.com/feed/@cardinalinsights`). See section 5.

---

## 3. Newsletter signup (Beehiiv or Mailchimp — free tiers)

You mentioned an existing **Beehiiv** account and openness to Mailchimp.
Beehiiv's free plan supports up to 2,500 subscribers, so it comfortably
covers your >100-subscriber target; Mailchimp's free plan tops out at 500
contacts. **Beehiiv is the better fit given your numbers** — go with that
unless you have another reason to prefer Mailchimp.

Steps for Beehiiv:
1. In Beehiiv, go to **Subscribe Forms** and create an embed form (or use
   your publication's default subscribe page).
2. Copy the form's action URL and replace the placeholder in
   `index.html`'s `<form action="...">` (currently
   `https://cardinalinsights.beehiiv.com/subscribe`).
3. Test with your own email to confirm it lands in your Beehiiv audience.

Steps for Mailchimp instead: Audience → Signup forms → Embedded forms, copy
the generated form's `action` URL and field names into the same spot.

---

## 4. Publications page: verified-email-gated PDFs

Requirement: a visitor must **verify their email before** getting the PDF,
for free, with no backend server. The approach here uses your newsletter
provider's own **double opt-in** flow, so the "verification" is a real
confirmation email — not just a client-side check:

1. Visitor clicks "Get the report" → a small form appears → they enter
   their email and submit.
2. This submits to a **separate signup form/tag in Beehiiv, one per
   publication** (so Cardinal knows which report to unlock). Beehiiv lets
   you create multiple embed forms or tag subscribers per source.
3. Beehiiv sends its normal confirmation email (double opt-in).
4. In that specific form's settings, set the **post-confirmation redirect
   URL** to:
   `https://cardinalinsights.github.io/splash/publications-unlocked.html?doc=<publication-id>`
   (use the same `id` as in `publications.json`).
5. When the visitor clicks the confirmation link in their inbox, Beehiiv
   redirects them to that URL, `publications-unlocked.html` reads the
   `doc` parameter, looks up the matching entry in `publications.json`, and
   shows the **Download PDF** button — only reachable after a confirmed
   email.

**To add a new gated publication:** create a new Beehiiv form for it, set
its redirect URL as above, then add the corresponding entry (with that
form's action URL) to `data/publications.json`.

Caveat worth double-checking: whether the confirmation-redirect setting is
available on Beehiiv's free tier (Mailchimp's equivalent — Audience → Signup
forms → Form builder → "Confirmation thank you page" redirect — is on
Mailchimp's free plan for the basic non-advanced form; a JS-embedded form
needs "disable JavaScript" ticked for the redirect to fire). Worth a quick
check in your account before relying on it; if it turns out to be paid-tier
only, the fallback is a Google Form + Zapier/Make free-tier automation that
emails the link on confirmed submission — more moving parts, so try the
native route first.

---

## 5. Medium auto-pull ("Commentary" page)

`scripts/fetch_medium.py` fetches `https://medium.com/feed/@cardinalinsights`
and writes `data/posts.json` (title, link, date for each post). The GitHub
Action in `.github/workflows/fetch-medium.yml` runs this automatically once
a day and commits any changes — nothing to do once you start publishing on
Medium.

To trigger it manually (e.g. right after publishing a new post rather than
waiting for the daily run): go to the repo's **Actions** tab → "Fetch Medium
posts" → **Run workflow**.

Until your first Medium post goes live, `commentary.html` shows a friendly
"no posts yet" message with a link to your Medium profile — nothing breaks.

---

## 6. Resource summary (all free tiers)

| Need | Tool | Cost |
|---|---|---|
| Hosting | GitHub Pages | Free |
| Newsletter / list management | Beehiiv (up to 2,500 subs) | Free |
| Email verification for publications | Beehiiv double opt-in + redirect | Free |
| Blog | Medium (`@cardinalinsights`) | Free |
| Blog auto-sync | GitHub Actions (scheduled workflow) | Free (public repo) |
| Optional: friendlier admin UI for experts/publications | Decap CMS | Free |

No paid services are required for anything in this spec at your current
scale. If subscriber count grows well past Beehiiv's free tier or PDF
traffic gets heavy, that's the point to revisit — not before.

---

## 7. Responsiveness

The layout keeps the original two-column approach (fixed sidebar + content)
at ≥768px, and stacks to a single column below that, exactly as the current
site does. The experts grid additionally reflows from 1 → 2 → 3 columns as
width increases (mobile → tablet → desktop), and all forms and cards use
fluid widths so nothing overflows on small screens.
