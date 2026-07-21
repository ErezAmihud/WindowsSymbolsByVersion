"""mkdocs-gen-files script: render the version index from builds_state.json.

Generates:
  index.md   - the website landing page, grouped by product and sorted by build
  index.json - machine-readable mapping for scripting:
               [{uuid, title, build, arch, manifest, files?}, ...]
               `files` (the per-build path data used by the winsyms CLI for
               scope filtering) is only present for builds processed after
               the pipeline started recording binary paths.
"""

import json
import os.path

import mkdocs_gen_files

BLOB_BASE = "https://github.com/ErezAmihud/WindowsSymbolsByVersion/blob/main/manifests"
RAW_BASE = "https://raw.githubusercontent.com/ErezAmihud/WindowsSymbolsByVersion/main/manifests"

GROUPS = ["Windows 11", "Windows 10", "Windows Server", "Azure Stack HCI", "Other"]

HEADER = """\
# Windows Versions

A mapping of Windows version to a public-symbols manifest. Use your browser's
search (Ctrl+F) to find a build, or go to [uupdump](https://uupdump.net/), open
the download page of the version you want, take the `id` from the url bar and
download `manifests/<id>.manifest` from the
[repo](https://github.com/ErezAmihud/WindowsSymbolsByVersion).

A machine-readable version of this page is available at [index.json](index.json).

NOTE - many pdbs listed in a manifest are not on the Microsoft symbol server,
that is expected: the manifest lists every pdb referenced by the windows image.
"""


def group_of(title: str) -> str:
    lowered = title.lower()
    for group in GROUPS[:-1]:
        if group.lower() in lowered:
            return group
    return "Other"


def build_sort_key(build: str):
    try:
        return tuple(int(part) for part in build.split("."))
    except ValueError:
        return (0,)


def main():
    with open("builds_state.json") as f:
        state = json.load(f)
    # done builds without a manifest on disk were purged (2026-07: everything
    # before per-build path data); they stay in the state so the pipeline
    # never reprocesses them, but are not listed on the site.
    done = [
        {
            "uuid": uuid,
            "title": info["title"],
            "build": info["build"],
            "arch": info["arch"],
        }
        for uuid, info in state["builds"].items()
        if info["status"] == "done" and os.path.exists(f"manifests/{uuid}.manifest")
    ]

    with mkdocs_gen_files.open("index.md", "w") as f:
        f.write(HEADER)
        for group in GROUPS:
            entries = sorted(
                (e for e in done if group_of(e["title"]) == group),
                key=lambda e: (build_sort_key(e["build"]), e["arch"]),
                reverse=True,
            )
            if not entries:
                continue
            f.write(f"\n## {group}\n\n")
            f.write("| Version | Build | Arch | Manifest |\n|---|---|---|---|\n")
            for e in entries:
                f.write(
                    f"| {e['title']} | {e['build']} | {e['arch']} "
                    f"| [download]({BLOB_BASE}/{e['uuid']}.manifest) |\n"
                )

    def index_entry(e):
        entry = {**e, "manifest": f"{RAW_BASE}/{e['uuid']}.manifest"}
        if os.path.exists(f"manifests/{e['uuid']}.files.json"):
            entry["files"] = f"{RAW_BASE}/{e['uuid']}.files.json"
        return entry

    with mkdocs_gen_files.open("index.json", "w") as f:
        json.dump([index_entry(e) for e in done], f, indent=1)


main()
