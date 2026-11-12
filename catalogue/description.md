Catalogue is the software store of Phorepoc. It reads the Phorepoc index, shows what is there by category, with search
and a list of what you have installed, downloads a package, checks its SHA-256 and installs it. It also lists updates
for what you have installed, Catalogue itself included.

Phorepoc images have Catalogue built in. This package is for an image built without it, and the ARM package also
installs on older Nokia Symbian^3 phones, on one whose installation check is lifted (the package is unsigned and asks
for `AllFiles`) and with a modern TLS installed for the `https://` index. The repository's README has the details.
