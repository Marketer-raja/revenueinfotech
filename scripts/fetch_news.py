#!/usr/bin/env python3
"""Collect technology-news candidates from RSS/Atom feeds for human review.

Writes news.json (the unpublished editorial review queue) and a noindex /news/
source directory. It never writes home-news.json: the homepage is changed only
when an editor reviews and publishes selected items through /newsdesk/.
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
MAX_ITEMS, MAX_PER_FEED, EXCERPT_CHARS = 40, 12, 240
MEDIA = "{http://search.yahoo.com/mrss/}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"
# Home page slots: hero (1), Editor's briefs (3), latest list (6), featured cards (6)
SLOTS = [("hero", 1), ("brief", 3), ("latest", 6), ("featured", 6)]

# Category -> keywords. A story must match at least one tech keyword to be kept.
CATEGORIES = {
    "Artificial Intelligence": ["ai", "artificial intelligence", "machine learning", "llm", "chatgpt", "openai",
        "gemini", "claude", "anthropic", "neural", "deepseek", "copilot", "nvidia", "gpu", "chatbot", "generative", "deep learning"],
    "Cybersecurity": ["security", "hack", "hacker", "breach", "malware", "ransomware", "vulnerability", "exploit",
        "phishing", "cyber", "zero-day", "cve", "encryption", "spyware", "botnet", "patch"],
    "Cloud Computing": ["cloud", "aws", "azure", "google cloud", "data center", "datacenter", "kubernetes", "serverless", "server"],
    "Software Development": ["developer", "programming", "github", "open source", "open-source", "python", "javascript",
        "rust", "api", "flaw", "flaws", "rce", "tls", "nginx", "winrar", "sdk", "code", "coding", "software", "compiler", "devops"],
    "Operating Systems": ["windows", "macos", "linux", "android", "ios", "ipados", "chromeos", "kernel", "firmware", "operating system"],
    "Enterprise Software & SaaS": ["saas", "enterprise", "microsoft", "salesforce", "oracle", "sap", "startup", "funding", "ibm"],
    "Data & Analytics": ["data", "database", "analytics", "sql", "big data", "privacy"],
    "Web Development": ["browser", "chrome", "firefox", "safari", "web", "html", "css", "website", "wordpress"],
}
EXTRA_TECH = ["tech", "technology", "apple", "iphone", "ipad", "mac", "google", "pixel", "samsung", "galaxy", "smartphone",
    "phone", "laptop", "pc", "chip", "processor", "semiconductor", "intel", "amd", "qualcomm", "arm", "tesla", "ev",
    "robot", "robotics", "drone", "app", "apps", "gadget", "wearable", "headphones", "vr", "ar", "quantum", "5g",
    "broadband", "internet", "meta", "amazon", "alexa", "spacex", "starlink", "satellite", "gaming", "console", "xbox",
    "playstation", "nintendo", "steam", "camera", "tablet", "smartwatch", "display", "oled", "battery", "usb", "wifi",
    "rsa", "ram", "memory", "vmware", "ethernet", "wi fi", "router", "network", "networking", "waymo", "robotaxi", "mcp", "agent", "agents", "protocol", "projector", "smart tv", "tv", "hard drive", "ssd", "storage", "homepod", "nest", "doorbell", "googlebook", "chromebook", "smart home", "solar", "streaming", "netflix", "youtube", "crypto", "blockchain", "bitcoin", "software", "hardware", "device", "digital", "computer", "computing"]
# Stories mainly about these topics are dropped even if a feed publishes them.
NON_TECH = ["recipe", "celebrity", "horoscope", "election", "senator", "football", "nba", "nfl", "soccer",
    "movie review", "box office", "fashion", "royal family", "deal of the day", "best deals", "coupon", "sale:", "% off", "coupon", "promo code", "gifts for", "trump", "lawsuit over", "documentary", "hair", "grow lights", "cat feeder"]
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


def words(text):
    return " " + re.sub(r"[^a-z0-9+#]+", " ", text.lower()) + " "


def has(blob, kw):
    return (" " + kw + " ") in blob


def categorize(title, desc):
    """Return a tech category, or None if the story is not about technology."""
    t, d = words(title), words(desc)
    if any(k in t for k in NON_TECH):
        return None
    best, score = None, 0
    for cat, kws in CATEGORIES.items():
        sc = sum(3 for k in kws if has(t, k)) + sum(1 for k in kws if has(d, k))
        if sc > score:
            best, score = cat, sc
    extra = sum(2 for k in EXTRA_TECH if has(t, k)) + sum(1 for k in EXTRA_TECH if has(d, k))
    if score + extra < 1:          # not enough tech signal -> drop
        return None
    return best or "Software Development"


def find_image(el, desc_html):
    for tag in (MEDIA + "content", MEDIA + "thumbnail"):
        for m in el.iter(tag):
            u = m.get("url", "")
            if u.startswith("http") and (m.get("medium") in (None, "image") or re.search(r"\.(jpe?g|png|webp|gif)", u, re.I)):
                return u
    for enc in el.findall("enclosure") + el.findall(ATOM + "link"):
        if (enc.get("type") or "").startswith("image") and (enc.get("url") or enc.get("href")):
            return enc.get("url") or enc.get("href")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', desc_html or "")
    return html.unescape(m.group(1)) if m and m.group(1).startswith("http") else ""


def og_image(url):
    """Fallback: read the article's og:image (only the page head is read)."""
    try:
        req = Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
        with urlopen(req, timeout=10) as r:
            head = r.read(200_000).decode("utf-8", "ignore")
        m = re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)', head, re.I) \
            or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image)', head, re.I)
        u = html.unescape(m.group(1)) if m else ""
        return u if u.startswith("http") else ""
    except Exception:
        return ""


