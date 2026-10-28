#!/usr/bin/env bash
# Install a menu entry for the built binary (optional).
# Usage: ./scripts/install_desktop_entry.sh [/path/to/WaygroundAutomator]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${1:-$ROOT/dist/WaygroundAutomator}"
BIN="$(readlink -f "$BIN")"

if [ ! -x "$BIN" ]; then
    echo "ERROR: not an executable: $BIN" >&2
    echo "Build it first with ./scripts/build_in_container.sh" >&2
    exit 1
fi

ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$ICON_DIR" "$APPS_DIR"
cp "$ROOT/assets/logo.png" "$ICON_DIR/wayground-automator.png"

cat > "$APPS_DIR/wayground-automator.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Wayground Pro Automator
Comment=Automated tests on wayground.com
Exec="$BIN"
Icon=wayground-automator
Terminal=false
Categories=Utility;
EOF

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS_DIR" || true
echo "Installed: $APPS_DIR/wayground-automator.desktop"
echo "Executable: $BIN"
