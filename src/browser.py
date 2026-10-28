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
        ("/opt/google/chrome-unstable/google-chrome-unstable", "Chrome"),
        ("/opt/google/chrome-beta/google-chrome-beta", "Chrome"),
        ("/opt/microsoft/msedge/msedge", "Edge"),
        ("/opt/microsoft/msedge-beta/msedge-beta", "Edge"),
        ("/usr/bin/google-chrome-stable", "Chrome"),
        ("/usr/bin/google-chrome", "Chrome"),
        ("/usr/bin/google-chrome-beta", "Chrome"),
        ("/usr/bin/google-chrome-unstable", "Chrome"),
        ("/usr/bin/chromium", "Chromium"),
        ("/usr/bin/chromium-browser", "Chromium"),
        ("/usr/bin/ungoogled-chromium", "Chromium"),
        ("/usr/bin/microsoft-edge-stable", "Edge"),
        ("/usr/bin/microsoft-edge", "Edge"),
        ("/usr/bin/microsoft-edge-beta", "Edge"),
        ("/usr/bin/opera", "Opera"),
        ("/usr/bin/opera-stable", "Opera"),
        ("/usr/bin/vivaldi-stable", "Vivaldi"),
        ("/usr/bin/vivaldi-snapshot", "Vivaldi"),
    ]
    names = [
        ("google-chrome-stable", "Chrome"), ("google-chrome", "Chrome"),
        ("google-chrome-beta", "Chrome"), ("google-chrome-unstable", "Chrome"),
        ("chromium", "Chromium"), ("chromium-browser", "Chromium"),
        ("ungoogled-chromium", "Chromium"),
        ("microsoft-edge-stable", "Edge"), ("microsoft-edge", "Edge"),
        ("microsoft-edge-beta", "Edge"),
        ("brave-browser", "Brave"), ("brave", "Brave"),
        ("opera", "Opera"), ("opera-stable", "Opera"),
        ("vivaldi-stable", "Vivaldi"),
    ]
    for command, name in names:
        found = shutil.which(command)
        if found:
            paths.append((found, name))
    return paths


def _sandboxed_candidates():
    """Snap and Flatpak browsers are checked last: they need special handling."""
    apps = [
        ("com.google.Chrome", "Chrome"),
        ("com.microsoft.Edge", "Edge"),
        ("org.chromium.Chromium", "Chromium"),
        ("com.brave.Browser", "Brave"),
    ]
    prefixes = (
        "/var/lib/flatpak/exports/bin",
        os.path.expanduser("~/.local/share/flatpak/exports/bin"),
    )
    paths = [(f"{prefix}/{app_id}", name) for prefix in prefixes for app_id, name in apps]
    paths.append(("/snap/bin/chromium", "Chromium"))
    paths.append(("/snap/bin/google-chrome", "Chrome"))
    paths.append(("/snap/bin/brave", "Brave"))
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
    # Sandboxed browsers come last: they need extra handling at launch time.
    return _linux_candidates() + _bundled_candidates() + _sandboxed_candidates()


def _browser_name_for(path: str) -> str:
    lowered = os.path.basename(path).lower()
    if "msedge" in lowered or "edge" in lowered:
        return "Edge"
    if "brave" in lowered:
        return "Brave"
    if "vivaldi" in lowered:
        return "Vivaldi"
    if "opera" in lowered:
        return "Opera"
    if "chrome" in lowered and "chromium" not in lowered:
        return "Chrome"
    return "Chromium"


def _executable(path: str) -> bool:
    return bool(path) and os.path.isfile(path) and os.access(path, os.X_OK)


def manual_override():
    """WAYGROUND_BROWSER=<path or command name> forces a specific browser."""
    value = os.environ.get("WAYGROUND_BROWSER", "").strip()
    if not value:
        return None
    path = shutil.which(value) if os.sep not in value else value
    if _executable(path):
        return path, _browser_name_for(path)
    log_error(f"WAYGROUND_BROWSER does not point to an executable: {value}")
    return None


