# WindowsSymbolsByVersion

[![License: MIT](https://img.shields.io/github/license/ErezAmihud/WindowsSymbolsByVersion)](LICENSE)

Get the debug symbols for any Windows build by its version, build number, or
uuid — no access to that installation's actual files required.

That matters most on **airgapped machines**: there's no internet to look up
which PDBs a build needs, and normally you'd have to run a symbol tool
against the machine's actual files to find out. This repo already has that
mapping, computed ahead of time from public Windows builds.

## Get symbols

The easiest way is the `winsyms` CLI:

```console
$ pip install winsyms
$ cargo install --git https://github.com/ErezAmihud/pdblister  # does the actual downloading
$ winsyms get 26100.1297 --scope system32
```

It resolves your build (by version, uuid, or title), fetches the manifest
scoped to the paths you asked for, and runs
[pdblister](https://github.com/ErezAmihud/pdblister) for you. See
[cli/README.md](cli/README.md) for full usage.

## Or, do it manually

Every build's manifest is committed under [`manifests/`](manifests/) (browse
by uuid, or find the right one on the
[website](https://erezamihud.github.io/WindowsSymbolsByVersion/)):

```console
$ symchk /im manifest.txt /s SRV*C:\MySymbols*http://msdl.microsoft.com/download/symbols
```

A manifest lists **every** dll/exe in that build's install image — most
aren't public, so expect some symbols to be missing. For a build released in
the last day or so, check the website: it can take up to a day after release
on uupdump for a build to appear here.

Only x86/amd64, en-us, non-insider/preview/cumulative-update builds are
processed — arm64 and other languages aren't covered.

A machine-readable index of every processed build is at
[index.json](https://erezamihud.github.io/WindowsSymbolsByVersion/index.json).

## How it works

Each build is pulled from [uupdump.net](https://uupdump.net), converted to an
ISO, and its `install.wim`/`boot.wim` are parsed for every PE file's PDB/GUID
— fully automated on GitHub Actions. See [ARCHITECTURE.md](ARCHITECTURE.md)
for the full pipeline.

## Contributing

The pipeline works today via uupdump.net. If you know a faster or more
reliable way to generate these manifests, contributions are welcome — see
[ARCHITECTURE.md](ARCHITECTURE.md#alternatives-considered) for what's been
considered.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/erezamihud)
