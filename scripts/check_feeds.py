"""
Checks every source in sources.txt and reports which have a working feed.

Run it after editing sources.txt (the "Check Reading List Feeds" action does
this). It writes feeds_report.md: working sources with their newest item,
then the ones that need attention.
"""

import time

from feeds import read_sources, resolve_feed


def newest(parsed):
    if not parsed.entries:
        return "(feed is empty)", ""
    e = parsed.entries[0]
    when = e.get("published") or e.get("updated") or ""
    return (e.get("title") or "(untitled)").strip()[:90], when[:25]


def main():
    sources = read_sources()
    working, failed = [], []
    for s in sources:
        feed_url, parsed, note = resolve_feed(s["url"])
        if feed_url:
            title, when = newest(parsed)
            working.append((s["name"], feed_url, len(parsed.entries), title, when))
            print(f"OK    {s['name']}: {feed_url}")
        else:
            failed.append((s["name"], s["url"], note))
            print(f"FAIL  {s['name']}: {note}")
        time.sleep(0.5)

    lines = [f"# Reading list feed check", "", f"{len(working)} of {len(sources)} sources have a working feed.", ""]
    lines += ["## Need attention", ""]
    lines += [f"- **{n}** ({u}): {note}" for n, u, note in failed] or ["None."]
    lines += ["", "## Working", "", "| Source | Feed | Items | Newest item | Date |", "|---|---|---|---|---|"]
    lines += [f"| {n} | {f} | {c} | {t.replace('|', '/')} | {w} |" for n, f, c, t, w in working]
    with open("feeds_report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\n{len(working)} working, {len(failed)} need attention. See feeds_report.md.")


if __name__ == "__main__":
    main()
