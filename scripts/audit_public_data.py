#!/usr/bin/env python3
"""Fail the public-data build if personal tracker fields leak into repo data."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / "properties.json", ROOT / "data" / "update_history.json", ROOT / "data" / "discovery_history.json"]
FORBIDDEN = {
    "pros", "cons", "questions", "checklist", "favourites", "favs",
    "ratings", "projects", "decisions", "watchlist", "viewingDate", "savedSearches",
    "financial", "deposit", "mortgage", "houseFund", "personalNotes", "personal"
}

def walk(value, path=""):
    if isinstance(value, dict):
        for k, v in value.items():
            if k in FORBIDDEN:
                raise SystemExit(f"Personal-data field '{k}' found in public repository data at {path or '/'}")
            walk(v, f"{path}/{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            walk(v, f"{path}/{i}")

for f in FILES:
    if not f.exists():
        continue
    try:
        walk(json.loads(f.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {f}: {exc}")
print("Public-data audit passed: no recognised personal tracker fields found.")
