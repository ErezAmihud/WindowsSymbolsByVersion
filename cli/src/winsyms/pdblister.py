"""Locate and run the external pdblister binary (never auto-downloaded)."""

import os
import shutil
import subprocess
import tempfile

INSTALL_HINT = (
    "pdblister was not found. Install it with:\n"
    "    cargo install --git https://github.com/ErezAmihud/pdblister\n"
    "or point at an existing binary with --pdblister PATH or the "
    "WINSYMS_PDBLISTER environment variable."
)


def find_pdblister(explicit=None):
    """Resolve the pdblister binary: --pdblister flag, then WINSYMS_PDBLISTER,
    then PATH. Raises with install instructions when none is found."""
    for candidate in (explicit, os.environ.get("WINSYMS_PDBLISTER")):
        if candidate:
            if not os.path.isfile(candidate):
                raise SystemExit(f"error: pdblister binary not found at {candidate}")
            return candidate
    found = shutil.which("pdblister")
    if not found:
        raise SystemExit(f"error: {INSTALL_HINT}")
    return found


def run_download(binary, manifest_text, out_dir, server):
    """Stage manifest_text as `manifest` in a temp cwd and run
    `pdblister download SRV*<out_dir>*<server>` (pdblister reads ./manifest)."""
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "manifest"), "w") as f:
            f.write(manifest_text)
        try:
            subprocess.run([binary, "download", f"SRV*{out_dir}*{server}"], cwd=tmp, check=True)
        except subprocess.CalledProcessError as e:
            raise SystemExit(f"error: pdblister exited with status {e.returncode}") from e
    return out_dir
