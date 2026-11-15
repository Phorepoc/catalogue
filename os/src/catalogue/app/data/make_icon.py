# Copyright The Phorepoc Authors
# SPDX-License-Identifier: AGPL-3.0-only
"""make_icon.py -- renders the Catalogue launcher icon (download glyph on the "store" accent) to the Etesian design language
(https://language.etesian-design.com) with core's icon generator (core os/tools/icongen; set PHOREPOC_CORE to the core
checkout). Writes phestore_icon.svg (the source), phestore_icon_tiny.svg (its SVG-Tiny form, which pdk tools/app_icon_mif.py
turns into phestore_icon.mif, the registration's icon_file), phestore_icon.mbm and phestore_icon_preview.png.
Run: PHOREPOC_CORE=<core> py make_icon.py (needs Pillow)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.environ.get("PHOREPOC_CORE", os.path.join(HERE, "..", "..", "..", "..", "..", "..", "core")),
                                "os", "tools", "icongen"))
import icongen  # noqa: E402
import mbm  # noqa: E402

if __name__ == "__main__":
    mbm.make_app_icon(HERE, "phestore", "download", icongen.ACCENTS["store"])
