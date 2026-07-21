"""End-to-end test for code/pdb_finding.py and code/merge_paths.py.

Builds a directory tree of synthetic PE files (and non-PE decoys) and checks
that the generated manifest contains exactly the expected pdb entries, that
the optional .paths output records the exact path/pdb/guid TSV lines, and
that merge_paths.py merges .paths files into a sorted deduped files.json.

Run from the repo root: python3 tests/test_pdb_finding.py
"""

import json
import os
import subprocess
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from make_pe import expected_signature_string, make_pe

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_tree(root):
    expected = set()
    expected_paths = set()

    def add_pe(rel_path, pdb_name, guid_str, age):
        path = os.path.join(root, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        guid = uuid.UUID(guid_str)
        with open(path, "wb") as f:
            f.write(make_pe(pdb_name, guid, age))
        expected.add(f"{pdb_name},{expected_signature_string(guid, age)},1")
        expected_paths.add(f"{rel_path}\t{pdb_name}\t{expected_signature_string(guid, age)}")

    add_pe(
        "Windows/System32/ntdll.dll",
        "ntdll.pdb",
        "11111111-2222-3333-4444-555555555555",
        1,
    )
    add_pe(
        "Windows/System32/kernel32.dll",
        "kernel32.pdb",
        "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        2,
    )
    add_pe(
        "Windows/explorer.exe",
        "explorer.pdb",
        "99999999-8888-7777-6666-555544443333",
        10,
    )
    add_pe(
        "Program Files/App/sp ace.exe",
        "space.pdb",
        "0f0f0f0f-1e1e-2d2d-3c3c-4b4b4b4b4b4b",
        3,
    )
    # extensionless PE (e.g. bootmgr)
    add_pe("bootmgr", "bootmgr.pdb", "12312312-4564-5645-7897-891011121314", 7)

    # decoys that must not produce manifest lines
    with open(os.path.join(root, "Windows/no_debug.dll"), "wb") as f:
        f.write(make_pe(None))  # valid PE without a debug directory
    with open(os.path.join(root, "Windows/readme.txt"), "w") as f:
        f.write("not a pe file")
    with open(os.path.join(root, "Windows/broken.dll"), "wb") as f:
        f.write(b"MZ" + b"\xde\xad\xbe\xef" * 20)  # MZ magic but not a valid PE
    open(os.path.join(root, "Windows/empty.dll"), "wb").close()

    return expected, expected_paths


def test_pdb_finding():
    with tempfile.TemporaryDirectory() as tmp:
        tree = os.path.join(tmp, "tree")
        os.makedirs(tree)
        expected, expected_paths = build_tree(tree)

        manifest = os.path.join(tmp, "manifest.out")
        subprocess.run(
            [
                sys.executable,
                os.path.join(REPO_ROOT, "code", "pdb_finding.py"),
                tree,
                manifest,
            ],
            check=True,
            cwd=REPO_ROOT,
        )

        with open(manifest) as f:
            got = {line.strip() for line in f if line.strip()}
        assert got == expected, (
            f"manifest mismatch:\nmissing: {sorted(expected - got)}\nunexpected: {sorted(got - expected)}"
        )

        # 3-arg mode: same manifest, plus exact path<TAB>pdb<TAB>guid lines
        paths = os.path.join(tmp, "manifest.paths")
        subprocess.run(
            [
                sys.executable,
                os.path.join(REPO_ROOT, "code", "pdb_finding.py"),
                tree,
                manifest,
                paths,
            ],
            check=True,
            cwd=REPO_ROOT,
        )
        with open(manifest) as f:
            got = {line.strip() for line in f if line.strip()}
        assert got == expected, "3-arg mode changed the manifest output"
        with open(paths) as f:
            got_paths = {line.rstrip("\n") for line in f if line.strip()}
        assert got_paths == expected_paths, (
            f"paths mismatch:\nmissing: {sorted(expected_paths - got_paths)}\nunexpected: {sorted(got_paths - expected_paths)}"
        )

    print(f"test_pdb_finding OK ({len(expected)} entries)")


def test_merge_paths():
    with tempfile.TemporaryDirectory() as tmp:
        # overlapping entries across two .paths files must be deduped
        with open(os.path.join(tmp, "a.paths"), "w") as f:
            f.write("Windows/System32/ntdll.dll\tntdll.pdb\tAAAA1\n")
            f.write("Windows/explorer.exe\texplorer.pdb\tBBBB1\n")
        with open(os.path.join(tmp, "b.paths"), "w") as f:
            f.write("Windows/System32/ntdll.dll\tntdll.pdb\tAAAA1\n")
            f.write("bootmgr\tbootmgr.pdb\tCCCC1\n")
        open(os.path.join(tmp, "empty.paths"), "w").close()

        out = os.path.join(tmp, "files.json")
        subprocess.run(
            [
                sys.executable,
                os.path.join(REPO_ROOT, "code", "merge_paths.py"),
                tmp,
                out,
            ],
            check=True,
            cwd=REPO_ROOT,
        )
        got = json.load(open(out))

    assert got == [
        {"path": "Windows/System32/ntdll.dll", "pdb": "ntdll.pdb", "guid": "AAAA1"},
        {"path": "Windows/explorer.exe", "pdb": "explorer.pdb", "guid": "BBBB1"},
        {"path": "bootmgr", "pdb": "bootmgr.pdb", "guid": "CCCC1"},
    ], f"unexpected files.json: {got}"
    print("test_merge_paths OK")


if __name__ == "__main__":
    test_pdb_finding()
    test_merge_paths()
