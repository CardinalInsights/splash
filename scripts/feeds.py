"""
Shared helpers for the Cardinal Insights reading list: read sources.txt and
find each source's RSS/Atom feed.

A source's address can be a feed already, or a normal web page. For a web
page we look for the feed the site advertises in its HTML, then try the
usual addresses (/feed, /rss, ...).

An address written as  news:example.org  uses a Google News search of that
site instead, for sites with no feed or that block automated readers.
"""

import re
from pathlib import Path
from urllib.parse import urljoin

import feedparser
import requests

SOURCES_FILE = Path(__file__).resolve().parent.parent / "sources.txt"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CardinalReadingList/1.0)"}
COMMON_PATHS = ["feed", "feed/", "rss", "rss.xml", "feed.xml", "atom.xml", "index.xml", "rss/", "feeds/posts/default"]
TIMEOUT = 20


def read_sources(path=SOURCES_FILE):
    sources = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        name, url = (part.strip() for part in line.split("|", 1))
        if name and url:
            sources.append({"name": name, "url": url})
    return sources


def fetch(url):
    return requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)


def parse_feed(content):
    """Returns the parsed feed if `content` really is a feed with entries or a title."""
    parsed = feedparser.parse(content)
    if parsed.get("version") and (parsed.entries or parsed.feed.get("title")):
        return parsed
    return None


def advertised_feeds(html, base_url):
    """Feed links a page declares via <link rel="alternate" type="application/rss+xml">."""
    found = []
    for tag in re.findall(r"<link\b[^>]*>", html, flags=re.I):
        if not re.search(r'rel=["\']?alternate', tag, flags=re.I):
            continue
        if not re.search(r"type=[\"']?application/(rss|atom)\+xml", tag, flags=re.I):
            continue
        href = re.search(r'href=["\']([^"\']+)["\']', tag, flags=re.I)
        if href:
            found.append(urljoin(base_url, href.group(1).replace("&amp;", "&")))
    # Sites often list a comments feed too; prefer the main one.
    found.sort(key=lambda u: "comment" in u.lower())
    return found


def is_news_search(url):
    return url.lower().startswith("news:")


def news_search_feed(url):
    """`news:example.org` -> a Google News feed of recent pages from that site.

    For sites that have no feed of their own, or that refuse automated
    readers. Coverage is whatever Google News has indexed, and the feed
    carries headlines only (no article text).
    """
    domain = url.split(":", 1)[1].strip().replace("https://", "").replace("http://", "").strip("/")
    if domain.startswith("www."):
        domain = domain[4:]
    return f"https://news.google.com/rss/search?q=site:{domain}+when:7d&hl=en-GB&gl=GB&ceid=GB:en"


def resolve_feed(url):
    """Returns (feed_url, parsed_feed, note). feed_url is None if nothing worked."""
    if is_news_search(url):
        feed_url = news_search_feed(url)
        try:
            resp = fetch(feed_url)
        except requests.RequestException as e:
            return None, None, f"news search could not connect ({type(e).__name__})"
        parsed = parse_feed(resp.content) if resp.status_code < 400 else None
        if parsed:
            return feed_url, parsed, "news search feed"
        return None, None, f"news search answered {resp.status_code}"
    try:
        resp = fetch(url)
    except requests.RequestException as e:
        return None, None, f"could not connect ({type(e).__name__})"
    if resp.status_code >= 400:
        first_note = f"site answered {resp.status_code}"
    else:
        parsed = parse_feed(resp.content)
        if parsed:
            return resp.url, parsed, "address is a feed"
        first_note = "no feed found"
        for candidate in advertised_feeds(resp.text, resp.url):
            try:
                r = fetch(candidate)
                parsed = parse_feed(r.content) if r.ok else None
            except requests.RequestException:
                parsed = None
            if parsed:
                return candidate, parsed, "feed advertised by the site"

    base = url if url.endswith("/") else url + "/"
    for path in COMMON_PATHS:
        candidate = urljoin(base, path)
        try:
            r = fetch(candidate)
            parsed = parse_feed(r.content) if r.ok else None
        except requests.RequestException:
            parsed = None
        if parsed:
            return candidate, parsed, "feed found at a standard address"
    return None, None, first_note
