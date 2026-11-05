#!/usr/bin/env bash
# Copyright The Phorepoc Authors
# SPDX-License-Identifier: Apache-2.0
#
# sis.sh -- the pdk's package.yml runs it after the components: the Catalogue SIS for PHOREPOC_ARCH
# ($PHOREPOC_BUILD/sis/catalogue-<arch>.sis).
#
#   ARM  (older Nokia Symbian^3 phones and Phorepoc phones): --arm = the ARM image, targeted at the Symbian^3 platform UID.
#   x32  (Phorepoc PC images built without Catalogue).
#
# The package is unsigned (like the other Phorepoc packages): Phorepoc installs it as it is; a stock phone needs it signed
# or its installation check lifted (README.md, "Older Symbian phones").
#
# Needs the components built first:  phe component resources catalogue ; phe component build [-arch arm] catalogue
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
ARCH=${PHOREPOC_ARCH:-arm}
case "$ARCH" in arm) AFL=--arm;; x32) AFL=;; *) echo "ARCH must be arm or x32 (got '$ARCH')"; exit 1;; esac
: "${PHOREPOC_PDK:?set PHOREPOC_PDK}" "${PHOREPOC_BUILD:?set PHOREPOC_BUILD}"
# our own code is Apache-2.0: its text and the NOTICE travel with the package
LIC=
for f in "$HERE/LICENSES/Apache-2.0.txt" "$HERE/NOTICE"; do
  b=$(basename "$f"); case $b in *.txt) ;; *) b=$b.txt;; esac
  LIC="$LIC --file $f=!:/resource/catalogue/$b"
done
# shellcheck disable=SC2086
python3 "$PHOREPOC_PDK/tools/make_sis.py" catalogue $AFL --unsigned --version "${PHOREPOC_PACKAGE_VERSION:-1.0.0}" \
  --name "Catalogue" --vendor Phorepoc $LIC \
  --out "$PHOREPOC_BUILD/sis/catalogue-$ARCH.sis"
