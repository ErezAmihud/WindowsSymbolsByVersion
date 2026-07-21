"""Build a pdblister manifest for an index entry, optionally path-filtered.

Scope filtering never touches the pipeline: the committed .manifest is used
as-is for the unfiltered case, and any path filter recreates the manifest
from the build's files.json ({path, pdb, guid} records captured at
generation time).
"""

import requests

SYSTEM32_PREFIX = "windows/system32/"


def _fetch(url):
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        raise SystemExit(f"error: failed to download {url}: {e}") from e


def _normalize(path):
    return path.replace("\\", "/").lstrip("/").lower()


def build_manifest(entry, path_prefix=None):
    """Return manifest text (`pdb,guid,1` lines) for an index entry.

    path_prefix=None means no filtering. A prefix (e.g. "windows/system32/")
    is matched case-insensitively against each binary's path inside the image.
    """
    if path_prefix is None:
        return _fetch(entry["manifest"]).text

    if "files" not in entry:
        raise SystemExit(
            f"error: build {entry['build']} ({entry['uuid']}) predates path data; "
            "path filtering is only available for builds processed after path "
            "recording was added. Use --scope all for this build."
        )

    prefix = _normalize(path_prefix)
    files = _fetch(entry["files"]).json()
    lines = sorted(
        {f"{f['pdb']},{f['guid']},1" for f in files if _normalize(f["path"]).startswith(prefix)}
    )
    return "".join(line + "\n" for line in lines)
