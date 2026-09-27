#!/usr/bin/env python3
"""Discover property candidates from public search results.

Discovery is deliberately conservative: it adds only candidate records with an
exact source URL, title and/or price evidence. Candidates are marked as
`needs_verification` and never promoted to verified facts automatically.
"""
from __future__ import annotations
import hashlib, html, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PROPERTIES = ROOT / "properties.json"
DISCOVERY = ROOT / "data" / "discovery_history.json"
TIMEOUT = 20
UA = "HouseTracker/1.0 (personal property discovery)"
MAX_RESULTS_PER_QUERY = 8
MAX_NEW_CANDIDATES_PER_RUN = 50

AREAS = [
    "Walsall", "Brownhills", "Pelsall", "Walsall Wood", "Willenhall",
    "Wednesbury", "Wolverhampton", "Bilston", "Tipton", "Coseley",
    "Cannock", "Great Wyrley", "Cheslyn Hay", "Rugeley", "Stafford", "Telford"
]
PORTALS = {
    "rightmove": "rightmove.co.uk",
    "zoopla": "zoopla.co.uk",
    "onthemarket": "onthemarket.com",
}


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "en-GB,en;q=0.9"})
    with urlopen(req, timeout=TIMEOUT) as r:
        return r.read(900_000).decode("utf-8", errors="ignore")


def search(query: str) -> str:
    # DuckDuckGo's public HTML endpoint is used only as a discovery index; the
    # resulting property pages remain the source of truth.
    return fetch("https://html.duckduckgo.com/html/?q=" + quote(query))


def extract_results(body: str):
    out = []
    # DDG result anchors generally use result__a. Keep extraction conservative.
    for m in re.finditer(r'<a[^>]+class=["\'][^"\']*result__a[^"\']*["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', body, re.I | re.S):
        url = html.unescape(m.group(1))
        title = re.sub(r"<[^>]+>", " ", m.group(2))
        title = html.unescape(re.sub(r"\s+", " ", title)).strip()
        if any(domain in url for domain in PORTALS.values()):
            out.append((url, title))
        if len(out) >= MAX_RESULTS_PER_QUERY:
            break
    return out


def normalise_url(url: str):
    # Drop search/ref parameters where possible; keep the property path intact.
    p = urlparse(url)
    if not p.scheme or not p.netloc:
        return None
    return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")


def extract_price(text: str):
    vals = re.findall(r"£\s?([0-9]{2,3}(?:,[0-9]{3})+|[0-9]{5,6})", text)
    nums = []
    for v in vals:
        n = int(v.replace(",", ""))
        if 150000 <= n <= 350000:
            nums.append(n)
    return nums[0] if nums else None


def make_id(url: str):
    return "cand-" + hashlib.sha1(url.encode()).hexdigest()[:12]


def main():
    properties = json.loads(PROPERTIES.read_text(encoding="utf-8"))
    existing = {normalise_url(x.get("link", "")) for x in properties if x.get("link")}
    candidates = []
    queries = []
    for area in AREAS:
        for portal, domain in PORTALS.items():
            queries.append(f"site:{domain} {area} 3 bedroom detached 2 bathroom £350,000")
            queries.append(f"site:{domain} {area} new build 3 bedroom house £350,000")

    seen = set()
    successful_queries = 0
    failed_queries = 0
    for query in queries:
        try:
            body = search(query)
            results = extract_results(body)
            successful_queries += 1
        except Exception as exc:
            failed_queries += 1
            print(f"Discovery query failed: {query}: {exc}")
            continue
        for raw_url, result_title in results:
            if len(candidates) >= MAX_NEW_CANDIDATES_PER_RUN:
                break
            url = normalise_url(raw_url)
            if not url or url in existing or url in seen:
                continue
            seen.add(url)
            if len(candidates) >= MAX_NEW_CANDIDATES_PER_RUN:
                break
            candidates.append({
                "id": make_id(url),
                "title": result_title[:240],
                "link": url,
                "status": "candidate",
                "verification": "needs_verification",
                "source": "public_search_discovery",
                "discoveredAt": datetime.now(timezone.utc).isoformat(),
                "discoveryQuery": query,
                "notes": "Candidate discovered by search index. Verify exact listing, price, beds/baths, garden, parking, tenure and availability before treating as a match.",
            })

    # If every query failed, preserve the previous candidate set and avoid treating
    # a transient search outage as an empty discovery result.
    if successful_queries == 0 and queries:
        history = json.loads(DISCOVERY.read_text(encoding="utf-8")) if DISCOVERY.exists() else {"runs": [], "candidates": []}
        now = datetime.now(timezone.utc).isoformat()
        history.setdefault("runs", []).insert(0, {"timestamp": now, "queries": len(queries), "successfulQueries": 0, "failedQueries": failed_queries, "newCandidates": 0, "status": "failed_preserved_previous_data"})
        history["runs"] = history["runs"][:20]
        history["lastRun"] = now
        DISCOVERY.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"queries": len(queries), "successfulQueries": 0, "failedQueries": failed_queries, "newCandidates": 0, "status": "failed_preserved_previous_data"}, indent=2))
        return

    # Keep discovery separate from manually verified properties. The UI can show
    # candidates as a review queue without polluting the trusted property list.
    history = json.loads(DISCOVERY.read_text(encoding="utf-8")) if DISCOVERY.exists() else {"runs": [], "candidates": []}
    old = {x.get("link"): x for x in history.get("candidates", []) if x.get("link")}
    for c in candidates:
        old.setdefault(c["link"], c)
    history["candidates"] = list(old.values())[:500]
    now = datetime.now(timezone.utc).isoformat()
    history.setdefault("runs", []).insert(0, {"timestamp": now, "queries": len(queries), "successfulQueries": successful_queries, "failedQueries": failed_queries, "newCandidates": len(candidates), "status": "ok"})
    history["runs"] = history["runs"][:20]
    history["lastRun"] = now
    DISCOVERY.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"queries": len(queries), "successfulQueries": successful_queries, "failedQueries": failed_queries, "newCandidates": len(candidates), "status": "ok"}, indent=2))


if __name__ == "__main__":
    main()
