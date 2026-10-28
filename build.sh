#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "==================================================="
echo "  Building Wayground Pro Automator (Linux binary)"
echo "==================================================="

BUILD_PYTHON="python3"
if [ -x ".venv/bin/python" ]; then
    BUILD_PYTHON="$PWD/.venv/bin/python"
fi

echo "[1/3] Checking dependencies..."
"$BUILD_PYTHON" -m pip install -r requirements.txt pyinstaller

echo
echo "[2/3] Compiling the desktop executable..."
"$BUILD_PYTHON" scripts/build_linux.py

echo
echo "[3/3] Build complete!"
echo "Output file: dist/<version>/WaygroundAutomator"
echo "==================================================="
