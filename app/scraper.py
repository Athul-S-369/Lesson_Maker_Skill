"""Web scraping on top of Scrapling (https://github.com/D4Vinci/Scrapling), with a plain-httpx fallback.

* fetch_page(url): SSRF-guarded fetch (manual redirects, every hop re-checked) with browser-like TLS/headers,
  then structure-aware extraction of the main content (headings, paragraphs, lists, code) instead of a
  tag-stripped dump of the whole page.
* bing_search / wikipedia_search: keyless extra sources, so research no longer depends on a single API.

If Scrapling is not installed everything still works through the old regex extractor (AVAILABLE is False).
Optional JS rendering (SCRAPER_BROWSER=1 and `scrapling install`) is used only when a page yields almost no text.
"""
import base64
import html
import os
import re
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

import httpx

from . import retrieval

try:
    from scrapling.fetchers import Fetcher
    AVAILABLE = True
except Exception:  # noqa: BLE001 - missing package or missing optional deps: fall back to httpx
    Fetcher = None
    AVAILABLE = False

MAX_BODY = 1_000_000          # httpx fallback: bytes read per page
MAX_PAGE_BYTES = 6_000_000    # Scrapling path: pages larger than this are skipped (RFC 9110 is 1.2 MB)
MAX_REDIRECTS = 4
TEXT_CAP = 120_000            # default stored text per page (relevance-trimmed when the page is longer)
PAGE_TEXT_CAP = 700_000       # extracted before trimming; RFC 9110 is about 450k characters
MIN_USEFUL_CHARS = 400
NOISE = "script,style,noscript,svg,nav,footer,header,aside,form,iframe,button"
BLOCKS = "h1,h2,h3,h4,p,li,pre,blockquote,td,th,dd,dt"
MAIN_CANDIDATES = ("main", "article", "[role=main]", "#content", "#main-content", ".post-content", ".markdown-body")
UA = "KalviumLessonTool/2.0 (research prototype)"


def _public(url: str) -> bool:
    from . import research  # late import: research imports this module
    return research.is_public_http_url(url)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


# ---------------- extraction ----------------
def _meta(page, selector: str) -> str:
    found = page.css(selector)
    return found[0].attrib.get("content", "") if found else ""


def extract_text(page) -> dict:
    """Main-content extraction from a Scrapling page: {title, description, published, text}."""
    t = page.css("title")
    h1 = page.css("h1")
    title = _clean(t[0].get_all_text()) if t else (_clean(h1[0].get_all_text()) if h1 else "")
    description = _clean(_meta(page, 'meta[name="description"]') or _meta(page, 'meta[property="og:description"]'))
    published = (_meta(page, 'meta[property="article:published_time"]') or _meta(page, 'meta[name="date"]'))[:10]
    noise_texts = {_clean(el.get_all_text()) for el in page.css(NOISE)}
    body = page.css("body")
    root = body[0] if body else page
    total = len(root.get_all_text()) or 1
    best, best_len = None, 0
    for sel in MAIN_CANDIDATES:
        c = page.css(sel)
        n = len(c[0].get_all_text()) if c else 0
        # semantic elements (<main>, role=main) are trusted from 15% of the page (mega-menus inflate the rest);
        # generic ids/classes must hold half of it, so a small widget can never win
        need = 0.15 if sel in ("main", "[role=main]") else 0.5
        if n > MIN_USEFUL_CHARS and n >= need * total and n > best_len:
            best, best_len = c[0], n
    container = best if best is not None else root
    lines, seen = [], set()
    for el in container.css(BLOCKS):
        if el.tag in ("li", "blockquote", "td", "th", "dd", "dt") and el.css("p,pre,ul,ol,table"):
            continue                                    # a wrapper of other blocks: its children are visited on their own
        txt = _clean(el.get_all_text())
        if len(txt) < 3 or txt in seen or txt in noise_texts:
            continue
        seen.add(txt)
        if len(el.tag) == 2 and el.tag[0] == "h":
            lines.append(f"{txt}.")
        elif el.tag == "pre":
            lines.append(txt)                           # code blocks, and plain-text documents such as RFCs, kept whole
        else:
            lines.append(txt if txt[-1] in ".!?:;)" else txt + ".")
    text = " ".join(lines).strip()
    if len(text) < MIN_USEFUL_CHARS:                    # unusual markup: use everything visible in the container
        text = _clean(container.get_all_text())
    return {"title": title, "description": description, "published": published, "text": text[:PAGE_TEXT_CAP]}