def parse_feed(xml_bytes, source):
    root = ET.fromstring(xml_bytes)
    items = []
    for it in root.iter("item"):                      # RSS 2.0
        link = txt(it, "link")
        date = parse_date(txt(it, "pubDate", "{http://purl.org/dc/elements/1.1/}date"))
        d = txt(it, "description", CONTENT + "encoded")
        items.append((txt(it, "title"), link, d, date, find_image(it, txt(it, CONTENT + "encoded") or d)))
    for en in root.iter(ATOM + "entry"):              # Atom
        link = ""
        for l in en.findall(ATOM + "link"):
            if l.get("rel", "alternate") == "alternate" and l.get("href"):
                link = l.get("href")
                break
        date = parse_date(txt(en, ATOM + "published", ATOM + "updated"))
        d = txt(en, ATOM + "summary", ATOM + "content")
        items.append((txt(en, ATOM + "title"), link, d, date, find_image(en, txt(en, ATOM + "content") or d)))
    out = []
    for title, link, desc, date, image in items[:MAX_PER_FEED]:
        title, link = clean(title), (link or "").strip()
        if not title or not link.startswith(("http://", "https://")):
            continue
        category = categorize(title, clean(desc))
        if not category:
            print(f"  skip (not tech): {title[:70]}")
            continue
        url = norm_url(link)
        out.append({
            "id": hashlib.sha1(url.encode()).hexdigest()[:12],
            "title": title,
            "url": link,
            "source": source,
            "published": (date or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds"),
            "excerpt": clean(desc, EXCERPT_CHARS),
            "image": image,
            "category": category,
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
            f'<article><p class="meta">{html.escape(i["source"])} &middot; <time datetime="{i["published"]}">{d}</time></p>' +
            (f'<img src="{html.escape(i["image"], quote=True)}" alt="" loading="lazy">' if i.get("image") else "") +
            f'<h2><a href="{html.escape(i["url"], quote=True)}" rel="noopener" target="_blank">{html.escape(i["title"])}</a></h2>'
            f'<p>{html.escape(i["excerpt"])}</p></article>')
    now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Latest Technology News | RevenueInfoTech</title>
<meta name="description" content="A source directory of technology-news leads reviewed by RevenueInfoTech editors.">
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{SITE}/news/">
<style>body{{font-family:Inter,system-ui,sans-serif;max-width:760px;margin:0 auto;padding:24px;color:#111827;line-height:1.55}}
a{{color:#2563EB}}article{{border-bottom:1px solid #e5e7eb;padding:14px 0}}h2{{font-size:1.1rem;margin:.2rem 0}}
article img{{width:100%;max-height:320px;object-fit:cover;border-radius:6px}}.meta{{color:#6b7280;font-size:.8rem;margin:0}}header a{{font-weight:700;text-decoration:none}}</style></head>
<body><header><a href="/">&larr; RevenueInfoTech</a></header>
<h1>Latest Technology News</h1>
<p class="meta">Editorial research queue · Updated {now}. These publisher-supplied feed excerpts are leads for editorial review, not original RevenueInfoTech reporting. For full reporting, visit the linked publisher.</p>
{chr(10).join(rows)}
<p class="meta"><a href="/contact.html">Contact</a> &middot; <a href="/privacy-policy.html">Privacy Policy</a></p>
</body></html>"""


def render_sitemap():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Public editorial and policy pages only. /news/ and /newsdesk/ are excluded because they are not original articles/admin pages.
    # Update the static lastmod dates below when you edit those pages.
    urls = [
        ("/",                        today,        "daily",   "1.0"),
        ("/about.html",              today,        "yearly",  "0.5"),
        ("/editorial-ethics.html",   "2026-10-18", "yearly",  "0.5"),
        ("/peer-review-process.html","2026-10-18", "yearly",  "0.5"),
        ("/sponsorship-disclosure.html","2026-10-18","yearly","0.4"),
        ("/contact.html",            "2026-10-18", "yearly",  "0.4"),
        ("/privacy-policy.html",     "2026-10-18", "yearly",  "0.3"),
        ("/terms-of-service.html",   "2026-10-18", "yearly",  "0.3"),
    ]
    body = "".join(
        f"\n  <url>\n    <loc>{SITE}{u}</loc>\n    <lastmod>{m}</lastmod>\n"
        f"    <changefreq>{c}</changefreq>\n    <priority>{pr}</priority>\n  </url>"
        for u, m, c, pr in urls
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}\n</urlset>\n')


def build_home(items):
    """Fill the home page automatically: newest stories with pictures go in the visible slots."""
    with_img = [i for i in items if i.get("image")]
    without = [i for i in items if not i.get("image")]
    ordered, out, pos = with_img + without, [], 0
    used_sources = {}
    for section, n in SLOTS:
        for _ in range(n):
            if pos >= len(ordered):
                break
            out.append((ordered[pos], section)); pos += 1
    out += [(i, "none") for i in ordered[pos:]]
    home = []
    for i, sec in out:
        home.append({"id": i["id"], "title": i["title"], "summary": i["excerpt"] or i["title"],
                     "source": i["source"], "url": i["url"], "image": i.get("image", ""),
                     "category": i.get("category", "Software Development"), "section": sec,
                     "featured": sec == "hero", "published": i["published"]})
    # keep newest-first order inside each section
    return sorted(home, key=lambda h: h["published"], reverse=True)


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
    # re-check old items too, so nothing non-tech survives from earlier runs
    existing = [i for i in existing if i.get("category") or categorize(i.get("title", ""), i.get("excerpt", ""))]
    for i in existing:
        i.setdefault("category", categorize(i.get("title", ""), i.get("excerpt", "")))
    merged = {i["id"]: i for i in existing}
    merged.update({i["id"]: i for i in fresh})
    items = sorted(merged.values(), key=lambda i: i["published"], reverse=True)[:MAX_ITEMS]
    for i in items[:40]:                      # fetch a picture for stories whose feed had none
        if not i.get("image"):
            i["image"] = og_image(i["url"])
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    jp.write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "items": items}, indent=2))
    (ROOT / "news").mkdir(exist_ok=True)
    (ROOT / "news" / "index.html").write_text(render_html(items))
    print(f"wrote {len(items)} candidate items to news.json; homepage content was left unchanged for manual approval")


if __name__ == "__main__":
    main()
