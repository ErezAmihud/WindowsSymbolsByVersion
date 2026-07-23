# WindowsSymbolsByVersion

Download the debug symbols for any Windows build using just its version, build number, or uuid - no access to that installation's actual files needed.
Especially helpful for airgapped machines where you can't get anything out to the internet.

## Install the CLI

The easiest way to use this repo is the `winsyms` CLI:

```console
$ pip install winsyms
$ cargo install --git https://github.com/ErezAmihud/pdblister   # does the actual downloading
$ winsyms get 26100.1297 --scope system32
```

It resolves a build (by build number, uuid or title), recreates a manifest
scoped to the paths you care about (via flag - e.g. only `Windows/System32`) and runs
pdblister for you. See [cli/README.md](cli/README.md) for details.


The manifests are also provided as it in the "manifests" directory so you can see the mapping between a windows version to a symbol manifest, which you can convert to symbols using `symchk /im manifest.txt /s SRV*C:\MySymbols*http://msdl.microsoft.com/download/symbols`.
The manifests can be found in the [website](https://erezamihud.github.io/WindowsSymbolsByVersion/) or in the repo (by uuid).
NOTE the manifest contains the debug symbols for **every** dll and exe in the iso, meaning a lot of them are probably not public. Expect some symbols to not be found.
If you want the **latest** version, check this site after 1 day the release is on uupdump.

## Method

I am using uup files from uupdump.net to create iso for each windows version and then parse it's install.wim and boot.wim to get all the dll's. If any symbol version that is here is not working let me know.
Read more in the website, or see [ARCHITECTURE.md](ARCHITECTURE.md) for how the pipeline works.

There is also a machine-readable index of all versions at
[index.json](https://erezamihud.github.io/WindowsSymbolsByVersion/index.json) if you want to script the lookup.

## Releasing (maintainers)

Tag `cli-v<version>` (after bumping `pyproject.toml` and
`src/winsyms/__init__.py`) to trigger `.github/workflows/release-cli.yml`,
which publishes to PyPI via trusted publishing. One-time setup: add a
[trusted publisher](https://docs.pypi.org/trusted-publishers/) on PyPI for
the `winsyms` project pointing at this repository and the
`release-cli.yml` workflow.

## Help is appriciated

If any1 have a faster method that is reliable to generate symbol manifests, feel free to contribute.

I saw that [mas](https://massgrave.dev/genuine-installation-media) has some ways to get windows installation media, and [files.rg](https://files.rg-adguard.net/) can actually supply them, but I am not sure it is actually that important - as the repo currently works.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/erezamihud)
