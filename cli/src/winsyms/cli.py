"""winsyms - download the public PDB symbols of a specific Windows release."""

import argparse
import sys

from winsyms import __version__, index, manifest, pdblister

DEFAULT_SERVER = "https://msdl.microsoft.com/download/symbols"


def _add_index_args(parser):
    parser.add_argument(
        "--index",
        metavar="FILE",
        help="use a local index.json instead of downloading (airgap)",
    )
    parser.add_argument(
        "--arch", help="only consider builds of this architecture (e.g. amd64, x86)"
    )


def _print_entries(entries, file=sys.stdout):
    print(f"{'BUILD':<16} {'ARCH':<6} {'PATHS':<5} {'UUID':<36} TITLE", file=file)
    for e in sorted(entries, key=lambda e: (e["build"], e["arch"])):
        paths = "yes" if "files" in e else "no"
        print(
            f"{e['build']:<16} {e['arch']:<6} {paths:<5} {e['uuid']:<36} {e['title']}",
            file=file,
        )


def _resolve_one(args):
    entries = index.load_index(args.index)
    matches = index.resolve(entries, args.query, args.arch)
    if not matches:
        raise SystemExit(f"error: no build matches {args.query!r}; try `winsyms list`")
    if len(matches) > 1:
        _print_entries(matches, file=sys.stderr)
        raise SystemExit(
            f"error: {args.query!r} matches {len(matches)} builds; narrow with --arch, the full build number or the uuid"
        )
    return matches[0]


def cmd_update(args):
    entries = index.load_index(force_refresh=True)
    print(f"index refreshed: {len(entries)} builds")


def cmd_list(args):
    entries = index.load_index(args.index)
    if args.query:
        entries = index.resolve(entries, args.query, args.arch)
    elif args.arch:
        entries = [e for e in entries if e["arch"] == args.arch]
    if not entries:
        raise SystemExit(f"error: no build matches {args.query!r}")
    _print_entries(entries)


def cmd_get(args):
    if args.path_prefix is not None:
        prefix = args.path_prefix
    elif args.scope == "system32":
        prefix = manifest.SYSTEM32_PREFIX
    else:
        prefix = None

    entry = _resolve_one(args)
    print(
        f"selected: {entry['title']} [{entry['arch']}] ({entry['uuid']})",
        file=sys.stderr,
    )
    text = manifest.build_manifest(entry, prefix).replace("\r\n", "\n")
    if not text:
        raise SystemExit(f"error: no pdb entries match path prefix {prefix!r} in this build")

    if args.manifest_only:
        out_file = args.out or "manifest"
        with open(out_file, "w") as f:
            f.write(text)
        print(f"wrote {len(text.splitlines())} manifest lines to {out_file}")
        return

    binary = pdblister.find_pdblister(args.pdblister)
    out_dir = pdblister.run_download(binary, text, args.out or "symbols", args.server)
    print(f"symbols downloaded to {out_dir}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="winsyms",
        description="Download the public PDB symbols of a specific Windows release. "
        "Data comes from the WindowsSymbolsByVersion project; the actual "
        "symbol download is done by the external pdblister tool.",
    )
    parser.add_argument("--version", action="version", version=f"winsyms {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_update = sub.add_parser("update", help="force-refresh the cached build index")
    p_update.set_defaults(func=cmd_update)

    p_list = sub.add_parser("list", help="list known builds, optionally filtered")
    p_list.add_argument("query", nargs="?", help="uuid, build number or title substring")
    _add_index_args(p_list)
    p_list.set_defaults(func=cmd_list)

    p_get = sub.add_parser("get", help="download the symbols of one build")
    p_get.add_argument("query", help="uuid, build number (e.g. 26100.1297) or title substring")
    p_get.add_argument(
        "--scope",
        choices=["all", "system32"],
        default="all",
        help="which binaries to cover (default: all)",
    )
    p_get.add_argument(
        "--path-prefix",
        metavar="P",
        help="cover only binaries under this path inside the image (overrides --scope)",
    )
    p_get.add_argument(
        "--out",
        metavar="PATH",
        help="symbol output directory (default: ./symbols); with --manifest-only, the manifest file path (default: ./manifest)",
    )
    p_get.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help=f"symbol server URL (default: {DEFAULT_SERVER})",
    )
    p_get.add_argument(
        "--manifest-only",
        action="store_true",
        help="only write the manifest file, do not run pdblister (airgap: fetch here, download inside)",
    )
    p_get.add_argument(
        "--pdblister",
        metavar="PATH",
        help="pdblister binary (default: $WINSYMS_PDBLISTER or PATH lookup)",
    )
    _add_index_args(p_get)
    p_get.set_defaults(func=cmd_get)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        raise SystemExit(130)


if __name__ == "__main__":
    main()
