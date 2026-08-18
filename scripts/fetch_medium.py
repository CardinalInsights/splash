#!/usr/bin/env python3
"""
Fetch the Cardinal Insights Medium RSS feed and write it to data/posts.json
in the simple shape commentary.html expects: [{ "title", "url", "date" }, ...]

Uses only the Python standard library so it runs on a plain GitHub Actions
runner with no pip install step.
"""
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

MEDIUM_HANDLE = "cardinalinsights"
FEED_URL = f"https://medium.com/feed/@{MEDIUM_HANDLE}"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "posts.json"


def fetch_feed(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; CardinalInsightsBot/1.0)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_query(url: str) -> str:
    return url.split("?")[0]


def parse_items(xml_text: str):
    root = ET.fromstring(xml_text)
    posts = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        if not title or not link:
            continue
        posts.append({
            "title": title,
            "url": strip_query(link),
            "date": pub_date,
        })
    return posts


def main():
    try:
        xml_text = fetch_feed(FEED_URL)
        posts = parse_items(xml_text)
    except Exception as exc:  # network hiccup, empty feed, etc.
        print(f"Warning: could not fetch/parse Medium feed: {exc}", file=sys.stderr)
        # Leave the existing posts.json untouched rather than wiping it.
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(posts, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(posts)} posts to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
