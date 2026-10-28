#!/usr/bin/env bash
# Fill the prebuilt-variant PKGBUILD from a built release asset.
# Usage: generate_arch_bin_pkgbuild.sh <tag> <asset-directory>
#   <tag>             release tag, for example v4.0.1
#   <asset-directory> directory containing wayground-pro-automator-*.pkg.tar.zst
# Writes <asset-directory>/PKGBUILD and <asset-directory>/.SRCINFO.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:?usage: $0 <tag> <asset-directory>}"
DIR="${2:?usage: $0 <tag> <asset-directory>}"

cd "$DIR"
ASSET="$(ls wayground-pro-automator-*.pkg.tar.zst)"
VERSION="$(echo "$ASSET" | sed -E 's/^wayground-pro-automator-(.+)-([0-9]+)-x86_64\.pkg\.tar\.zst$/\1/')"
RELEASE="$(echo "$ASSET" | sed -E 's/^wayground-pro-automator-(.+)-([0-9]+)-x86_64\.pkg\.tar\.zst$/\2/')"
SHA256="$(sha256sum "$ASSET" | awk '{print $1}')"

sed -e "s/__PKGVER__/$VERSION/g" \
    -e "s/__PKGREL__/$RELEASE/g" \
    -e "s/__ASSET__/$ASSET/g" \
    -e "s/__SHA256__/$SHA256/g" \
    -e "s/__TAG__/$TAG/g" \
    "$ROOT/packaging/arch-bin/PKGBUILD" > PKGBUILD

makepkg --printsrcinfo > .SRCINFO

echo "Asset:   $ASSET"
echo "Version: $VERSION-$RELEASE"
echo "SHA256:  $SHA256"
echo "--- PKGBUILD ---"
cat PKGBUILD
echo "--- .SRCINFO ---"
cat .SRCINFO
