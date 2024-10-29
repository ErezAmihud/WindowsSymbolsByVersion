# WindowsSymbolsByVersion

Creation of a mapping between windows version to public pdb symbols. It is useful for airgapped networks where you can't get any information out.
The mapping is between a windows version to a symbol manifest, which you can convert to symbols using `symchk /im manifest.txt /s SRV*C:\MySymbols*http://msdl.microsoft.com/download/symbols`.
**A faster way** is using [pdblister](https://github.com/microsoft/pdblister) by download and rename the manifest file to `manifest` and run `pdblister download SRV*C:\Symbols*https://msdl.microsoft.com/download/symbols`
The manifests can be found in the [website](https://erezamihud.github.io/WindowsSymbolsByVersion/) or in the repo (by uuid).
NOTE the manifest contains the debug symbols for **every** dll and exe in the iso, meaning a lot of them are probably not public. Expect some symbols to not be found.
If you want the **latest** version, check this site after 1 day the release is on uupdump.

### Method
I am using uup files from uupdump.net to create iso for each windows version and then parse it's install.wim and boot.wim to get all the dll's. If any symbol version that is here is not working let me know.
Read more in the website.



### Help is appriciated
If any1 have a faster method that is reliable to generate symbol manifests, feel free to contribute.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/erezamihud)