def _regex_text(body: str) -> str:
    t = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer|header)\b.*?</\1>", " ", body)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return _clean(html.unescape(t))[:PAGE_TEXT_CAP]


# ---------------- fetching ----------------
def _get(url: str):
    return Fetcher.get(url, stealthy_headers=True, impersonate="chrome", timeout=12, follow_redirects=False,
                       retries=1, retry_delay=1)


def _fit(out: dict | None, query: str, cap: int | None) -> dict | None:
    """Keep `text` within `cap` characters. A long page (an RFC, a spec) is cut down to the passages that match `query`
    (plus its opening), not to its first `cap` characters, so the part the lesson needs is never lost to truncation."""
    cap = cap or TEXT_CAP
    if out and len(out["text"]) > cap:
        out["text_chars_total"] = len(out["text"])
        out["text"] = retrieval.excerpt(out["text"], query, budget=cap, size=1500) if query else out["text"][:cap]
    return out


def fetch_page(url: str, query: str = "", cap: int | None = None) -> dict | None:
    """Fetch and extract one page. Returns {title, description, published, text, engine} or None.
    `query` (lesson title and objective) decides which passages survive when the page is longer than `cap`."""
    try:
        for _ in range(MAX_REDIRECTS + 1):
            if not _public(url):
                return None
            if AVAILABLE:
                r = _get(url)
                status, headers, body = r.status, r.headers, r
            else:
                with httpx.stream("GET", url, timeout=12, follow_redirects=False, headers={"User-Agent": UA}) as h:
                    status, headers = h.status_code, h.headers
                    raw = b""
                    for chunk in h.iter_bytes():
                        raw += chunk
                        if len(raw) > MAX_BODY:
                            break
                    body = raw[:MAX_BODY].decode(h.encoding or "utf-8", errors="replace")
            if status in (301, 302, 303, 307, 308):
                url = urljoin(url, headers.get("location", ""))
                continue
            ctype = headers.get("content-type", "")
            if status != 200 or ("html" not in ctype and "text" not in ctype):
                return None
            if AVAILABLE:
                if len(getattr(body, "body", b"") or b"") > MAX_PAGE_BYTES:
                    return None                              # refuse to parse enormous pages (the 12s timeout bounds the download)
                out = extract_text(body)
                out["engine"] = "scrapling"
                if len(out["text"]) < MIN_USEFUL_CHARS and os.getenv("SCRAPER_BROWSER") == "1":
                    out = _browser_fetch(url) or out
                return _fit(out, query, cap) if out["text"] else None
            text = _regex_text(body)
            return _fit({"title": "", "description": "", "published": "", "text": text, "engine": "httpx"}, query, cap) if text else None
        return None
    except Exception:  # noqa: BLE001 - any scrape problem just means "snippet only"
        return None


def _browser_fetch(url: str) -> dict | None:  # pragma: no cover - needs `scrapling install` (browsers)
    try:
        from scrapling.fetchers import DynamicFetcher
        out = extract_text(DynamicFetcher.fetch(url, headless=True, network_idle=True, timeout=20000))
        out["engine"] = "scrapling-browser"
        return out
    except Exception:  # noqa: BLE001
        return None


# ---------------- keyless search sources ----------------
def _bing_target(href: str) -> str:
    """Bing wraps result links as bing.com/ck/a?...&u=a1<base64url(target)>."""
    q = parse_qs(urlparse(href).query)
    u = (q.get("u") or [""])[0]
    if u.startswith("a1"):
        try:
            raw = u[2:]
            return base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode("utf-8", "replace")
        except (ValueError, UnicodeError):
            return ""
    return href


