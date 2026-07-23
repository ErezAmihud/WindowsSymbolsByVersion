# WindowsSymbolsByVersion

![builds analyzed](https://img.shields.io/endpoint?url=https://erezamihud.github.io/WindowsSymbolsByVersion/badge.json)

Creation of a mapping between windows version to public pdb symbols. It is useful for airgapped networks where you can't get any information out.

## Install the CLI

The easiest way to use this repo is the `winsyms` CLI:

```console
$ pip install winsyms
$ cargo install --git https://github.com/ErezAmihud/pdblister   # does the actual downloading
$ winsyms get 26100.1297 --scope system32
```

It resolves a build (by build number, uuid or title), recreates a manifest
scoped to the paths you care about (e.g. only `Windows/System32`) and runs
pdblister for you. `--manifest-only` covers the airgap flow. See
[cli/README.md](cli/README.md) for details.
The mapping is between a windows version to a symbol manifest, which you can convert to symbols using `symchk /im manifest.txt /s SRV*C:\MySymbols*http://msdl.microsoft.com/download/symbols`.
**A faster way** is using [pdblister](https://github.com/microsoft/pdblister) by download and rename the manifest file to `manifest` and run `pdblister download SRV*C:\Symbols*https://msdl.microsoft.com/download/symbols`
The manifests can be found in the [website](https://erezamihud.github.io/WindowsSymbolsByVersion/) or in the repo (by uuid).
NOTE the manifest contains the debug symbols for **every** dll and exe in the iso, meaning a lot of them are probably not public. Expect some symbols to not be found.
If you want the **latest** version, check this site after 1 day the release is on uupdump.

## Method

I am using uup files from uupdump.net to create iso for each windows version and then parse it's install.wim and boot.wim to get all the dll's. If any symbol version that is here is not working let me know.
Read more in the website, or see [ARCHITECTURE.md](ARCHITECTURE.md) for how the pipeline works.

There is also a machine-readable index of all versions at
[index.json](https://erezamihud.github.io/WindowsSymbolsByVersion/index.json) if you want to script the lookup.

## Help is appriciated

If any1 have a faster method that is reliable to generate symbol manifests, feel free to contribute.

I saw that [mas](https://massgrave.dev/genuine-installation-media) has some ways to get windows installation media, and [files.rg](https://files.rg-adguard.net/) can actually supply them, but I am not sure it is actually that important - as the repo currently works.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/erezamihud)
