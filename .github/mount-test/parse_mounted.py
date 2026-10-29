#!/usr/bin/env python3
"""Prototype: parse the listfile's files straight from a mounted wim image.

Usage: parse_mounted.py <repo_root> <mountpoint> <listfile> <out> <paths_out> [workers]
Same output format as pdb_finding.py, with the in-image path from the listfile.
"""

import os
import sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.join(sys.argv[1], "code"))
from pdb_finding import process_file  # noqa: E402


def main():
    mnt, listfile, out_path, paths_path = sys.argv[2:6]
    workers = int(sys.argv[6]) if len(sys.argv) > 6 else os.cpu_count()
    with open(listfile, encoding="utf-8", errors="surrogateescape") as f:
        rels = [line.strip().strip('"').lstrip("/") for line in f if line.strip()]
    files = [os.path.join(mnt, r) for r in rels]

    with (
        open(out_path, "w") as out,
        open(paths_path, "w") as paths_out,
        ProcessPoolExecutor(max_workers=workers) as ex,
    ):
        for rel, rets in zip(rels, ex.map(process_file, files, chunksize=64)):
            for pdb, guid in rets:
                out.write(f"{pdb},{guid},1\n")
                paths_out.write(f"{rel}\t{pdb}\t{guid}\n")


if __name__ == "__main__":
    main()
