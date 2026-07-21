#!/usr/bin/bash
# Merge per-partial manifests into a single deduped, count-free manifest.
#
# \r must be stripped before dedup: create_iso's partial (Windows runner)
# ends its lines in \r\n while the wim-derived partials (Linux runners)
# don't, so the same line from each side won't collapse unless \r is gone
# first.
set -e
cat ./partials/*.out | sed 's/\r$//' | sort -u > manifest.out
