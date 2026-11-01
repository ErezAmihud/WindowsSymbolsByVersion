"""Build Volatility 3 symbol tables (ISF) for a Windows build.

Volatility needs an ISF file matching the exact PDB GUID/age of the kernel
(and of tcpip/win32k for some plugins) in the memory image. When it has none,
it downloads the PDB from Microsoft and converts it - impossible on an
airgapped analysis box. Our manifests already list those GUIDs for every
build, so the pack can be built ahead of time on a connected machine.

Download and conversion are injected (`build_pack`) so the logic is testable
without pdblister or volatility3.
"""

import lzma
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

INSTALL_HINT = (
    'volatility3 is required for this command. Install it with: pip install "winsyms[volatility]"'
)

# ntkrnlmp: x64 kernel, ntkrpamp: x86 PAE kernel; tcpip backs windows.netscan,
# win32k* back the desktop/window/clipboard plugins.
VOLATILITY_PDBS = (
    "ntkrnlmp.pdb",
    "ntkrpamp.pdb",
    "tcpip.pdb",
    "win32k.pdb",
    "win32kbase.pdb",
    "win32kfull.pdb",
)


@dataclass(frozen=True)
class PdbRef:
    name: str
    # symbol-server key: 32 hex GUID chars followed by the age in hex
    key: str

    @property
    def guid(self):
        return self.key[:32].upper()

    @property
    def age(self):
        return int(self.key[32:], 16)

    def isf_relpath(self):
        # Volatility's lookup key is <pdb>/<GUID>-<age> with a decimal age
        return os.path.join("windows", self.name, f"{self.guid}-{self.age}.json.xz")

    def store_path(self, store_dir):
        return os.path.join(store_dir, self.name, self.key, self.name)


@dataclass
class Report:
    converted: list = field(default_factory=list)
    existing: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    failed: list = field(default_factory=list)  # (PdbRef, exception)


def select(manifest_text, names=VOLATILITY_PDBS):
    """Return the deduped PdbRefs in manifest_text whose pdb name is in names."""
    wanted = {n.lower() for n in names}
    refs = set()
    for line in manifest_text.splitlines():
        parts = line.strip().split(",")
        if len(parts) < 2 or not parts[0]:
            continue
        name, key = parts[0], parts[1]
        if name.lower() in wanted and len(key) > 32:
            refs.add(PdbRef(name, key))
    return sorted(refs, key=lambda r: (r.name.lower(), r.key))


def build_pack(refs, out_dir, download, convert):
    """Write an ISF file under out_dir for every ref, skipping ones already there.

    download(manifest_text, store_dir) must fetch the PDBs into a symbol-server
    layout; convert(pdb_path, out_path, pdb_name) must write one ISF file.
    """
    report = Report()
    todo = []
    for ref in refs:
        if os.path.exists(os.path.join(out_dir, ref.isf_relpath())):
            report.existing.append(ref)
        else:
            todo.append(ref)
    if not todo:
        return report

    with tempfile.TemporaryDirectory(prefix="winsyms-pdbs-") as store:
        download("".join(f"{r.name},{r.key},1\n" for r in todo), store)
        for ref in todo:
            pdb_path = ref.store_path(store)
            if not os.path.isfile(pdb_path):
                report.missing.append(ref)
                continue
            out_path = os.path.join(out_dir, ref.isf_relpath())
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            # Convert to a temp name so a crash never leaves a truncated ISF that
            # later runs would treat as "already built"
            partial = out_path + ".partial"
            try:
                convert(pdb_path, partial, ref.name)
                os.replace(partial, out_path)
            except Exception as e:  # one bad PDB must not sink the whole pack
                print(f"error: converting {ref.name} ({ref.key}) failed: {e!r}", file=sys.stderr)
                Path(partial).unlink(missing_ok=True)
                report.failed.append((ref, e))
                continue
            report.converted.append(ref)
    return report


def require_volatility():
    """Fail fast, before any download, when volatility3 isn't installed."""
    try:
        import volatility3  # noqa: F401
    except ImportError as e:
        raise SystemExit(f"error: {INSTALL_HINT}") from e


def convert_with_volatility(pdb_path, out_path, pdb_name):
    """Convert one PDB to an xz-compressed ISF file, exactly as volatility3's
    own pdbconv.py does when it downloads a missing symbol table."""
    import json
    from urllib import request

    from volatility3.framework import contexts
    from volatility3.framework.symbols.windows.pdbconv import PdbReader

    location = "file:" + request.pathname2url(os.path.abspath(pdb_path))
    reader = PdbReader(contexts.Context(), location, database_name=pdb_name)
    try:
        data = json.dumps(reader.get_json(), indent=2, sort_keys=True)
    finally:
        # The reader's file layer keeps the PDB open (in its own cloned context);
        # on Windows that blocks deleting the temp symbol store afterwards
        layers = reader.context.layers
        for name in list(layers):
            layers[name].destroy()
    with lzma.open(out_path, "wb") as f:
        f.write(data.encode("latin-1"))
