#!/usr/bin/env bash
# Build the self-contained AppImage from the standalone PyInstaller binary.
#
# Usage: scripts/build_appimage.sh [path/to/WaygroundAutomator]
#   With no argument the binary is built with scripts/build_linux.py first.
#
# Requires squashfs-tools (mksquashfs). appimagetool is downloaded and cached
# under build/appimage-tools; FUSE is not needed (--appimage-extract-and-run).
# Result: dist/WaygroundAutomator-<version>-x86_64.AppImage
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/build/appimage"
APPDIR="$WORK/WaygroundAutomator.AppDir"
TOOLDIR="$ROOT/build/appimage-tools"

BINARY="${1:-}"
if [ -z "$BINARY" ]; then
    "$ROOT/scripts/build_linux.py" --distpath "$WORK/binary"
    BINARY="$WORK/binary/WaygroundAutomator"
fi
if [ ! -x "$BINARY" ]; then
    echo "ERROR: not an executable: $BINARY" >&2
    exit 1
fi

if ! command -v mksquashfs >/dev/null 2>&1; then
    echo "ERROR: mksquashfs is missing (install squashfs-tools)." >&2
    exit 1
fi

echo "==> Assembling the AppDir from $BINARY"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
         "$TOOLDIR"
cp "$BINARY" "$APPDIR/usr/bin/WaygroundAutomator"
cp "$ROOT/assets/logo.png" "$APPDIR/wayground-automator.png"
cp "$ROOT/assets/logo.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/wayground-automator.png"
cp "$ROOT/packaging/appimage/wayground-automator.desktop" "$APPDIR/wayground-automator.desktop"
install -m 755 /dev/stdin "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
# AppRun: resolve the mounted AppDir so the AppImage works from any path.
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/WaygroundAutomator" "$@"
EOF

TOOL="${APPIMAGETOOL:-$TOOLDIR/appimagetool-x86_64.AppImage}"
if [ ! -x "$TOOL" ]; then
    echo "==> Downloading appimagetool"
    curl -fsSL -o "$TOOL" \
        https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "$TOOL"
fi

VERSION="$(python3 - "$ROOT/src/config.py" <<'EOF'
import ast, sys
tree = ast.parse(open(sys.argv[1], encoding="utf-8").read())
print(next(ast.literal_eval(node.value) for node in tree.body
           if isinstance(node, ast.Assign)
           and any(isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets)))
EOF
)"
NAME="WaygroundAutomator-$VERSION-x86_64.AppImage"
OUT_DIR="${WAYGROUND_OUT:-$ROOT/dist}"

echo "==> Building $NAME"
mkdir -p "$OUT_DIR"
ARCH=x86_64 "$TOOL" --appimage-extract-and-run --no-appstream \
    "$APPDIR" "$OUT_DIR/$NAME"

echo "AppImage: $OUT_DIR/$NAME"
ls -lh "$OUT_DIR/$NAME"
