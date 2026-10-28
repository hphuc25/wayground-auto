#!/usr/bin/env bash
# Build the standalone Linux binary inside a container.
# Usage: ./scripts/build_in_container.sh [--engine podman|docker]
set -euo pipefail
cd "$(dirname "$0")/.."

ENGINE="${CONTAINER_ENGINE:-}"
if [ -z "$ENGINE" ]; then
    if command -v podman >/dev/null 2>&1; then
        ENGINE=podman
    elif command -v docker >/dev/null 2>&1; then
        ENGINE=docker
    else
        echo "ERROR: install podman or docker (or set CONTAINER_ENGINE)." >&2
        exit 1
    fi
fi
IMAGE="${IMAGE:-wayground-automator-build}"

echo "==> Using $ENGINE, image $IMAGE"
"$ENGINE" build -t "$IMAGE" -f Containerfile .

mkdir -p dist
VOLUME="$PWD/dist:/out"
if [ "$ENGINE" = "podman" ]; then
    # Relabel the bind mount on SELinux hosts.
    VOLUME="$VOLUME:Z"
fi

echo "==> Building WaygroundAutomator (binary + AppImage)"
"$ENGINE" run --rm -v "$VOLUME" "$IMAGE"

echo
echo "Output in dist/:"
ls -lh dist
