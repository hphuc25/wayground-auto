# Build container for the Linux standalone binary.
# Ubuntu 22.04 (glibc 2.35) keeps the result runnable on Ubuntu 22.04+,
# Debian 12+ and other current distributions.
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/venv \
    PATH=/venv/bin:$PATH

# Python plus the system libraries needed to import/bundle Qt (PySide6) and
# to start the resulting binary on a normal desktop.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-venv \
        libpython3.10 \
        binutils \
        ca-certificates \
        curl \
        file \
        squashfs-tools \
        libgl1 \
        libegl1 \
        libglib2.0-0 \
        libdbus-1-3 \
        libfontconfig1 \
        libfreetype6 \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxcb-cursor0 \
        libxcb-icccm4 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-randr0 \
        libxcb-render0 \
        libxcb-render-util0 \
        libxcb-shape0 \
        libxcb-shm0 \
        libxcb-sync1 \
        libxcb-util1 \
        libxcb-xfixes0 \
        libxcb-xinerama0 \
        libxcb-xkb1 \
        libxkbcommon0 \
        libxkbcommon-x11-0 \
        libxi6 \
        libsm6 \
        libice6 \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv "$VIRTUAL_ENV" \
    && pip install --upgrade pip

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt pyinstaller

COPY . .

# /out is expected to be a mounted volume; see scripts/build_in_container.sh.
# Produces both the one-file binary and the AppImage.
CMD ["bash", "-c", "python scripts/build_linux.py --distpath /out && WAYGROUND_OUT=/out scripts/build_appimage.sh /out/WaygroundAutomator"]
