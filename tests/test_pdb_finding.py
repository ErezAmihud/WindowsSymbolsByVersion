"""End-to-end test for code/pdb_finding.py.

Builds a directory tree of synthetic PE files (and non-PE decoys) and checks
that the generated manifest contains exactly the expected pdb entries.

Run from the repo root: python3 tests/test_pdb_finding.py
"""
import os
import subprocess
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from make_pe import make_pe, expected_signature_string

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_tree(root):
    expected = set()

    def add_pe(rel_path, pdb_name, guid_str, age):
        path = os.path.join(root, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        guid = uuid.UUID(guid_str)
        with open(path, "wb") as f:
            f.write(make_pe(pdb_name, guid, age))
        expected.add(f"{pdb_name},{expected_signature_string(guid, age)},1")

    add_pe("Windows/System32/ntdll.dll", "ntdll.pdb", "11111111-2222-3333-4444-555555555555", 1)
    add_pe("Windows/System32/kernel32.dll", "kernel32.pdb", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", 2)
    add_pe("Windows/explorer.exe", "explorer.pdb", "99999999-8888-7777-6666-555544443333", 10)
    add_pe("Program Files/App/sp ace.exe", "space.pdb", "0f0f0f0f-1e1e-2d2d-3c3c-4b4b4b4b4b4b", 3)
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

    return expected


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tree = os.path.join(tmp, "tree")
        os.makedirs(tree)
        expected = build_tree(tree)

        manifest = os.path.join(tmp, "manifest.out")
        subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "code", "pdb_finding.py"), tree, manifest],
            check=True, cwd=REPO_ROOT,
        )

        with open(manifest) as f:
            got = {line.strip() for line in f if line.strip()}

    assert got == expected, f"manifest mismatch:\nmissing: {sorted(expected - got)}\nunexpected: {sorted(got - expected)}"
    print(f"test_pdb_finding OK ({len(expected)} entries)")


if __name__ == "__main__":
    main()
