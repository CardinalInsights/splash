#!/usr/bin/env python3
"""
Cardinal Insights daily reading list.

Each run:
  1. Reads sources.txt and finds every source's RSS feed.
  2. Collects items that are new since the last run.
  3. Asks Claude (Haiku) which ones match your topics.
  4. Asks Claude for a ~50-word summary of each one kept.
  5. Writes data/reading/<date>.json for reading.html to display, and
     deletes days older than RETENTION_DAYS.

Topics come live from the Tags field in the Airtable archive when the
AIRTABLE_TOKEN secret is set, otherwise from topics.txt.

Required secret:  ANTHROPIC_API_KEY
Optional secret:  AIRTABLE_TOKEN  (needs the schema.bases:read scope)
"""

import datetime as dt
import html
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

from feeds import read_sources, resolve_feed

MODEL = "claude-haiku-4-5-20251001"
MAX_ITEMS_PER_DAY = 40        # most stories shown for one day
MAX_PER_SOURCE = 6            # stops one busy source filling the page
NEW_WINDOW_DAYS = 2           # how far back a dated item still counts as new
RETENTION_DAYS = 7            # days of reading lists kept on the site
SUMMARY_WORDS = 50
FILTER_BATCH = 40             # items per topic-filter request
SUMMARY_BATCH = 8             # items per summary request

AIRTABLE_BASE_ID = "appIGt0AfE0O7Da4c"
AIRTABLE_TABLE_ID = "tbliNdl6iyEOGlsez"

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "reading"
STATE_FILE = DATA_DIR / "state.json"      # feed addresses and links already seen
TOPICS_FILE = ROOT / "topics.txt"


# ---------- topics ----------

def load_topics():
    token = os.environ.get("AIRTABLE_TOKEN", "").strip()
    if token:
        try:
            resp = requests.get(
                f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables",
                headers={"Authorization": f"Bearer {token}"}, timeout=30,
            )
            resp.raise_for_status()
            for table in resp.json().get("tables", []):
                if table.get("id") != AIRTABLE_TABLE_ID:
                    continue
                for field in table.get("fields", []):
                    if field.get("name") == "Tags":
                        names = [c["name"] for c in field.get("options", {}).get("choices", [])]
                        if names:
                            print(f"Topics: {len(names)} read live from Airtable Tags.")
                            return names
        except Exception as e:  # fall back rather than fail the whole run
            print(f"Could not read Airtable tags ({type(e).__name__}); using topics.txt.")
    names = [l.strip() for l in TOPICS_FILE.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.strip().startswith("#")]
    print(f"Topics: {len(names)} read from topics.txt.")
    return names


# ---------- collecting new items ----------

def clean_text(raw, limit):
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", raw or "", flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text[:limit]


