#!/bin/sh
# Build the model and publish the exports as a GitHub release.
# Usage: tools/release.sh v0.1 "Notes de version"
set -e
TAG=${1:?tag, e.g. v0.1}
NOTES=${2:-"Cassette ferrotype $TAG"}
FC=/Applications/FreeCAD.app/Contents/Resources/bin/python
cd "$(dirname "$0")/.."
$FC cad/build_cassette.py
# the tag goes on the commit that was built (not on the default branch)
gh release create "$TAG" --target "$(git rev-parse HEAD)" --title "Cassette ferrotype $TAG" --notes "$NOTES" \
  exports/piece1_interface.stl exports/piece2_cadre_verre.stl exports/piece3_couvercle.stl \
  exports/ressort_lames.stl exports/glissiere_verrou.stl exports/capot_verrou.stl \
  exports/piece3_couvercle_pour_v0.1.stl \
  exports/*.step exports/cassette_ferrotype.FCStd
