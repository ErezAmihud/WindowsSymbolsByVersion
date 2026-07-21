"""End-to-end test for code/wim_dedup.py + code/extract_and_parse.sh.

Builds a 2-image WIM where image 2 shares most files with image 1 (like the
editions inside a real install.wim), then checks that:
 - the per-image listfiles only contain PE-like files not seen in an earlier image,
 - extracting via the listfiles and parsing yields exactly the union of pdb
   entries that a full extraction of both images would yield,
 - the .paths sidecars record the in-image path of every entry, and
   merge_paths.py turns them into a files.json whose pdb/guid set reproduces
   the merged manifest exactly (the scope=all recreation guarantee).

Requires wimlib-imagex (apt package wimtools).
Run from the repo root: pytest tests/test_wim_dedup.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid

import pytest
from make_pe import expected_signature_string, make_pe

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write(root, rel_path, data):
    path = os.path.join(root, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def pe_and_entry(pdb_name, guid_str, age):
    guid = uuid.UUID(guid_str)
    return (
        make_pe(pdb_name, guid, age),
        f"{pdb_name},{expected_signature_string(guid, age)},1",
    )


def test_wim_dedup():
    if shutil.which("wimlib-imagex") is None:
        pytest.skip("wimlib-imagex not installed (apt-get install wimtools)")

    with tempfile.TemporaryDirectory() as tmp:
        img1, img2 = os.path.join(tmp, "img1"), os.path.join(tmp, "img2")
        expected = set()

        shared_pe, entry = pe_and_entry("ntdll.pdb", "11111111-1111-1111-1111-111111111111", 1)
        expected.add(entry)
        old_b, entry = pe_and_entry("b_old.pdb", "22222222-2222-2222-2222-222222222222", 1)
        expected.add(entry)
        new_b, entry = pe_and_entry("b_new.pdb", "33333333-3333-3333-3333-333333333333", 2)
        expected.add(entry)
        only2_pe, entry = pe_and_entry("only2.pdb", "44444444-4444-4444-4444-444444444444", 5)
        expected.add(entry)
        bootmgr_pe, entry = pe_and_entry("bootmgr.pdb", "55555555-5555-5555-5555-555555555555", 9)
        expected.add(entry)
        space_pe, entry = pe_and_entry("space.pdb", "66666666-6666-6666-6666-666666666666", 3)
        expected.add(entry)

        # image 1
        write(img1, "Windows/System32/ntdll.dll", shared_pe)
        write(img1, "Windows/System32/b.dll", old_b)
        write(img1, "Program Files/App/sp ace.exe", space_pe)
        write(img1, "readme.txt", b"MZ but wrong extension, must be skipped")
        # image 2: ntdll identical, b.dll updated, two new files
        write(img2, "Windows/System32/ntdll.dll", shared_pe)
        write(img2, "Windows/System32/b.dll", new_b)
        write(img2, "Windows/System32/only2.sys", only2_pe)
        write(img2, "bootmgr", bootmgr_pe)
        write(img2, "Program Files/App/sp ace.exe", space_pe)

        wim = os.path.join(tmp, "install.wim")
        for img in (img1, img2):
            cmd = "capture" if img == img1 else "append"
            subprocess.run(
                ["wimlib-imagex", cmd, img, wim, os.path.basename(img)],
                check=True,
                capture_output=True,
            )

        # run the resolver + per-image extraction in a clean workdir, like the workflow does
        workdir = os.path.join(tmp, "work")
        code_dir = os.path.join(workdir, "code")
        os.makedirs(code_dir)
        for script in (
            "wim_dedup.py",
            "extract_and_parse.sh",
            "pdb_finding.py",
            "merge_paths.py",
        ):
            shutil.copy(os.path.join(REPO_ROOT, "code", script), code_dir)
        shutil.copy(wim, workdir)

        out = subprocess.run(
            [sys.executable, "code/wim_dedup.py", "install.wim", "install"],
            check=True,
            capture_output=True,
            text=True,
            cwd=workdir,
        )
        matrix_line = out.stdout.strip()
        assert matrix_line == "version_matrix=[1,2]", f"unexpected matrix output: {matrix_line!r}"

        with open(os.path.join(workdir, "listfile_install_1.txt")) as f:
            listfile_1 = f.read()
        with open(os.path.join(workdir, "listfile_install_2.txt")) as f:
            listfile_2 = f.read()
        assert sorted(listfile_1.splitlines()) == [
            '"/Program Files/App/sp ace.exe"',
            '"/Windows/System32/b.dll"',
            '"/Windows/System32/ntdll.dll"',
        ], f"unexpected listfile 1: {listfile_1!r}"
        # image 2 must only list content not already covered by image 1
        assert sorted(listfile_2.splitlines()) == [
            '"/Windows/System32/b.dll"',
            '"/Windows/System32/only2.sys"',
            '"/bootmgr"',
        ], f"unexpected listfile 2: {listfile_2!r}"
        assert "readme.txt" not in listfile_1 + listfile_2

        got = set()
        got_paths = {}
        for image in ("1", "2"):
            subprocess.run(
                ["bash", "code/extract_and_parse.sh", "install", image],
                check=True,
                cwd=workdir,
            )
            with open(os.path.join(workdir, f"manifest_install_{image}.out")) as f:
                got.update(line.strip() for line in f if line.strip())
            with open(os.path.join(workdir, f"manifest_install_{image}.paths")) as f:
                got_paths[image] = sorted(line.split("\t")[0] for line in f if line.strip())

        assert got == expected, (
            f"manifest mismatch:\nmissing: {sorted(expected - got)}\n"
            f"unexpected: {sorted(got - expected)}"
        )

        # .paths must record the in-image path of every extracted PE
        assert got_paths["1"] == [
            "Program Files/App/sp ace.exe",
            "Windows/System32/b.dll",
            "Windows/System32/ntdll.dll",
        ], f"unexpected image 1 paths: {got_paths['1']}"
        assert got_paths["2"] == [
            "Windows/System32/b.dll",
            "Windows/System32/only2.sys",
            "bootmgr",
        ], f"unexpected image 2 paths: {got_paths['2']}"

        # empty-listfile path: extract_and_parse must produce empty outputs
        open(os.path.join(workdir, "listfile_install_9.txt"), "w").close()
        subprocess.run(
            ["bash", "code/extract_and_parse.sh", "install", "9"],
            check=True,
            cwd=workdir,
        )
        assert os.path.getsize(os.path.join(workdir, "manifest_install_9.out")) == 0
        assert os.path.getsize(os.path.join(workdir, "manifest_install_9.paths")) == 0

        # merging all .paths must reproduce the merged manifest (scope=all guarantee)
        subprocess.run(
            [sys.executable, "code/merge_paths.py", ".", "files.json"],
            check=True,
            cwd=workdir,
        )
        with open(os.path.join(workdir, "files.json")) as fh:
            files = json.load(fh)
        recreated = {f"{f['pdb']},{f['guid']},1" for f in files}
        assert recreated == expected, (
            f"files.json does not reproduce the manifest:\nmissing: {sorted(expected - recreated)}"
            f"\nunexpected: {sorted(recreated - expected)}"
        )

    print(f"test_wim_dedup OK ({len(expected)} entries)")
