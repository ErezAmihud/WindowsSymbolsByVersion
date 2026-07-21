"""End-to-end test of the full manifest-generation pipeline against a
synthetic ISO layout: code/pdb_finding.py (ISO root) + code/wim_dedup.py +
code/extract_and_parse.sh (boot.wim + install.wim) + code/merge_manifests.sh.

Mirrors every step of .github/workflows/download_build.yml between
create_iso's iso-root scan and merge_artifacts, skipping only the genuinely
external/platform-only steps (uupdump download, the Windows uup-converter,
git commit) -- same scope test_wim_dedup.py already covers for the wim side.

One entry (ntdll.pdb) is planted identically in both boot.wim and install.wim
image 1, and the iso-root partial's line endings are rewritten to \r\n to
simulate it coming from the Windows create_iso runner while the wim-derived
partials come from Linux runners. This is the exact condition merge_artifacts
must handle: dedup across partials regardless of \r origin, with no uniq -c
count prefix in the result.

Requires wimlib-imagex (apt package wimtools).
Run from the repo root: python3 tests/test_manifest_pipeline.py
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from make_pe import make_pe, expected_signature_string

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write(root, rel_path, data):
    path = os.path.join(root, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def pe_and_entry(pdb_name, guid_str, age):
    guid = uuid.UUID(guid_str)
    return make_pe(pdb_name, guid, age), f"{pdb_name},{expected_signature_string(guid, age)},1"


def build_wims(tmp):
    """boot.wim (1 image) + install.wim (2 images, like test_wim_dedup.py).
    ntdll.pdb is shared between boot.wim and install.wim image 1, to exercise
    dedup *across* wims, not just within one image."""
    expected = set()

    boot_dir = os.path.join(tmp, "boot_img")
    ntdll_pe, entry = pe_and_entry("ntdll.pdb", "11111111-1111-1111-1111-111111111111", 1)
    expected.add(entry)
    write(boot_dir, "Windows/System32/ntdll.dll", ntdll_pe)
    winload_pe, entry = pe_and_entry("winload.pdb", "77777777-7777-7777-7777-777777777777", 4)
    expected.add(entry)
    write(boot_dir, "Windows/System32/winload.efi", winload_pe)

    boot_wim = os.path.join(tmp, "boot.wim")
    subprocess.run(["wimlib-imagex", "capture", boot_dir, boot_wim, "boot"],
                   check=True, capture_output=True)

    img1 = os.path.join(tmp, "install_img1")
    img2 = os.path.join(tmp, "install_img2")
    write(img1, "Windows/System32/ntdll.dll", ntdll_pe)
    b_old_pe, entry = pe_and_entry("b_old.pdb", "22222222-2222-2222-2222-222222222222", 1)
    expected.add(entry)
    write(img1, "Windows/System32/b.dll", b_old_pe)
    write(img1, "readme.txt", b"not a pe file")

    write(img2, "Windows/System32/ntdll.dll", ntdll_pe)
    b_new_pe, entry = pe_and_entry("b_new.pdb", "33333333-3333-3333-3333-333333333333", 2)
    expected.add(entry)
    write(img2, "Windows/System32/b.dll", b_new_pe)
    only2_pe, entry = pe_and_entry("only2.pdb", "44444444-4444-4444-4444-444444444444", 5)
    expected.add(entry)
    write(img2, "Windows/System32/only2.sys", only2_pe)

    install_wim = os.path.join(tmp, "install.wim")
    for img in (img1, img2):
        cmd = "capture" if img == img1 else "append"
        subprocess.run(["wimlib-imagex", cmd, img, install_wim, os.path.basename(img)],
                       check=True, capture_output=True)

    return boot_wim, install_wim, expected


def build_iso_root(tmp, boot_wim, install_wim):
    """A synthetic unpacked_dir (what move_iso_dir.bat produces from a real
    ISO): a loose file at the root, scanned directly by create_iso's
    pdb_finding.py call, plus sources/boot.wim and sources/install.wim."""
    expected = set()
    root = os.path.join(tmp, "unpacked_dir")

    setup_pe, entry = pe_and_entry("setup.pdb", "55555555-5555-5555-5555-555555555555", 3)
    expected.add(entry)
    write(root, "setup.exe", setup_pe)
    write(root, "readme.txt", b"not a pe file")

    os.makedirs(os.path.join(root, "sources"), exist_ok=True)
    shutil.copy(boot_wim, os.path.join(root, "sources", "boot.wim"))
    shutil.copy(install_wim, os.path.join(root, "sources", "install.wim"))

    return root, expected


def run_wim_stage(workdir, name):
    """wim_dedup.py + extract_and_parse.sh for one wim, like parse_boot_wim /
    parse_install_wim do per matrix entry."""
    out = subprocess.run([sys.executable, "code/wim_dedup.py", f"{name}.wim", name],
                         check=True, capture_output=True, text=True, cwd=workdir)
    matrix = json.loads(out.stdout.strip().split("=", 1)[1])
    for version in matrix:
        subprocess.run(["bash", "code/extract_and_parse.sh", name, str(version)],
                       check=True, cwd=workdir)


def main():
    if shutil.which("wimlib-imagex") is None:
        print("SKIP: wimlib-imagex not installed (apt-get install wimtools)")
        return

    with tempfile.TemporaryDirectory() as tmp:
        boot_wim, install_wim, wim_expected = build_wims(tmp)
        unpacked_dir, root_expected = build_iso_root(tmp, boot_wim, install_wim)
        expected = wim_expected | root_expected

        workdir = os.path.join(tmp, "work")
        code_dir = os.path.join(workdir, "code")
        os.makedirs(code_dir)
        for script in ("wim_dedup.py", "extract_and_parse.sh", "pdb_finding.py", "merge_manifests.sh"):
            shutil.copy(os.path.join(REPO_ROOT, "code", script), code_dir)

        # create_iso: scan the iso root directly
        subprocess.run(
            [sys.executable, "code/pdb_finding.py", unpacked_dir,
             "manifest_general.out", "manifest_general.paths"],
            check=True, cwd=workdir,
        )
        # simulate this partial coming from the Windows create_iso runner
        # (Python text-mode writes \r\n there) while the wim-derived
        # partials below come from Linux runners (\n only)
        general_path = os.path.join(workdir, "manifest_general.out")
        with open(general_path, "rb") as f:
            content = f.read()
        with open(general_path, "wb") as f:
            f.write(content.replace(b"\n", b"\r\n"))

        # split_wims + parse_boot_wim/parse_install_wim
        shutil.copy(os.path.join(unpacked_dir, "sources", "boot.wim"), workdir)
        shutil.copy(os.path.join(unpacked_dir, "sources", "install.wim"), workdir)
        run_wim_stage(workdir, "boot")
        run_wim_stage(workdir, "install")

        # merge_artifacts
        partials = os.path.join(workdir, "partials")
        os.makedirs(partials)
        for out_file in glob.glob(os.path.join(workdir, "manifest*.out")):
            shutil.copy(out_file, partials)
        subprocess.run(["bash", "code/merge_manifests.sh"], check=True, cwd=workdir)

        with open(os.path.join(workdir, "manifest.out"), "rb") as f:
            raw = f.read()

    assert b"\r" not in raw, "manifest.out still has CRLF line endings"
    lines = raw.decode("ascii").splitlines()
    assert lines == sorted(lines), f"manifest.out is not sorted: {lines}"
    assert len(lines) == len(set(lines)), f"manifest.out has duplicate lines: {lines}"
    for line in lines:
        assert not re.match(r"^\s*\d+\s", line), f"line has a uniq -c count prefix: {line!r}"
    assert set(lines) == expected, (
        f"manifest.out mismatch:\nmissing: {sorted(expected - set(lines))}"
        f"\nunexpected: {sorted(set(lines) - expected)}"
    )

    print(f"test_manifest_pipeline OK ({len(expected)} entries)")


if __name__ == "__main__":
    main()
