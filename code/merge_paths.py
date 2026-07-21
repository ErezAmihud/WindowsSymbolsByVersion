#!/usr/bin/env python3
"""Merge the per-image `path<TAB>pdb<TAB>guid` .paths files into one files.json.

files.json is the complete per-build record of which binary (by path inside
the image) references which pdb/guid. It is committed once per build and lets
the winsyms CLI recreate scope-filtered manifests without ever reprocessing
an ISO.

Usage: merge_paths.py <dir_with_paths_files> <out_json>
"""

import glob
import json
import os
import sys


def merge(src_dir):
    entries = set()
    for paths_file in glob.glob(os.path.join(src_dir, "*.paths")):
        with open(paths_file) as f:
            for lineno, line in enumerate(f, 1):
                line = line.rstrip("\n")
                if not line:
                    continue
                try:
                    path, pdb, guid = line.split("\t")
                except ValueError as e:
                    raise ValueError(
                        f"{paths_file}:{lineno}: expected 3 tab-separated fields, got {line!r}"
                    ) from e
                entries.add((path, pdb, guid))
    return [{"path": p, "pdb": pdb, "guid": guid} for p, pdb, guid in sorted(entries)]


def main():
    if len(sys.argv) != 3:
        print("Usage: merge_paths.py <dir_with_paths_files> <out_json>", file=sys.stderr)
        sys.exit(1)
    merged = merge(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        json.dump(merged, f, separators=(",", ":"))
    print(f"merged {len(merged)} entries into {sys.argv[2]}", file=sys.stderr)


if __name__ == "__main__":
    main()
