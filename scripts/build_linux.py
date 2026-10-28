"""Build the standalone desktop executable for Linux with PyInstaller."""

import argparse
import ast
import os
from pathlib import Path
import subprocess
import sys


def main():
    if not sys.platform.startswith("linux"):
        raise SystemExit("Build the Linux executable on Linux.")
    parser = argparse.ArgumentParser()
    parser.add_argument("--console", action="store_true", help="Diagnostic console build")
    parser.add_argument("--distpath", help="Alternative output folder when a previous executable is running")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "src" / "config.py").read_text(encoding="utf-8"))
    version = next(ast.literal_eval(node.value) for node in tree.body
                   if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets))
    destination = args.distpath or ("scratch/gui-debug" if args.console else f"dist/{version}")
    command = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile",
        "--console" if args.console else "--windowed", "--name", "WaygroundAutomator",
        "--distpath", destination, "--workpath", f"build/desktop-{version}",
        "--add-data", f"assets{os.pathsep}assets",
        "--collect-data", "playwright_stealth",
        "--paths", "src", "src/main.py",
    ]
    # PyInstaller ignores --icon on Linux; a desktop entry provides the launcher icon.
    subprocess.run(command, cwd=root, check=True)


if __name__ == "__main__":
    main()
