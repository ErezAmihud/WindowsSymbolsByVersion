#!/usr/bin/env python3
"""Pick the next builds to process.

Reads process_builds.json / problematic.json / priority.json, filters the
uupdump build list down to new, non-insider x86/amd64 builds available in
en-us, and writes the picked uuids to a.txt as a JSON list (the uuid matrix
for the download workflow).

Usage: daily.py [allowed_download_size]
"""
import re
import sys
import json
from listid import listid
from get_lang import get_langs

DEFAULT_ALLOWED_SIZE = 3
EXCLUDED_TITLE_PATTERNS = [r"cumulative update", r"\binsider\b", r"\bpreview\b"]


def load_state():
    processed = set(json.load(open("process_builds.json", "r")))
    processed.update(json.load(open("problematic.json", "r")))
    priority = set(json.load(open("priority.json", "r")))
    return processed, priority


def is_wanted(build, processed):
    if build.uuid in processed:
        return False
    if build.arch not in ("x86", "amd64"):
        return False
    title = build.title.lower()
    return not any(re.search(pattern, title) for pattern in EXCLUDED_TITLE_PATTERNS)


def pick_builds(builds, processed, priority, allowed_size, get_langs=get_langs):
    builds = sorted(builds, key=lambda build: build.uuid not in priority)
    picked = []
    for build in builds:
        if len(picked) >= allowed_size:
            break
        if not is_wanted(build, processed):
            continue
        try:
            if "en-us" not in get_langs(build.uuid):
                continue
        except Exception as e:
            print(f"skipping {build.uuid}, listlangs failed: {e}", file=sys.stderr)
            continue
        picked.append(build)
    return picked


if __name__ == "__main__":
    allowed_size = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else DEFAULT_ALLOWED_SIZE

    processed, priority = load_state()
    picked = pick_builds(listid(), processed, priority, allowed_size)
    for build in picked:
        print(build.uuid, str(build))
    json.dump([build.uuid for build in picked], open("a.txt", "w"))
