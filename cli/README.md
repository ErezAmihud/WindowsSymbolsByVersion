# winsyms

[![PyPI](https://img.shields.io/pypi/v/winsyms.svg)](https://pypi.org/project/winsyms/)
[![Python](https://img.shields.io/pypi/pyversions/winsyms.svg)](https://pypi.org/project/winsyms/)
[![License: MIT](https://img.shields.io/pypi/l/winsyms.svg)](https://github.com/ErezAmihud/WindowsSymbolsByVersion/blob/main/LICENSE)
![Builds analyzed](https://img.shields.io/endpoint?url=https://erezamihud.github.io/WindowsSymbolsByVersion/badge.json)

Download the public PDB symbols for a specific Windows release, in one
command:

```console
$ pip install winsyms
$ winsyms get 26100.1297 --scope system32
```

Data comes from
[WindowsSymbolsByVersion](https://github.com/ErezAmihud/WindowsSymbolsByVersion),
which processes every Windows build published on uupdump.net and records the
pdb/guid for every binary in its install image. New builds show up
automatically — the CLI fetches the current index at runtime, no `pip`
upgrade needed.

## Requirements

Python 3.9+. The actual download is done by
[pdblister](https://github.com/ErezAmihud/pdblister), which must be on your
`PATH` (or pointed to via `--pdblister PATH` / `WINSYMS_PDBLISTER`):

```console
$ cargo install --git https://github.com/ErezAmihud/pdblister
```

`winsyms get ... --manifest-only` works without pdblister installed.

## Usage

```console
$ winsyms list 24H2                    # find builds by uuid, build number, or title substring
$ winsyms get 26100.1297 --arch amd64  # all symbols for a build -> ./symbols
$ winsyms get 26100.1297 --scope system32          # only binaries under Windows/System32
$ winsyms get 26100.1297 --path-prefix windows/system32/drivers/
```

Run `winsyms get --help` for the full flag reference (output dir, symbol
server, cache TTL, and more).

## Volatility 3

`winsyms volatility` builds the
[ISF symbol tables](https://volatility3.readthedocs.io/en/latest/symbol-tables.html)
Volatility 3 needs for a build, so memory images can be analysed on a
machine with no internet:

```console
$ pip install "winsyms[volatility]"
$ winsyms volatility 26100.1297 --out vol-symbols   # on a connected machine
$ vol -s vol-symbols -f memory.raw windows.info     # anywhere, offline
```

By default it converts `ntkrnlmp.pdb`, `ntkrpamp.pdb`, `tcpip.pdb`,
`win32k.pdb`, `win32kbase.pdb` and `win32kfull.pdb`; pick others with
`--pdb NAME` (repeatable). Tables already in `--out` are skipped, so rerunning
for more builds extends the same directory.

## License

MIT. See [LICENSE](https://github.com/ErezAmihud/WindowsSymbolsByVersion/blob/main/LICENSE).
