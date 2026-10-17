#!/usr/bin/env python3
"""Aggregate headlines from RSS/Atom feeds.

Writes:  news.json, news/index.html (crawlable static page), sitemap.xml
Stores only: title, source, link, date and a SHORT excerpt taken from the feed.
It never copies full article text. Every item links back to the original.
"""
import hashlib, html, json, re, sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://revenueinfotech.com"
MAX_ITEMS, MAX_PER_FEED, EXCERPT_CHARS = 60, 15, 240
UA = "RevenueInfoTechBot/1.0 (+https://revenueinfotech.com/contact.html)"
ATOM = "{http://www.w3.org/2005/Atom}"
TRACKING = ("utm_", "fbclid", "gclid", "ref", "source")


def clean(text, limit=None):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    if limit and len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "..."
    return text


def norm_url(url):
    p = urlparse(url.strip())
    q = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith(TRACKING)]
    return urlunparse((p.scheme, p.netloc.lower(), p.path.rstrip("/") or "/", "", urlencode(q), ""))


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def txt(el, *names):
    for n in names:
        found = el.find(n)
        if found is not None and (found.text or "").strip():
            return found.text
    return ""


def parse_feed(xml_bytes, source):
    root = ET.fromstring(xml_bytes)
    items = []
    for it in root.iter("item"):                      # RSS 2.0
        link = txt(it, "link")
        date = parse_date(txt(it, "pubDate", "{http://purl.org/dc/elements/1.1/}date"))
        items.append((txt(it, "title"), link, txt(it, "description"), date))
    for en in root.iter(ATOM + "entry"):              # Atom
        link = ""
        for l in en.findall(ATOM + "link"):
            if l.get("rel", "alternate") == "alternate" and l.get("href"):
                link = l.get("href")
                break
        date = parse_date(txt(en, ATOM + "published", ATOM + "updated"))
        items.append((txt(en, ATOM + "title"), link, txt(en, ATOM + "summary", ATOM + "content"), date))
    out = []
    for title, link, desc, date in items[:MAX_PER_FEED]:
        title, link = clean(title), (link or "").strip()
        if not title or not link.startswith(("http://", "https://")):
            continue
        url = norm_url(link)
        out.append({
            "id": hashlib.sha1(url.encode()).hexdigest()[:12],
            "title": title,
            "url": link,
            "source": source,
            "published": (date or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds"),
            "excerpt": clean(desc, EXCERPT_CHARS),
        })
    return out


def fetch(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, text/xml"})
    with urlopen(req, timeout=20) as r:
        return r.read()


def render_html(items):
    rows = []
    for i in items:
        d = i["published"][:10]
        rows.append(
            f'<article><p class="meta">{html.escape(i["source"])} &middot; <time datetime="{i["published"]}">{d}</time></p>'
            f'<h2><a href="{html.escape(i["url"], quote=True)}" rel="noopener" target="_blank">{html.escape(i["title"])}</a></h2>'
            f'<p>{html.escape(i["excerpt"])}</p></article>')
    now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Latest Technology News | RevenueInfoTech</title>
<meta name="description" content="Headlines and short summaries from leading technology publications and company newsrooms, updated hourly. Every item links to its original source.">
<link rel="canonical" href="{SITE}/news/">
<style>body{{font-family:Inter,system-ui,sans-serif;max-width:760px;margin:0 auto;padding:24px;color:#111827;line-height:1.55}}
a{{color:#2563EB}}article{{border-bottom:1px solid #e5e7eb;padding:14px 0}}h2{{font-size:1.1rem;margin:.2rem 0}}
.meta{{color:#6b7280;font-size:.8rem;margin:0}}header a{{font-weight:700;text-decoration:none}}</style></head>
<body><header><a href="/">&larr; RevenueInfoTech</a></header>
<h1>Latest Technology News</h1>
<p class="meta">Updated {now}. Summaries are brief excerpts supplied by each publisher's feed; click through to read the full story at the source.</p>
{chr(10).join(rows)}
<p class="meta"><a href="/contact.html">Contact</a> &middot; <a href="/privacy-policy.html">Privacy Policy</a></p>
</body></html>"""


def render_sitemap():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = ["/", "/news/", "/contact.html", "/privacy-policy.html"]
    body = "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n'


def main():
    cfg = json.loads((ROOT / "feeds.json").read_text())
    existing = []
    jp = ROOT / "news.json"
    if jp.exists():
        existing = json.loads(jp.read_text()).get("items", [])
    fresh, ok = [], 0
    for f in cfg["feeds"]:
        try:
            fresh += parse_feed(fetch(f["url"]), f["name"])
            ok += 1
            print(f"ok    {f['name']}")
        except Exception as e:
            print(f"FAIL  {f['name']}: {e}", file=sys.stderr)
    if ok == 0:
        sys.exit("No feed could be fetched; leaving existing files untouched.")
    merged = {i["id"]: i for i in existing}
    merged.update({i["id"]: i for i in fresh})
    items = sorted(merged.values(), key=lambda i: i["published"], reverse=True)[:MAX_ITEMS]
    jp.write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "items": items}, indent=2))
    (ROOT / "news").mkdir(exist_ok=True)
    (ROOT / "news" / "index.html").write_text(render_html(items))
    (ROOT / "sitemap.xml").write_text(render_sitemap())
    print(f"wrote {len(items)} items")


if __name__ == "__main__":
    main()
