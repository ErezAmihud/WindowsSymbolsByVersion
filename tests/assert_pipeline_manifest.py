#!/usr/bin/env python3
"""Assert download_build.yml's merged pipeline output matches the known test fixture.

The correctness gate for the test_mode pipeline run: green jobs alone don't prove the
manifest is right, so compare the merged output against make_fake_wims.expected_entries().

Usage (in the assert_test_manifest job): assert_pipeline_manifest.py <manifest.out> <files.json>
 - manifest.out lines are `<pdb>,<guid>,1`
 - files.json is a JSON list of {path, pdb, guid}
Both must reproduce expected_entries(); exits non-zero (failing the job) on any drift.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from make_fake_wims import expected_entries


def _fail(label, got, expected):
    print(
        f"{label} mismatch:\n"
        f"  missing:    {sorted(expected - got)}\n"
        f"  unexpected: {sorted(got - expected)}",
        file=sys.stderr,
    )
    sys.exit(1)


def main(manifest_path, files_json_path):
    expected = expected_entries()

    manifest_entries = set()
    with open(manifest_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            manifest_entries.add(line)
    if manifest_entries != expected:
        _fail("manifest.out", manifest_entries, expected)

    with open(files_json_path) as f:
        files = json.load(f)
    files_entries = {f"{e['pdb']},{e['guid']},1" for e in files}
    if files_entries != expected:
        _fail("files.json", files_entries, expected)

    print(f"assert_pipeline_manifest OK ({len(expected)} entries)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: assert_pipeline_manifest.py <manifest.out> <files.json>")
    main(sys.argv[1], sys.argv[2])
