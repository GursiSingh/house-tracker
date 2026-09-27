#!/usr/bin/env python3
"""Safely check tracked property source pages.

This deliberately does NOT invent availability or overwrite the manually verified
property facts. It only records whether a source URL is reachable and extracts
obvious page title/price signals when present. Review flagged changes before
relying on them.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
PROPERTIES = ROOT / "properties.json"
HISTORY = ROOT / "data" / "update_history.json"

USER_AGENT = "HouseTracker/1.0 (personal property tracking; contact via repository)"
TIMEOUT = 15


def fetch(url: str):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-GB,en;q=0.9"})
    try:
        with urlopen(req, timeout=TIMEOUT) as r:
            body = r.read(700_000).decode("utf-8", errors="ignore")
            return r.status, body, None
    except HTTPError as e:
        try:
            body = e.read(200_000).decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        return e.code, body, str(e)
    except (URLError, TimeoutError, OSError) as e:
        return None, "", str(e)


def meta(body: str, name: str):
    pat = rf'<meta[^>]+(?:property|name)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)' \
          rf'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(name)}["\']'
    m = re.search(pat, body, re.I)
    if not m:
        return None
    return html.unescape(m.group(1) or m.group(2) or "").strip()


def title(body: str):
    value = meta(body, "og:title") or meta(body, "twitter:title")
    if value:
        return value[:240]
    m = re.search(r'<title[^>]*>(.*?)</title>', body, re.I | re.S)
    return html.unescape(re.sub(r'\s+', ' ', m.group(1))).strip()[:240] if m else None


def price(body: str):
    # Prefer JSON-LD/obvious price metadata, then a conservative GBP pattern.
    for key in ("product:price:amount", "og:price:amount"):
        v = meta(body, key)
        if v:
            try:
                return int(float(v.replace(',', '').strip()))
            except ValueError:
                pass
    for pat in (r'"price"\s*:\s*"?(\d{5,6}(?:\.\d+)?)', r'£\s?([0-9]{3},?[0-9]{3})'):
        m = re.search(pat, body, re.I)
        if m:
            try:
                return int(float(m.group(1).replace(',', '')))
            except ValueError:
                pass
    return None


def image_url(body: str, base_url: str):
    # Prefer an OpenGraph image published by the exact listing page.
    value = meta(body, "og:image") or meta(body, "twitter:image")
    if value:
        return urljoin(base_url, value)
    # Conservative fallback: an image tag whose alt/title explicitly identifies a
    # floorplan is used for the floorplan field, not as a property photo.
    return None

def floorplan_url(body: str, base_url: str):
    patterns = [
        r'<img[^>]+(?:alt|title)=["\'][^"\']*floor ?plan[^"\']*["\'][^>]+src=["\']([^"\']+)',
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]+(?:alt|title)=["\'][^"\']*floor ?plan[^"\']*["\']',
    ]
    for pat in patterns:
        m=re.search(pat,body,re.I)
        if m:
            return urljoin(base_url,html.unescape(m.group(1)))
    return None

def main():
    data = json.loads(PROPERTIES.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    changes = []
    checked = 0

    for item in data:
        url = item.get("link")
        if not url:
            continue
        checked += 1
        status, body, error = fetch(url)
        t = title(body) if body else None
        observed_price = price(body) if body else None
        preview = image_url(body, url) if body else None
        floorplan = floorplan_url(body, url) if body else None
        tr = item.setdefault("tracking", {})
        old_price = tr.get("observedPrice")
        tr["lastChecked"] = now
        tr["httpStatus"] = status
        tr["sourceReachable"] = bool(status and 200 <= status < 400)
        tr["observedTitle"] = t
        tr["observedPrice"] = observed_price
        tr["previewImage"] = preview
        if preview:
            item.setdefault("media", {})["photos"] = [preview]
            item["media"]["photoSource"] = url
            item["media"]["photoVerifiedAt"] = now
        if floorplan:
            item.setdefault("media", {})["floorplan"] = {"url": floorplan, "source": url, "verifiedAt": now}
        tr["priceChanged"] = bool(old_price and observed_price and old_price != observed_price)
        note = ""
        if tr["priceChanged"]:
            note = f"Observed source price changed from £{old_price:,} to £{observed_price:,}; verify listing manually."
            changes.append({"id": item["id"], "type": "observed_price_change", "note": note})
        elif status is None or status >= 400:
            note = f"Source returned {status or 'no response'}; availability not inferred."
            changes.append({"id": item["id"], "type": "source_check", "note": note})
        # Keep a repository-backed price timeline as well as the browser-only history.
        # This records observed source prices only; it never invents a historical price.
        if observed_price:
            ph = tr.setdefault("priceHistory", [])
            if not ph or ph[-1].get("price") != observed_price:
                ph.append({"date": now[:10], "price": observed_price})
                tr["priceHistory"] = ph[-60:]
        tr["changeNote"] = note

    PROPERTIES.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    history = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else {"runs": []}
    history["lastRun"] = now
    history.setdefault("runs", []).insert(0, {"timestamp": now, "checked": checked, "changes": changes})
    history["runs"] = history["runs"][:20]
    HISTORY.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"checked": checked, "changes": len(changes), "timestamp": now}, indent=2))


if __name__ == "__main__":
    main()
