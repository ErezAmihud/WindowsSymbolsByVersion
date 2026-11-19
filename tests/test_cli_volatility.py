"""Tests for `winsyms volatility` (cli/src/winsyms/volatility.py).

The download (pdblister) and conversion (volatility3) steps are injected, so
these run with no network, no pdblister and no volatility3 installed.

Run from the repo root: pytest tests/test_cli_volatility.py
"""

import importlib.util
import os
import subprocess
import sys

import pytest
from winsyms import volatility as wvol

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_SRC = os.path.join(REPO_ROOT, "cli", "src")

KERNEL = "ntkrnlmp.pdb,B6CDAA3A3EF13C3B2799115B0470342B1,1\n"
MANIFEST = (
    ",0806F2FCC9034CE2A4D2D33ED1D422171,1\n"  # nameless entries exist in real manifests
    + KERNEL
    + "ntdll.pdb,E3C16524B6DB48109A895BFE84669AC11,1\n"
    + "TCPIP.pdb,256E595DB835F1FABE3DC077E042F3191,1\n"
    + "win32kfull.pdb,0123456789ABCDEF0123456789ABCDEF1A,1\n"
)


def refs_by_name(refs):
    return {r.name.lower(): r for r in refs}


def test_select_keeps_only_volatility_pdbs():
    refs = wvol.select(MANIFEST)
    assert sorted(r.name.lower() for r in refs) == ["ntkrnlmp.pdb", "tcpip.pdb", "win32kfull.pdb"]


def test_select_with_explicit_names_is_case_insensitive():
    refs = wvol.select(MANIFEST, names=["NTDLL.PDB"])
    assert [r.name for r in refs] == ["ntdll.pdb"]


def test_select_dedups_repeated_lines():
    assert len(wvol.select(KERNEL + KERNEL)) == 1


def test_isf_path_matches_volatility_layout():
    # Volatility looks up windows/<pdb>/<GUID>-<age>.json.xz with a *decimal* age,
    # while the manifest (symbol-server style) appends the age in hex.
    refs = refs_by_name(wvol.select(MANIFEST))
    assert refs["ntkrnlmp.pdb"].isf_relpath() == os.path.join(
        "windows", "ntkrnlmp.pdb", "B6CDAA3A3EF13C3B2799115B0470342B-1.json.xz"
    )
    assert refs["win32kfull.pdb"].isf_relpath() == os.path.join(
        "windows", "win32kfull.pdb", "0123456789ABCDEF0123456789ABCDEF-26.json.xz"
    )


class FakeDownload:
    """Writes a dummy PDB into the symbol store for every manifest line,
    except names listed in `unpublished` (Microsoft doesn't publish every PDB)."""

    def __init__(self, unpublished=()):
        self.unpublished = set(unpublished)
        self.manifests = []

    def __call__(self, manifest_text, store_dir):
        self.manifests.append(manifest_text)
        for line in manifest_text.splitlines():
            name, key, _ = line.split(",")
            if name in self.unpublished:
                continue
            path = os.path.join(store_dir, name, key, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(f"pdb {name}")


class FakeConvert:
    def __init__(self, fail=()):
        self.fail = set(fail)
        self.calls = []

    def __call__(self, pdb_path, out_path, pdb_name):
        self.calls.append(pdb_name)
        if pdb_name in self.fail:
            raise ValueError("corrupt pdb")
        with open(pdb_path) as f:
            src = f.read()
        with open(out_path, "w") as f:
            f.write(f"isf of {src}")


def test_build_pack_converts_every_published_pdb(tmp_path):
    refs = wvol.select(MANIFEST)
    download, convert = FakeDownload(unpublished={"win32kfull.pdb"}), FakeConvert()

    report = wvol.build_pack(refs, str(tmp_path), download, convert)

    by_name = refs_by_name(refs)
    kernel_isf = tmp_path / by_name["ntkrnlmp.pdb"].isf_relpath()
    assert kernel_isf.read_text() == "isf of pdb ntkrnlmp.pdb"
    assert (tmp_path / by_name["tcpip.pdb"].isf_relpath()).exists()
    assert not (tmp_path / by_name["win32kfull.pdb"].isf_relpath()).exists()
    assert sorted(r.name for r in report.converted) == ["TCPIP.pdb", "ntkrnlmp.pdb"]
    assert [r.name for r in report.missing] == ["win32kfull.pdb"]
    assert report.failed == []


def test_build_pack_skips_isf_files_that_already_exist(tmp_path):
    refs = wvol.select(MANIFEST)
    wvol.build_pack(refs, str(tmp_path), FakeDownload(), FakeConvert())

    download, convert = FakeDownload(), FakeConvert()
    report = wvol.build_pack(refs, str(tmp_path), download, convert)

    assert download.manifests == [] and convert.calls == []
    assert len(report.existing) == 3 and report.converted == []


def test_build_pack_downloads_only_what_is_missing(tmp_path):
    refs = refs_by_name(wvol.select(MANIFEST))
    wvol.build_pack([refs["ntkrnlmp.pdb"]], str(tmp_path), FakeDownload(), FakeConvert())

    download = FakeDownload()
    wvol.build_pack(list(refs.values()), str(tmp_path), download, FakeConvert())

    assert len(download.manifests) == 1
    assert "ntkrnlmp.pdb" not in download.manifests[0]


def test_build_pack_keeps_going_when_one_conversion_fails(tmp_path):
    refs = wvol.select(MANIFEST)
    report = wvol.build_pack(refs, str(tmp_path), FakeDownload(), FakeConvert(fail={"TCPIP.pdb"}))

    assert [r.name for r, _ in report.failed] == ["TCPIP.pdb"]
    assert "corrupt pdb" in str(report.failed[0][1])
    assert len(report.converted) == 2
    # no half-written ISF left behind for the failed one
    assert not (tmp_path / refs_by_name(refs)["tcpip.pdb"].isf_relpath()).exists()


@pytest.mark.skipif(
    importlib.util.find_spec("volatility3") is not None,
    reason="volatility3 is installed, so the missing-dependency path can't be exercised",
)
def test_cli_explains_how_to_install_volatility3(tmp_path):
    env = dict(os.environ, PYTHONPATH=CLI_SRC)
    res = subprocess.run(
        [sys.executable, "-m", "winsyms", "volatility", "26100.1297", "--out", str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode != 0
    assert "winsyms[volatility]" in res.stderr, res.stderr