def parse_bing(page) -> list[dict]:
    out = []
    for res in page.css("li.b_algo"):
        a = res.css("h2 a")
        if not a:
            continue
        url = _bing_target(a[0].attrib.get("href", ""))
        sn = res.css(".b_caption p") or res.css("p")
        if re.match(r"https?://", url) and "bing.com" not in urlparse(url).netloc:
            out.append({"type": "web", "title": _clean(a[0].get_all_text()) or url, "url": url,
                        "snippet": _clean(sn[0].get_all_text())[:500] if sn else "", "published": None, "engine_score": 0})
    return out


def bing_search(query: str) -> list[dict]:
    """Keyless web search (HTML scrape). Best-effort: raises httpx.HTTPError when blocked or unavailable."""
    if not AVAILABLE:
        return []
    r = Fetcher.get(f"https://www.bing.com/search?q={quote_plus(query)}&mkt=en-US&cc=US&setlang=en-US", stealthy_headers=True,
                    impersonate="chrome", timeout=15, retries=1)
    if r.status != 200:
        raise httpx.HTTPError(f"Bing returned HTTP {r.status}")
    return parse_bing(r)[:8]


def _json_get(url: str, params: dict) -> dict:
    """JSON GET through Scrapling's browser-like client (some APIs reject plain scripted clients), httpx otherwise."""
    if AVAILABLE:
        r = Fetcher.get(url, params=params, stealthy_headers=True, impersonate="chrome", timeout=15, retries=1)
        if r.status != 200:
            raise httpx.HTTPError(f"HTTP {r.status} from {urlparse(url).netloc}")
        return r.json()
    r = httpx.get(url, params=params, timeout=15, headers={"User-Agent": UA})
    r.raise_for_status()
    return r.json()


def wikipedia_search(query: str) -> list[dict]:
    data = _json_get("https://en.wikipedia.org/w/api.php",
                     {"action": "query", "list": "search", "srsearch": query, "srlimit": 3, "format": "json"})
    out = []
    for x in data.get("query", {}).get("search", []):
        title = x.get("title", "")
        if title:
            out.append({"type": "web", "title": f"{title} - Wikipedia",
                        "url": "https://en.wikipedia.org/wiki/" + quote_plus(title.replace(" ", "_"), safe="_()"),
                        "snippet": _clean(html.unescape(re.sub(r"<[^>]+>", "", x.get("snippet", ""))))[:500],
                        "published": None, "engine_score": 0})
    return out


# ---------------- command line (used by the research agents) ----------------
def main(argv: list[str]) -> int:
    """python -m app.scraper fetch <url> [--max N] [--query "<topic>"] | search "<query>" | wiki "<query>"  -> JSON on stdout.
    With --query, a page longer than --max keeps the passages that match the query instead of its first N characters."""
    import json
    if len(argv) < 2 or argv[0] not in ("fetch", "search", "wiki"):
        print(main.__doc__)
        return 2
    cmd, arg = argv[0], argv[1]
    try:
        if cmd == "fetch":
            cap = int(argv[argv.index("--max") + 1]) if "--max" in argv else TEXT_CAP
            query = argv[argv.index("--query") + 1] if "--query" in argv else ""
            page = fetch_page(arg, query, cap)
            out = ({"url": arg, "ok": True, **{**page, "chars": len(page["text"])}} if page
                   else {"url": arg, "ok": False, "error": "could not fetch or extract (blocked, non-HTML, private address or empty)"})
        elif cmd == "search":
            out = {"query": arg, "results": bing_search(arg)}
        else:
            out = {"query": arg, "results": wikipedia_search(arg)}
    except Exception as e:  # noqa: BLE001 - the agent needs a readable error, not a traceback
        out = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out.get("ok", True) else 1


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main(_sys.argv[1:]))
