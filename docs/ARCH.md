# Arch Linux packaging

Two packages are available: a **source package** built from this checkout and a
**prebuilt package** (`wayground-pro-automator-bin`) built by CI and published
on the [GitHub releases page](https://github.com/hphuc25/wayground-auto/releases).

## Install from a GitHub release (recommended)

Every release ships a ready `wayground-pro-automator-*.pkg.tar.zst` plus a
filled-in `PKGBUILD` for the prebuilt variant. Users only need the PKGBUILD:

```bash
mkdir wga-pkgbuild && cd wga-pkgbuild
gh release download --repo hphuc25/wayground-auto PKGBUILD .SRCINFO
# or without the GitHub CLI:
# curl -LO https://github.com/hphuc25/wayground-auto/releases/latest/download/PKGBUILD
makepkg -si
```

`makepkg` downloads the matching package from the release, verifies its
SHA-256, and installs it with `pacman` together with the repository
dependencies.

Direct installation of the same package, without `makepkg`:

```bash
gh release download --repo hphuc25/wayground-auto --pattern 'wayground-pro-automator-*.pkg.tar.zst'
sudo pacman -U wayground-pro-automator-*.pkg.tar.zst
```

Non-Arch distributions can grab the standalone binary from the same release:
`WaygroundAutomator-<tag>-linux-x86_64.tar.gz` (see [LINUX.md](LINUX.md)).

## Build the source package yourself

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

## Continuous integration

`.github/workflows/release.yml` runs on every `v*.*.*` tag (or manually from
the Actions tab) and publishes one GitHub release with:

| Asset | Built on | Contents |
| ----- | -------- | -------- |
| `WaygroundAutomator-<tag>-linux-x86_64.tar.gz` | Ubuntu 22.04 | One-file PyInstaller binary |
| `wayground-pro-automator-<ver>-1-x86_64.pkg.tar.zst` | Arch Linux container | System package from `packaging/arch/PKGBUILD` |
| `PKGBUILD`, `.SRCINFO` | Arch Linux container | Prebuilt variant with the release asset URL and its SHA-256 |
| `binary.sha256` | Ubuntu 22.04 | Checksum of the standalone binary archive |

To cut a release:

```bash
git tag v4.0.1
git push origin v4.0.1
```

For a rebuild without a tag, run the **Release** workflow from the Actions tab
and pass the tag as the input. Before tagging, bump `pkgver`/`pkgrel` in
`packaging/arch/PKGBUILD` and refresh `.SRCINFO`.
