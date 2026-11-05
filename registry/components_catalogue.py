# Copyright The Phorepoc Authors
# SPDX-License-Identifier: Apache-2.0

"""components_catalogue -- Catalogue's components (merged into core's registry when this repository is a layer:
PHOREPOC_ADAPTATIONS=<board adaptations>:<path to catalogue>, see the pdk's tools/emitter/paths.py). Paths are relative
to the merged OS tree.

  catalogue          the Catalogue app (phestore.exe, "Catalogue" in the launcher) -- the download app's UI
  catalogue_get      pheget.exe, the same engine as a command line (indexes -> download -> SHA-256 -> install)
  catalogue_gettest  the engine's software-source tests (a test, not in an image)

Build:  phe component resources catalogue && phe component build -arch arm catalogue      (x32: without -arch)
Package: python3 $PHOREPOC_PDK/tools/make_sis.py catalogue --arm --unsigned   (recipes/sis.sh does this with the licence files)

The images keep the file names the app has always had (phestore.exe, pheget.exe) and its UIDs, so an image built with
this layer is the same program as before, and the SIS upgrades or replaces it.
"""
import os

from paths import OS_ROOT

_SRC = os.path.join(OS_ROOT, "src", "catalogue")

COMPONENTS = {
    "catalogue": dict(mmp=os.path.join(_SRC, "app", "phestore.mmp"), rom="phestore.exe",
                      rom_data=["resource\apps\phestore_icon.mbm=" + os.path.join(_SRC, "app", "data", "phestore_icon.mbm")]),
    "catalogue_get": dict(mmp=os.path.join(_SRC, "engine", "pheget.mmp"), rom="pheget.exe"),
    "catalogue_gettest": dict(mmp=os.path.join(_SRC, "tests", "phegettest.mmp"), rom="phegettest.exe", test=True),
}
