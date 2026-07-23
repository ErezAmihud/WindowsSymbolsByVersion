# winsyms

![builds analyzed](https://img.shields.io/endpoint?url=https://erezamihud.github.io/WindowsSymbolsByVersion/badge.json)

Download the public PDB symbols of a **specific Windows release** in one command:

```console
$ pip install winsyms
$ winsyms get 26100.1297 --scope system32
```

Data comes from [WindowsSymbolsByVersion](https://github.com/ErezAmihud/WindowsSymbolsByVersion),
which processes every Windows build published on uupdump and records which
pdb/guid every binary in the image references. New builds appear in the index
daily - no `pip` upgrade needed, the CLI fetches the current index at runtime.

## Prerequisite: pdblister

The actual mass download is done by [pdblister](https://github.com/ErezAmihud/pdblister),
which must be on your `PATH` (or pointed at with `--pdblister PATH` /
`WINSYMS_PDBLISTER`):

```console
$ cargo install --git https://github.com/ErezAmihud/pdblister
```

`winsyms get ... --manifest-only` works without pdblister.

## Usage

```console
$ winsyms list 24H2                 # find builds (uuid, build number or title substring)
$ winsyms get 26100.1297 --arch amd64          # all symbols of that build -> ./symbols
$ winsyms get 26100.1297 --scope system32      # only binaries under Windows/System32
$ winsyms get 26100.1297 --path-prefix windows/system32/drivers/
$ winsyms get 26100.1297 --out D:\Symbols --server https://msdl.microsoft.com/download/symbols
$ winsyms update                    # force-refresh the cached index (cache TTL: 24h)
```

A query can be a uupdump uuid, an exact build number, or a title substring;
ambiguous queries print the candidates so you can narrow with `--arch` or the
uuid.

`--scope system32` (or any `--path-prefix`) needs the build's path data
(`files.json`), which exists for builds processed after path recording was
added to the pipeline. Older builds support `--scope all` only - the CLI
tells you when that is the case.

## Airgapped networks

On the connected side:

```console
$ winsyms get 26100.1297 --manifest-only --out manifest
```

Carry `manifest` (a plain `pdb,guid,1` text file) inside, then run pdblister
against your internal symbol mirror:

```console
$ pdblister download SRV*C:\Symbols*http://symbols.internal/download/symbols
```

or, if the inner network has winsyms and a copy of
[index.json](https://erezamihud.github.io/WindowsSymbolsByVersion/index.json):

```console
$ winsyms get 26100.1297 --index index.json --server http://symbols.internal/download/symbols
```

Note: manifests list **every** pdb the image references; many are not on the
public symbol server. Missing symbols are expected.

## Releasing (maintainers)

Tag `cli-v<version>` (after bumping `pyproject.toml` and
`src/winsyms/__init__.py`) to trigger `.github/workflows/release-cli.yml`,
which publishes to PyPI via trusted publishing. One-time setup: add a
[trusted publisher](https://docs.pypi.org/trusted-publishers/) on PyPI for
the `winsyms` project pointing at this repository and the
`release-cli.yml` workflow.
