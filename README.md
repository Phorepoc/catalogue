# catalogue

Catalogue is the software store of [Phorepoc OS](https://github.com/Phorepoc). It reads the
[index](https://github.com/Phorepoc/index), shows what's there by category, with search and a list of what you've
installed, downloads a package, checks its SHA-256 and installs it. It's how drivers, codecs, browser engines and apps
get onto a Phorepoc phone or PC without being built into the image.

The app (`phestore.exe`, "Catalogue" in the launcher) is custom-drawn with the Etesian design language, over a small
download engine (`pheget`) that you can also use from the command line.

## Releases

Every release has Catalogue as an installable SIS file for each architecture: `catalogue-arm.sis` for phones and
`catalogue-x32.sis` for the PC. The [release workflow](.github/workflows/release.yml) builds them from this repository
with the pdk's `package.yml`.

## Two ways to get it

**Built into an image.** This repository is a layer, like [tls](https://github.com/Phorepoc/tls) or
[webengine](https://github.com/Phorepoc/webengine): it brings an `os/` tree and a `registry/`. Add it to a board's
`REPOS` in `board.conf`, or to `PHOREPOC_ADAPTATIONS` in a local build, and the components below are part of the image.

```sh
PHOREPOC_ADAPTATIONS=<device repositories>:<path to catalogue> phe component resources catalogue
PHOREPOC_ADAPTATIONS=<device repositories>:<path to catalogue> phe component build -arch arm catalogue
```

Leave `-arch arm` out for the PC. The components are:

- `catalogue` is the app, `phestore.exe`.
- `catalogue_get` is the engine as a command line, `pheget.exe`.
- `catalogue_gettest` tests the engine's software sources. It's a test and not part of an image.

**Installed as a package.** The SIS holds the app, its registration and its icon. Install it on an image that was built
without Catalogue, or on an older Nokia Symbian^3 phone (below).

## Older Symbian phones

`catalogue-arm.sis` is an ARM build for the Symbian^3 platform, so it also installs on the older Nokia Symbian^3 phones
that list that platform. It needs nothing of Phorepoc's own on the phone: the app links only libraries that every
Symbian^3 phone has (`euser`, `apparc`, `cone`, `eikcore`, `eikcoctl`, `eikctl`, `eikdlg`, `avkon`, `aknskins`,
`fbscli`, `bitgdi`, `gdi`, `ws32`, `imageconversion`, `efsrv`, `bafl`, `charconv`, `esock`, `http`, `inetprotutil`,
`hash`, `swinstcli`), takes its font from the system, and works without `z:\resource\phorepoc\device.txt` (it then lists
every package built for ARM). There are three things to know.

**Signing.** The app asks for `TrustedUI NetworkServices AllFiles`.

- `NetworkServices` is one every user can grant.
- `TrustedUI` needs a developer certificate.
- `AllFiles` can't be had from a developer certificate or from a self-signed package. Symbian Signed only gives it to
  Certified Signed packages.

`AllFiles` is there because the installer's silent mode answers error -46 to a program without it when the package is
untrusted and holds binaries, and that is every package Catalogue installs. So a stock phone, which checks signatures
and capabilities when it installs, refuses this SIS. It installs on a phone whose installation check has been lifted,
and the package is unsigned, as every Phorepoc package is. Sign it for a phone that needs a signature.

**Secure connections.** Catalogue's index and its downloads are `https://` addresses, and the TLS in an older Symbian
phone stops at TLS 1.0 with a root certificate list that stopped growing years ago, so the connection fails. Put a modern
TLS on the phone first (see [tls](https://github.com/Phorepoc/tls)), or add an index of your own that has `http://`
addresses or local paths on the phone, under Sources in the app (`c:\data\pheget\indexes.txt`).

**Installing.** Catalogue installs with the system's silent installer (`swinstcli`), so each package it installs has to
be one the phone accepts under the rules above. The packages in the index are unsigned too.

## Building

The packages are built by the pdk's `package.yml` in the toolchain's `ghcr.io/phorepoc/base` image, on top of the
published core layer. To build by hand, check out core and the [pdk](https://github.com/Phorepoc/pdk) next to this
repository and run `phe source export -a` once. Then build the components as above and package them:

```sh
PHOREPOC_ARCH=arm PHOREPOC_PDK=<pdk> PHOREPOC_BUILD=<build> bash recipes/sis.sh      # build/sis/catalogue-arm.sis
```

## What's in here

- `os/src/catalogue/app/` is the app: the views (`pheui`), the icons (`pheicons`), the worker thread, the resources and
  the launcher icon in `data/`.
- `os/src/catalogue/engine/` is the download engine: indexes, downloads, SHA-256, the silent install, and a small JSON
  reader. `pheget.cpp` wraps it as a command line.
- `os/src/catalogue/tests/` tests the engine's software sources.
- `registry/components_catalogue.py` registers the components with core.
- `recipes/sis.sh` writes the SIS files. `package.conf` tells `package.yml` what to build.

Catalogue started in [core](https://github.com/Phorepoc/core), and this repository keeps that history.
