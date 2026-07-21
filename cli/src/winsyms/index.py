"""Fetch, cache and query the build index (index.json of the project site)."""

import json
import os
import sys
import time

import requests

INDEX_URL = "https://erezamihud.github.io/WindowsSymbolsByVersion/index.json"
CACHE_FILE = os.path.join(os.path.expanduser("~"), ".cache", "winsyms", "index.json")
CACHE_TTL = 24 * 60 * 60


def load_index(index_file=None, force_refresh=False):
    """Return the list of build entries.

    index_file (from --index) bypasses network and cache entirely - the
    airgap path. Otherwise a <24h cache copy is used; a failed refresh falls
    back to a stale cache with a warning so the CLI keeps working offline.
    """
    if index_file:
        try:
            with open(index_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise SystemExit(f"error: cannot read index file {index_file}: {e}")

    if (
        not force_refresh
        and os.path.exists(CACHE_FILE)
        and time.time() - os.path.getmtime(CACHE_FILE) < CACHE_TTL
    ):
        with open(CACHE_FILE) as f:
            return json.load(f)

    try:
        resp = requests.get(INDEX_URL, timeout=30)
        resp.raise_for_status()
        entries = resp.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        if os.path.exists(CACHE_FILE):
            print(
                f"warning: could not refresh index ({e}); using cached copy",
                file=sys.stderr,
            )
            with open(CACHE_FILE) as f:
                return json.load(f)
        raise SystemExit(
            f"error: could not download {INDEX_URL} and no cache exists: {e}"
        )

    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(entries, f)
    return entries


def resolve(entries, query, arch=None):
    """Return the entries matching query: exact uuid, else exact build, else
    case-insensitive title substring (titles contain the build number, so
    partial builds like "26100" match too)."""
    if arch:
        entries = [e for e in entries if e["arch"] == arch]
    for key in ("uuid", "build"):
        exact = [e for e in entries if e[key] == query]
        if exact:
            return exact
    lowered = query.lower()
    return [e for e in entries if lowered in e["title"].lower()]
