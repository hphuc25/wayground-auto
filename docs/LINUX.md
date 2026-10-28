# Running on Linux

The desktop UI, console mode and browser automation run natively on Linux. No
Windows emulation (Wine) is needed.

## Requirements

- Python 3.10+ and `pip`
- A Chromium-based browser: Google Chrome, Chromium, Microsoft Edge, Brave, or
  Playwright's bundled Chromium
- Qt runtime libraries, which the `PySide6` wheel bundles

If your distribution packages Qt/Chromium separately, install the usual X11 or
Wayland desktop libraries (for example `libxcb-cursor0` on Debian/Ubuntu if Qt
reports a missing `xcb` plugin).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium   # only needed as a browser fallback
cp .env.example .env                    # optional: personal AI keys
```

## Run

```bash
python src/main.py          # desktop UI
python src/main.py --cli    # console menu
python src/main.py --attach --wrong 5   # console, attach to a running browser
```

Browser detection looks for Chrome, Chromium, Edge, Brave, Snap/Flatpak builds
and finally Playwright's bundled Chromium (`~/.cache/ms-playwright`). A
dedicated automation profile is stored in
`~/.local/share/WaygroundAutomator/BrowserProfile`, so your normal browser
profile is never touched. UI preferences live in
`~/.config/WaygroundAutomator/ui.json`. Personal AI keys are read from `.env`
next to the sources first, then from `~/.config/WaygroundAutomator/.env` — the
place to put them after a system-wide install (for example the Arch package,
see [ARCH.md](ARCH.md)).

## Build a standalone binary

### In a container (recommended)

This produces a binary built on Ubuntu 22.04, so it runs on Ubuntu 22.04+,
Debian 12+ and other current distributions:

```bash
./scripts/build_in_container.sh
# podman or docker is detected automatically; override with CONTAINER_ENGINE=docker
```

The result is `dist/WaygroundAutomator`. The build uses `Containerfile` and
`.dockerignore`; `dist/` is mounted into the container as `/out`.

To add the binary to the application menu (also removes the Wayland portal
warning about an unknown app ID):

```bash
./scripts/install_desktop_entry.sh
```

### On the host

```bash
./build.sh
# or
pip install pyinstaller
python scripts/build_linux.py
```

The binary is written to `dist/<version>/WaygroundAutomator`. It still needs a
Chromium-based browser at runtime (or Playwright's Chromium installed with
`python -m playwright install chromium`).

To add it to the application menu, copy the binary somewhere on `PATH` and
install a desktop entry such as:

```ini
[Desktop Entry]
Type=Application
Name=Wayground Pro Automator
Exec=/opt/wayground/WaygroundAutomator
Icon=/opt/wayground/logo.png
Terminal=false
Categories=Utility;
```

## Platform notes

- **Boss key (F2/F8/Ctrl+Shift+H):** on Windows the key is registered globally.
  On Linux it works as an application shortcut while the window is focused,
  because Wayland and many X11 window managers do not allow global grabs
  without extra permissions. The tray icon also restores the panel.
- **System tray:** shown when the desktop provides a StatusNotifier/AppIndicator
  tray. Without one, use the panel's minimize/restore controls.
- **Wayland:** the window is a normal native window. Fractional scaling and
  global shortcuts are controlled by the compositor.
- **Closing a run:** Stop/Exit leaves the browser open, same as on Windows.
