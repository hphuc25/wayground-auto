"""
Browser auto-detection and launching with Chrome DevTools Protocol (CDP) debugging port.
"""

import os
import re
import shutil
import sys
import subprocess
import time
from pathlib import Path

import config
from config import C_BOLD, C_DIM, C_YELLOW, C_RESET
from ui import log_info, log_error, log_step


def _windows_candidates():
    return [
        # Edge (most common on Windows)
        (os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"), "Edge"),
        (os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"), "Edge"),
        (os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"), "Edge"),
        # Chrome
        (os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"), "Chrome"),
        (os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"), "Chrome"),
        (os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"), "Chrome"),
    ]


def _macos_candidates():
    apps = [
        ("Google Chrome", "Chrome"),
        ("Microsoft Edge", "Edge"),
        ("Chromium", "Chromium"),
        ("Brave Browser", "Brave"),
    ]
    return [(f"/Applications/{app}.app/Contents/MacOS/{app}", name) for app, name in apps]


def _linux_candidates():
    # Prefer an explicit path list, then fall back to PATH lookups.
    paths = [
        ("/opt/google/chrome/google-chrome", "Chrome"),
        ("/opt/microsoft/msedge/msedge", "Edge"),
        ("/usr/bin/google-chrome-stable", "Chrome"),
        ("/usr/bin/google-chrome", "Chrome"),
        ("/usr/bin/chromium", "Chromium"),
        ("/usr/bin/chromium-browser", "Chromium"),
        ("/usr/bin/microsoft-edge-stable", "Edge"),
        ("/usr/bin/microsoft-edge", "Edge"),
        ("/snap/bin/chromium", "Chromium"),
        ("/var/lib/flatpak/exports/bin/com.google.Chrome", "Chrome"),
        ("/var/lib/flatpak/exports/bin/com.microsoft.Edge", "Edge"),
        ("/var/lib/flatpak/exports/bin/org.chromium.Chromium", "Chromium"),
        (os.path.expanduser("~/.local/share/flatpak/exports/bin/com.google.Chrome"), "Chrome"),
        (os.path.expanduser("~/.local/share/flatpak/exports/bin/com.microsoft.Edge"), "Edge"),
    ]
    names = [
        ("google-chrome-stable", "Chrome"), ("google-chrome", "Chrome"),
        ("chromium", "Chromium"), ("chromium-browser", "Chromium"),
        ("microsoft-edge-stable", "Edge"), ("microsoft-edge", "Edge"),
        ("brave-browser", "Brave"), ("brave", "Brave"),
    ]
    for command, name in names:
        found = shutil.which(command)
        if found:
            paths.append((found, name))
    return paths


def _bundled_candidates():
    """Playwright's own Chromium build, if `playwright install chromium` was run."""
    root = Path(config.playwright_browsers_dir())
    patterns = (
        "chromium-*/chrome-linux*/chrome",
        "chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium",
    )
    found = []
    for pattern in patterns:
        for path in sorted(root.glob(pattern), reverse=True):
            found.append((str(path), "Chromium"))
    return found


def browser_candidates():
    if os.name == "nt":
        return _windows_candidates()
    if sys.platform == "darwin":
        return _macos_candidates() + _bundled_candidates()
    return _linux_candidates() + _bundled_candidates()


def find_browser_exe() -> tuple[str, str]:
    """
    Auto-detect a Chromium-based browser (Edge, Chrome, Chromium or Brave).
    Returns (path, name) or exits if not found.
    """
    candidates = browser_candidates()

    for path, name in candidates:
        if os.path.isfile(path):
            return path, name

    log_error("Could not find Chrome, Chromium or Edge!")
    print(f"  {C_DIM}Looked in:{C_RESET}")
    for path, name in candidates:
        print(f"    {C_DIM}{path}{C_RESET}")
    sys.exit(1)


def get_user_data_dir(browser_name: str) -> str:
    """
    Get the persistent user data directory for automation.
    Using a dedicated profile prevents conflicts with already running Edge/Chrome instances,
    ensures the debug port opens instantly, and permanently preserves Wayground logins.
    """
    profile_dir = os.path.join(config.data_dir(), "BrowserProfile")
    os.makedirs(profile_dir, exist_ok=True)
    return profile_dir


def is_port_open(port: int) -> bool:
    """Check if a CDP port is already open."""
    import socket
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
        return False


def launch_browser_with_debug(port: int, *, interactive: bool = True) -> subprocess.Popen:
    """
    Find Edge/Chrome, launch with --remote-debugging-port.
    Uses dedicated automator profile so debug port opens instantly even
    if user already has Edge/Chrome running with 100 tabs.
    """
    exe_path, browser_name = find_browser_exe()
    user_data = get_user_data_dir(browser_name)

    log_info(f"Found {browser_name}: {exe_path}")
    log_info(f"Automation Profile: {user_data}")

    cmd = [
        exe_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    log_info(f"Launching {browser_name} with debug port {port}...")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=(subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == "nt" else 0,
        start_new_session=os.name != "nt",
    )

    # Wait for browser to start and open the debug port (typically 1-2 seconds with dedicated profile)
    for i in range(12):
        if is_port_open(port):
            log_info(f"✅ {browser_name} is ready and connected! (port {port})")
            return proc
        time.sleep(0.8)
        if i % 3 == 2:
            log_step(f"Waiting for {browser_name} port {port}... ({int((i+1)*0.8)}s)")

    if not interactive:
        raise RuntimeError(
            f"{browser_name} did not open the automation port. "
            "Close the Automator browser window and connect again. Your other browser windows are left open."
        )
    print()
    log_error(f"{browser_name} is running, but port {port} is not responding.")
    log_info("This usually happens because the browser is ALREADY open in normal mode.")
    log_info(f"We can safely restart {browser_name} for you (all your tabs will be restored).")
    
    confirm = input(f"  {C_BOLD}[?]{C_RESET} Do you want to automatically restart {browser_name}? (y/n) [y]: ").strip().lower()
    
    if confirm not in ("n", "no"):
        log_info(f"Closing existing {browser_name} processes...")
        if os.name == "nt":
            exe_name = os.path.basename(exe_path)
            subprocess.run(["taskkill", "/F", "/IM", exe_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Only stop instances that use the automator profile; normal browser
            # windows stay untouched.
            subprocess.run(["pkill", "-f", re.escape(user_data)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)  # Give processes a moment to fully terminate

        log_info(f"Relaunching {browser_name} with debug port...")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0,
            start_new_session=os.name != "nt",
        )
        for i in range(15):
            if is_port_open(port):
                log_info(f"{browser_name} successfully restarted! (port {port})")
                return proc
            time.sleep(1)
            
        log_error(f"Still failed to open port {port} after restart.")
        sys.exit(1)
    else:
        log_error("Cannot continue without debugging port. Exiting.")
        sys.exit(1)
