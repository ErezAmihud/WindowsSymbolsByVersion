#!/usr/bin/env python3
"""Pick the next builds to process.

Filters the uupdump build list down to new, non-insider x86/amd64 builds
available in en-us (consulting builds_state.json for what is already done,
failed too often, or user-prioritized) and sets the picked uuids as the
`uuid_matrix` step output for the download workflow.

Usage: daily.py [allowed_download_size]
"""

import json
import re
import sys

from gha import write_output
from state import excluded_uuids, load_state, priority_uuids
from uupdump import get_langs, listid

DEFAULT_ALLOWED_SIZE = 3
EXCLUDED_TITLE_PATTERNS = [r"cumulative update", r"\binsider\b", r"\bpreview\b"]


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
    allowed_size = (
        int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else DEFAULT_ALLOWED_SIZE
    )

    state = load_state()
    picked = pick_builds(
        listid(), excluded_uuids(state), priority_uuids(state), allowed_size
    )
    for build in picked:
        print(build.uuid, str(build), file=sys.stderr)
    write_output("uuid_matrix", json.dumps([build.uuid for build in picked]))
