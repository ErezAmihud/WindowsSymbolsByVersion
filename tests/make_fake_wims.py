#!/usr/bin/env python3
"""Generate tiny synthetic boot.wim + install.wim + manifest_general for pipeline testing.

Substitutes for the ~110min Windows `create_iso` job so `download_build.yml`'s downstream
jobs can run on Linux in minutes (`test_mode: true`). Because the fake PEs use FIXED
GUIDs, the merged manifest the pipeline should produce is fully predictable:
`expected_entries()` is that ground truth, asserted by `tests/assert_pipeline_manifest.py`.

Reuses `tests/make_pe.py` (stdlib only) -- no pefile needed. Requires wimlib-imagex
(apt wimtools). Run from repo root: python3 tests/make_fake_wims.py
"""
import os
import re
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from make_pe import make_pe, expected_signature_string

# Single source of truth: (wim, image, rel_path, pdb, guid, age).
#  - wim "general" is the create_iso-only ISO-root partial (no real WIM); it carries a pdb
#    present nowhere else, proving that partial reaches merge_artifacts.
#  - install image 2 re-lists ntdll.dll (identical bytes -> deduped by wim_dedup by content
#    hash) plus a unique file, so the version matrix fans out to [1,2].
FIXTURE = [
    ("boot",    1, "bootmgr",                       "bootmgr.pdb",  "aaaaaaaa-0000-0000-0000-000000000001", 1),
    ("boot",    1, "boot/bootx.sys",                "bootx.pdb",    "aaaaaaaa-0000-0000-0000-000000000002", 1),
    ("install", 1, "Windows/System32/ntdll.dll",    "ntdll.pdb",    "bbbbbbbb-0000-0000-0000-000000000001", 1),
    ("install", 1, "Windows/System32/kernel32.dll", "kernel32.pdb", "bbbbbbbb-0000-0000-0000-000000000002", 1),
    ("install", 2, "Windows/System32/ntdll.dll",    "ntdll.pdb",    "bbbbbbbb-0000-0000-0000-000000000001", 1),  # shared -> deduped
    ("install", 2, "Windows/System32/only2.sys",    "only2.pdb",    "bbbbbbbb-0000-0000-0000-000000000003", 1),
    ("general", 0, "unpacked_dir/sources/setup.exe", "general.pdb", "cccccccc-0000-0000-0000-000000000001", 1),
]


def _entry(pdb, guid_str, age):
    return f"{pdb},{expected_signature_string(uuid.UUID(guid_str), age)},1"


def expected_entries():
    """Distinct manifest lines that must survive the full pipeline (merge dedups)."""
    return {_entry(pdb, g, age) for (_w, _i, _p, pdb, g, age) in FIXTURE}


def _write_pe(root, rel_path, pdb, guid_str, age):
    path = os.path.join(root, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(make_pe(pdb, uuid.UUID(guid_str), age))


def _rm(path):
    if os.path.exists(path):
        os.remove(path)


def build(dest="."):
    if shutil.which("wimlib-imagex") is None:
        sys.exit("wimlib-imagex not installed (apt-get install wimtools)")

    src = os.path.join(dest, "_fakewim_src")
    shutil.rmtree(src, ignore_errors=True)

    # boot.wim: single image
    boot_dir = os.path.join(src, "boot_1")
    for (w, _i, rel, pdb, g, age) in FIXTURE:
        if w == "boot":
            _write_pe(boot_dir, rel, pdb, g, age)
    boot_wim = os.path.join(dest, "boot.wim")
    _rm(boot_wim)
    subprocess.run(["wimlib-imagex", "capture", boot_dir, boot_wim, "boot_1"],
                   check=True, capture_output=True)

    # install.wim: capture image 1, append image 2 (mimics editions sharing files)
    install_wim = os.path.join(dest, "install.wim")
    _rm(install_wim)
    for image in (1, 2):
        img_dir = os.path.join(src, f"install_{image}")
        for (w, i, rel, pdb, g, age) in FIXTURE:
            if w == "install" and i == image:
                _write_pe(img_dir, rel, pdb, g, age)
        cmd = "capture" if image == 1 else "append"
        subprocess.run(["wimlib-imagex", cmd, img_dir, install_wim, f"install_{image}"],
                       check=True, capture_output=True)

    # manifest_general.out/.paths: the create_iso-only partial, written directly (no pefile)
    with open(os.path.join(dest, "manifest_general.out"), "w") as out, \
         open(os.path.join(dest, "manifest_general.paths"), "w") as paths:
        for (w, _i, rel, pdb, g, age) in FIXTURE:
            if w == "general":
                sig = expected_signature_string(uuid.UUID(g), age)
                out.write(f"{pdb},{sig},1\n")
                paths.write(f"{rel}\t{pdb}\t{sig}\n")

    shutil.rmtree(src, ignore_errors=True)


if __name__ == "__main__":
    build()
    # self-check: WIMs are readable and the fixture is well-formed
    info = subprocess.run(["wimlib-imagex", "info", "install.wim"],
                          check=True, capture_output=True, text=True).stdout
    assert re.search(r"Image Count:\s*2", info), info
    subprocess.run(["wimlib-imagex", "info", "boot.wim"], check=True, capture_output=True)
    assert os.path.getsize("manifest_general.out") > 0
    exp = expected_entries()
    assert len(exp) == 6, exp  # 2 boot + 3 distinct install + 1 general
    print(f"make_fake_wims OK ({len(exp)} expected entries)")