def entry_date(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return dt.datetime(*t[:6], tzinfo=dt.timezone.utc)
            except (TypeError, ValueError):
                pass
    return None


def entry_text(entry):
    body = ""
    content = entry.get("content")
    if content and isinstance(content, list):
        body = content[0].get("value", "")
    return body or entry.get("summary", "") or entry.get("description", "")


def strip_tracking(url):
    return re.sub(r"[?&](utm_[^=&]+|ref|rss|source)=[^&#]*", "", url).rstrip("?&")


def collect_new_items(sources, state, now):
    """Returns new items across all sources and updates `state` in place."""
    items, report = [], []
    cutoff = now - dt.timedelta(days=NEW_WINDOW_DAYS)
    for source in sources:
        name = source["name"]
        known = state["feeds"].get(name, {})
        feed_url, parsed = None, None
        if known.get("address") == source["url"] and known.get("feed"):
            feed_url, parsed, _ = resolve_feed(known["feed"])
        if not feed_url:
            feed_url, parsed, note = resolve_feed(source["url"])
        if not feed_url:
            report.append(f"NO FEED  {name}: {note}")
            continue
        state["feeds"][name] = {"address": source["url"], "feed": feed_url}

        first_time = name not in state["seen"]
        seen_list = list(state["seen"].get(name, []))   # oldest first
        seen = set(seen_list)
        fresh = []
        for entry in parsed.entries:
            link = strip_tracking((entry.get("link") or "").strip())
            title = clean_text(entry.get("title", ""), 300)
            if not link or not title:
                continue
            if link in seen:
                continue
            seen.add(link)
            seen_list.append(link)
            when = entry_date(entry)
            # Dated items must be recent. Undated ones only count once we have
            # seen this source before, so a first run can't dump its whole feed.
            if when:
                if when < cutoff:
                    continue
            elif first_time:
                continue
            fresh.append({
                "source": name,
                "title": title,
                "url": link,
                "date": when.date().isoformat() if when else "",
                "text": clean_text(entry_text(entry), 2500),
            })
        state["seen"][name] = seen_list[-600:]
        items.extend(fresh)
        report.append(f"{len(fresh):3d} new  {name}")
        time.sleep(0.3)
    print("\n".join(report))
    return items


# ---------- Claude ----------

def call_claude(prompt, max_tokens):
    last_error = None
    for attempt in range(3):
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={"model": MODEL, "max_tokens": max_tokens,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=120,
            )
            if resp.status_code in (429, 500, 502, 503, 529):
                raise RuntimeError(f"temporary API error {resp.status_code}")
            resp.raise_for_status()
            return "".join(b.get("text", "") for b in resp.json().get("content", []))
        except Exception as e:
            last_error = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Claude request failed after 3 tries: {last_error}")


def parse_json_array(text):
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("no JSON array in reply")
    return json.loads(text[start:end + 1])


def filter_by_topic(items, topics):
    """Adds 'score' (0-3) and 'tags' to each item; returns those scoring 2+."""
    topic_list = ", ".join(f'"{t}"' for t in topics)
    kept = []
    for start in range(0, len(items), FILTER_BATCH):
        batch = items[start:start + FILTER_BATCH]
        listing = "\n".join(
            f'{i}. [{it["source"]}] {it["title"]} :: {it["text"][:280]}' for i, it in enumerate(batch)
        )
        prompt = (
            "You are screening items for a UK research and advisory firm's daily reading list. "
            "The firm works on public safety, information integrity and AI policy.\n\n"
            f"Its topics are: {topic_list}.\n\n"
            "For each numbered item, decide how well it fits those topics:\n"
            "3 = squarely on topic and substantive (research, investigation, policy, significant news)\n"
            "2 = clearly relevant\n1 = loosely related\n0 = not relevant, or product/consumer/marketing news\n\n"
            "Reply with ONLY a JSON array, one object per item scoring 2 or 3, like "
            '[{"i": 0, "score": 3, "tags": ["AI Risks"]}]. '
            "Tags must be copied exactly from the topic list (1 to 3 per item). "
            "Leave out items scoring 0 or 1. If none qualify reply [].\n\n"
            f"Items:\n{listing}"
        )
        try:
            verdicts = parse_json_array(call_claude(prompt, 3000))
        except Exception as e:
            print(f"Topic filter failed for one batch of {len(batch)} ({e}); skipping it.")
            continue
        for v in verdicts:
            try:
                item = batch[int(v["i"])]
                score = int(v.get("score", 0))
            except (KeyError, ValueError, IndexError, TypeError):
                continue
            tags = [t for t in v.get("tags", []) if t in topics][:3]
            if score >= 2 and tags:
                item["score"], item["tags"] = score, tags
                kept.append(item)
    return kept


def choose_top(items):
    """Best-scoring first, capped per source and overall."""
    items.sort(key=lambda it: (-it["score"], it["source"]))
    per_source, chosen = {}, []
    for it in items:
        if per_source.get(it["source"], 0) >= MAX_PER_SOURCE:
            continue
        per_source[it["source"]] = per_source.get(it["source"], 0) + 1
        chosen.append(it)
        if len(chosen) >= MAX_ITEMS_PER_DAY:
            break
    return chosen


def summarise(items):
    for start in range(0, len(items), SUMMARY_BATCH):
        batch = items[start:start + SUMMARY_BATCH]
        listing = "\n\n".join(
            f'ITEM {i}\nSource: {it["source"]}\nTitle: {it["title"]}\nText: {it["text"] or "(no text supplied)"}'
            for i, it in enumerate(batch)
        )
        prompt = (
            f"Write a summary of about {SUMMARY_WORDS} words (never more than {SUMMARY_WORDS + 10}) for each item below, "
            "for an expert reader deciding whether to click through. Say what it found, claims or reports, "
            "plainly and specifically. Use ONLY the text supplied: do not add facts, figures or names that are "
            "not there. If the text is too thin to summarise, describe what the item covers based on its title. "
            "British spelling. No preamble such as 'This article'.\n\n"
            'Reply with ONLY a JSON array like [{"i": 0, "summary": "..."}].\n\n'
            f"{listing}"
        )
        try:
            for s in parse_json_array(call_claude(prompt, 2500)):
                try:
                    batch[int(s["i"])]["summary"] = str(s.get("summary", "")).strip()
                except (KeyError, ValueError, IndexError, TypeError):
                    continue
        except Exception as e:
            print(f"Summaries failed for one batch of {len(batch)} ({e}); using feed text instead.")
        for it in batch:
            if not it.get("summary"):
                words = it["text"].split()
                it["summary"] = " ".join(words[:SUMMARY_WORDS]) + ("…" if len(words) > SUMMARY_WORDS else "")


# ---------- output ----------

def write_day(date_str, entries, topics, now):
    payload = {
        "date": date_str,
        "generated_at": now.isoformat(timespec="seconds"),
        "topics": topics,
        "entries": [
            {k: it[k] for k in ("title", "url", "source", "date", "summary", "tags")} for it in entries
        ],
    }
    (DATA_DIR / f"{date_str}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rebuild_index(today):
    cutoff = today - dt.timedelta(days=RETENTION_DAYS)
    dates = []
    for path in DATA_DIR.glob("????-??-??.json"):
        try:
            d = dt.date.fromisoformat(path.stem)
        except ValueError:
            continue
        if d < cutoff:
            path.unlink()
        else:
            dates.append(path.stem)
    dates.sort(reverse=True)
    (DATA_DIR / "index.json").write_text(json.dumps({"days": dates}, indent=2) + "\n", encoding="utf-8")
    return dates


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: the ANTHROPIC_API_KEY secret is not set.")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    date_str = now.date().isoformat()

    state = {"feeds": {}, "seen": {}}
    if STATE_FILE.exists():
        try:
            state.update(json.loads(STATE_FILE.read_text(encoding="utf-8")))
        except ValueError:
            print("state.json was unreadable; starting fresh.")

    topics = load_topics()
    sources = read_sources()
    items = collect_new_items(sources, state, now)
    print(f"\n{len(items)} new item(s) from {len(sources)} source(s).")

    relevant = filter_by_topic(items, topics) if items else []
    chosen = choose_top(relevant)
    print(f"{len(relevant)} matched your topics; keeping {len(chosen)}.")
    if chosen:
        summarise(chosen)

    # If today's list already exists (a second run the same day), add to it.
    day_file = DATA_DIR / f"{date_str}.json"
    if day_file.exists():
        try:
            earlier = json.loads(day_file.read_text(encoding="utf-8")).get("entries", [])
            have = {e["url"] for e in chosen}
            chosen = chosen + [e for e in earlier if e["url"] not in have]
        except ValueError:
            pass
    write_day(date_str, chosen, topics, now)
    STATE_FILE.write_text(json.dumps(state) + "\n", encoding="utf-8")
    days = rebuild_index(now.date())
    print(f"Wrote {len(chosen)} entries for {date_str}; {len(days)} day(s) on the site.")


if __name__ == "__main__":
    main()
