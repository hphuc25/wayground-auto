# Arch Linux packaging

`packaging/arch/PKGBUILD` installs the project from the current checkout as a
regular system package. It builds no binary: the application is pure Python and
uses the distribution's Python packages.

## Dependencies (official repositories)

| Package | Purpose |
| ------- | ------- |
| `python` | Python 3.10+ |
| `pyside6` | Qt 6 bindings for the desktop UI |
| `python-playwright` | Browser automation over CDP |
| `python-openai` | AI solver client |
| `chromium` (optdepend) | Free browser used for the automation profile |

## Build and install

```bash
cd packaging/arch
makepkg -si     # checks dependencies, builds, installs with pacman
```

Directly from the built package:

```bash
cd packaging/arch
makepkg --nodeps --nocheck
sudo pacman -U wayground-pro-automator-*.pkg.tar.zst
```

To bump a release, edit `pkgver`/`pkgrel`, then refresh `.SRCINFO`:

```bash
makepkg --printsrcinfo > .SRCINFO
```

## What gets installed

```
/usr/bin/wayground-automator                      # launcher (GUI by default, --cli for console)
/usr/share/wayground-pro-automator/src/           # application sources
/usr/share/wayground-pro-automator/assets/        # icons and themes
/usr/share/applications/wayground-automator.desktop
/usr/share/icons/hicolor/256x256/apps/wayground-automator.png
/usr/share/licenses/wayground-pro-automator/LICENSE
```

Launch it with `wayground-automator` or from the application menu (Console
actions open `--cli` / `--cli --attach`).

## Personal configuration in a system install

`/usr/share` is not writable, so personal keys go to the per-user config folder:

```bash
mkdir -p ~/.config/WaygroundAutomator
cp .env.example ~/.config/WaygroundAutomator/.env
```

The loader reads `.env` next to the sources first (development checkouts), then
`~/.config/WaygroundAutomator/.env`. UI preferences are stored in the same
folder as `ui.json`.

## Browser

Install one of the `optdepends`, or use Playwright's bundled Chromium:

```bash
python -m playwright install chromium    # → ~/.cache/ms-playwright
```

Both the desktop UI and the console detect Chrome, Chromium, Edge, Brave,
Snap/Flatpak builds and the Playwright download.

## Tests

The PKGBUILD ships no `check()` step so a build never needs network access.
Run the regression suite manually from the repository root:

```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests
```