def find_browser_exe() -> tuple[str, str]:
    """
    Auto-detect a Chromium-based browser (Chrome, Chromium, Edge, Brave,
    Opera or Vivaldi). Set WAYGROUND_BROWSER to force a specific executable.
    Returns (path, name) or exits if not found.
    """
    override = manual_override()
    if override:
        return override

    candidates = browser_candidates()

    for path, name in candidates:
        if _executable(path):
            return path, name

    log_error("No Chrome, Chromium, Edge or Brave browser was found.")
    print(f"  {C_DIM}Looked in:{C_RESET}")
    for path, name in candidates:
        print(f"    {C_DIM}{path}{C_RESET}")
    print(f"  {C_YELLOW}Install a browser, or point the app to one explicitly:{C_RESET}")
    print(f"    {C_DIM}export WAYGROUND_BROWSER=/path/to/chrome   (or a command such as 'chromium'){C_RESET}")
    print(f"  {C_DIM}Fallback: download Playwright's Chromium with:{C_RESET}")
    print(f"    {C_DIM}python -m playwright install chromium{C_RESET}")
    sys.exit(1)


def sandbox_kind(exe_path: str) -> str | None:
    """Snap and Flatpak browsers cannot read arbitrary hidden folders."""
    resolved = os.path.realpath(exe_path)
    if resolved.startswith("/snap/"):
        return "snap"
    if "/flatpak/" in resolved:
        return "flatpak"
    return None


def get_user_data_dir(exe_path: str = "", browser_name: str = "") -> str:
    """
    Get the persistent user data directory for automation.
    Using a dedicated profile prevents conflicts with already running Edge/Chrome instances,
    ensures the debug port opens instantly, and permanently preserves Wayground logins.
    Snap hides dot-directories from the browser, so its profile must be visible.
    """
    if sandbox_kind(exe_path) == "snap":
        profile_dir = os.path.join(os.path.expanduser("~"), "WaygroundAutomator", "BrowserProfile")
    else:
        profile_dir = os.path.join(config.data_dir(), "BrowserProfile")
    os.makedirs(profile_dir, exist_ok=True)
    return profile_dir


def browser_command(exe_path: str, port: int, user_data: str) -> list:
    """Launch arguments; Flatpak needs the profile directory granted explicitly."""
    args = [
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if sandbox_kind(exe_path) == "flatpak":
        return ["flatpak", "run", f"--filesystem={user_data}", os.path.basename(exe_path), *args]
    return [exe_path, *args]


def is_port_open(port: int) -> bool:
    """Check if a CDP port is already open."""
    import socket
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
        return False


def launch_log_path() -> str:
    """Browser stderr is written here when the debug port fails to open."""
    log_path = os.path.join(config.data_dir(), "browser-launch.log")
    try:
        os.makedirs(config.data_dir(), exist_ok=True)
    except OSError:
        pass
    return log_path


def launch_browser_with_debug(port: int, *, interactive: bool = True) -> subprocess.Popen:
    """
    Find Edge/Chrome, launch with --remote-debugging-port.
    Uses dedicated automator profile so debug port opens instantly even
    if user already has Edge/Chrome running with 100 tabs.
    """
    exe_path, browser_name = find_browser_exe()
    user_data = get_user_data_dir(exe_path, browser_name)

    log_info(f"Found {browser_name}: {exe_path}")
    log_info(f"Automation Profile: {user_data}")

    cmd = browser_command(exe_path, port, user_data)
    log_path = launch_log_path()

    log_info(f"Launching {browser_name} with debug port {port}...")
    log_file = open(log_path, "w", encoding="utf-8", errors="replace")
    proc = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=(subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == "nt" else 0,
        start_new_session=os.name != "nt",
    )
    log_file.close()

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
            "Close the Automator browser window and connect again. Your other browser windows are left open. "
            f"Browser output was saved to: {log_path}"
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
