"""Tests for the winsyms CLI (cli/).

No network: a local http.server serves a fixture index.json / manifest /
files.json, and the end-to-end `get` runs against a fake `pdblister` script
on PATH that records its argv and staged manifest.

Run from the repo root: pytest tests/test_cli.py
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

from winsyms import index as windex
from winsyms import manifest as wmanifest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Kept for the `-m winsyms` subprocess env below; not a sys.path insert.
CLI_SRC = os.path.join(REPO_ROOT, "cli", "src")

UUID_NEW = "aaaaaaaa-0000-0000-0000-000000000001"
UUID_NEW_X86 = "aaaaaaaa-0000-0000-0000-000000000002"
UUID_OLD = "bbbbbbbb-0000-0000-0000-000000000001"

FILES_NEW = [
    {"path": "Windows/System32/drivers/x.sys", "pdb": "x.pdb", "guid": "G2"},
    {"path": "Windows/System32/ntdll.dll", "pdb": "ntdll.pdb", "guid": "G1"},
    # same pdb/guid reachable via two paths: recreation must dedup
    {"path": "Windows/SysWOW64/ntdll.dll", "pdb": "ntdll.pdb", "guid": "G1"},
    {"path": "Windows/explorer.exe", "pdb": "explorer.pdb", "guid": "G3"},
]
MANIFEST_NEW = "explorer.pdb,G3,1\nntdll.pdb,G1,1\nx.pdb,G2,1\n"
MANIFEST_OLD = "old.pdb,G9,1\n"


def make_fixtures(root, base_url):
    entries = [
        {
            "uuid": UUID_NEW,
            "title": "Windows 11, version 24H2 (26100.1297)",
            "build": "26100.1297",
            "arch": "amd64",
            "manifest": f"{base_url}/new.manifest",
            "files": f"{base_url}/new.files.json",
        },
        {
            "uuid": UUID_NEW_X86,
            "title": "Windows 11, version 24H2 (26100.1297)",
            "build": "26100.1297",
            "arch": "x86",
            "manifest": f"{base_url}/new_x86.manifest",
            "files": f"{base_url}/new_x86.files.json",
        },
        {
            "uuid": UUID_OLD,
            "title": "Feature update to Windows 10, version 21H1 (19043.1826)",
            "build": "19043.1826",
            "arch": "amd64",
            "manifest": f"{base_url}/old.manifest",
        },
    ]
    with open(os.path.join(root, "index.json"), "w") as f:
        json.dump(entries, f)
    with open(os.path.join(root, "new.manifest"), "w") as f:
        f.write(MANIFEST_NEW)
    with open(os.path.join(root, "new.files.json"), "w") as f:
        json.dump(FILES_NEW, f)
    with open(os.path.join(root, "old.manifest"), "w") as f:
        f.write(MANIFEST_OLD)
    return entries


def check_resolve(entries):
    assert windex.resolve(entries, UUID_OLD) == [entries[2]]
    # exact build: both arches; --arch narrows to one
    assert windex.resolve(entries, "26100.1297") == entries[:2]
    assert windex.resolve(entries, "26100.1297", arch="amd64") == [entries[0]]
    # title substring, case-insensitive, matches partial build numbers too
    assert windex.resolve(entries, "24h2", arch="x86") == [entries[1]]
    assert windex.resolve(entries, "19043") == [entries[2]]
    assert windex.resolve(entries, "no-such-build") == []
    print("test_resolve OK")


def check_build_manifest(entries):
    new, old = entries[0], entries[2]
    # scope all: the committed manifest, byte for byte
    assert wmanifest.build_manifest(new, None) == MANIFEST_NEW
    # empty prefix matches everything: recreation reproduces the manifest
    assert wmanifest.build_manifest(new, "") == MANIFEST_NEW
    # system32 scope: explorer.exe and SysWOW64 excluded, sorted, deduped
    assert (
        wmanifest.build_manifest(new, wmanifest.SYSTEM32_PREFIX) == "ntdll.pdb,G1,1\nx.pdb,G2,1\n"
    )
    # prefixes are case/slash-insensitive
    assert wmanifest.build_manifest(new, "\\Windows\\System32\\DRIVERS") == "x.pdb,G2,1\n"
    # builds without files.json only support scope all
    try:
        wmanifest.build_manifest(old, wmanifest.SYSTEM32_PREFIX)
        raise AssertionError("expected SystemExit for pre-path-data build")
    except SystemExit as e:
        assert "predates path data" in str(e), str(e)
    print("test_build_manifest OK")


def run_cli(args, fake_bin=None, record_dir=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = CLI_SRC
    # without a fake bin dir, hide any real pdblister the machine may have
    env["PATH"] = fake_bin + os.pathsep + env["PATH"] if fake_bin else os.devnull
    env.pop("WINSYMS_PDBLISTER", None)
    if record_dir:
        env["RECORD_DIR"] = record_dir
    return subprocess.run(
        [sys.executable, "-m", "winsyms"] + args,
        capture_output=True,
        text=True,
        env=env,
    )


def make_fake_pdblister(bin_dir):
    """A pdblister stand-in that records its argv and the staged manifest."""
    os.makedirs(bin_dir, exist_ok=True)
    path = os.path.join(bin_dir, "pdblister")
    with open(path, "w") as f:
        f.write('#!/bin/sh\necho "$@" > "$RECORD_DIR/argv"\ncp manifest "$RECORD_DIR/manifest"\n')
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
    return bin_dir


def check_get(tmp, index_file):
    fake_bin = make_fake_pdblister(os.path.join(tmp, "bin"))
    record = os.path.join(tmp, "record")
    os.makedirs(record)
    out_dir = os.path.join(tmp, "syms")

    # end-to-end: scope filter + pdblister invocation
    res = run_cli(
        [
            "get",
            "26100.1297",
            "--arch",
            "amd64",
            "--scope",
            "system32",
            "--index",
            index_file,
            "--out",
            out_dir,
            "--server",
            "https://sym.example/download",
        ],
        fake_bin=fake_bin,
        record_dir=record,
    )
    assert res.returncode == 0, res.stderr
    argv = open(os.path.join(record, "argv")).read().strip()
    assert argv == f"download SRV*{out_dir}*https://sym.example/download", argv
    staged = open(os.path.join(record, "manifest")).read()
    assert staged == "ntdll.pdb,G1,1\nx.pdb,G2,1\n", staged

    # ambiguous query: list candidates, exit non-zero
    res = run_cli(
        ["get", "26100.1297", "--index", index_file],
        fake_bin=fake_bin,
        record_dir=record,
    )
    assert res.returncode != 0
    assert (
        "matches 2 builds" in res.stderr and UUID_NEW in res.stderr and UUID_NEW_X86 in res.stderr
    ), res.stderr

    # --manifest-only: writes the manifest, needs no pdblister
    manifest_out = os.path.join(tmp, "m")
    res = run_cli(
        [
            "get",
            UUID_OLD,
            "--index",
            index_file,
            "--manifest-only",
            "--out",
            manifest_out,
        ]
    )
    assert res.returncode == 0, res.stderr
    assert open(manifest_out).read() == MANIFEST_OLD

    # pre-path-data build with a scope: clear error
    res = run_cli(["get", UUID_OLD, "--index", index_file, "--scope", "system32"])
    assert res.returncode != 0
    assert "predates path data" in res.stderr, res.stderr

    # no pdblister anywhere: install instructions
    res = run_cli(["get", UUID_OLD, "--index", index_file, "--out", out_dir])
    assert res.returncode != 0
    assert "cargo install" in res.stderr, res.stderr

    # list renders both matches with a PATHS column
    res = run_cli(["list", "26100.1297", "--index", index_file])
    assert res.returncode == 0, res.stderr
    assert UUID_NEW in res.stdout and UUID_NEW_X86 in res.stdout
    print("test_get OK")


def test_cli_e2e():
    with tempfile.TemporaryDirectory() as tmp:
        fixtures = os.path.join(tmp, "fixtures")
        os.makedirs(fixtures)
        handler = partial(SimpleHTTPRequestHandler, directory=fixtures)
        server = HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            base_url = f"http://127.0.0.1:{server.server_port}"
            entries = make_fixtures(fixtures, base_url)
            check_resolve(entries)
            check_build_manifest(entries)
            check_get(tmp, os.path.join(fixtures, "index.json"))
        finally:
            server.shutdown()
