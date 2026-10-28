"""Cross-platform path and browser-detection checks (Linux-focused)."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import browser
import config


LINUX = sys.platform.startswith("linux")


@unittest.skipUnless(LINUX, "XDG paths apply to Linux")
class LinuxPathTests(unittest.TestCase):
    def test_paths_follow_xdg_variables(self):
        environment = {
            "XDG_DATA_HOME": "/tmp/wg-data",
            "XDG_CONFIG_HOME": "/tmp/wg-config",
            "XDG_CACHE_HOME": "/tmp/wg-cache",
        }
        with patch.dict(os.environ, environment):
            self.assertEqual(config.data_dir(), "/tmp/wg-data/WaygroundAutomator")
            self.assertEqual(config.config_dir(), "/tmp/wg-config/WaygroundAutomator")
            self.assertEqual(config.playwright_browsers_dir(), "/tmp/wg-cache/ms-playwright")

    def test_preferences_live_under_config_dir(self):
        from desktop import Preferences
        with tempfile.TemporaryDirectory() as folder, \
                patch.dict(os.environ, {"XDG_CONFIG_HOME": folder}):
            prefs = Preferences()
            self.assertEqual(prefs.path, Path(folder) / "WaygroundAutomator" / "ui.json")

    def test_user_env_file_is_read_without_overriding_the_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            env_file = Path(folder) / ".env"
            env_file.write_text("# comment\nWAYGROUND_TEST_KEY='from-env-file'\nWAYGROUND_TEST_FIXED=1\n",
                                 encoding="utf-8")
            with patch.dict(os.environ, {"WAYGROUND_TEST_FIXED": "existing"}, clear=False):
                config._apply_env_file(str(env_file))
                self.assertEqual(os.environ["WAYGROUND_TEST_KEY"], "from-env-file")
                self.assertEqual(os.environ["WAYGROUND_TEST_FIXED"], "existing")


class BrowserDetectionTests(unittest.TestCase):
    def test_path_lookup_finds_chromium(self):
        with patch.object(browser.shutil, "which",
                          side_effect=lambda name: "/usr/bin/chromium" if name == "chromium" else None):
            candidates = browser.browser_candidates()
        self.assertIn(("/usr/bin/chromium", "Chromium"), candidates)

    def test_bundled_playwright_chromium_is_a_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / "chromium-1200" / "chrome-linux" / "chrome"
            binary.parent.mkdir(parents=True)
            binary.write_text("", encoding="utf-8")
            with patch.object(config, "playwright_browsers_dir", return_value=folder):
                candidates = browser.browser_candidates()
            self.assertIn((str(binary), "Chromium"), candidates)

    def test_sandboxed_browsers_come_last(self):
        candidates = browser.browser_candidates()
        paths = [path for path, _ in candidates]
        snap = paths.index("/snap/bin/chromium") if "/snap/bin/chromium" in paths else len(paths)
        self.assertLess(paths.index("/usr/bin/chromium"), snap)

    def test_sandbox_kind(self):
        self.assertEqual(browser.sandbox_kind("/snap/bin/chromium"), "snap")
        self.assertEqual(browser.sandbox_kind("/var/lib/flatpak/exports/bin/com.google.Chrome"), "flatpak")
        self.assertIsNone(browser.sandbox_kind("/usr/bin/google-chrome"))

    def test_snap_profile_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as home:
            with patch.dict(os.environ, {"HOME": home}, clear=False):
                profile = browser.get_user_data_dir("/snap/bin/chromium", "Chromium")
        self.assertTrue(profile.startswith(home + os.sep))
        self.assertNotIn("/.", os.path.relpath(profile, home))

    def test_flatpak_command_grants_the_profile_directory(self):
        cmd = browser.browser_command("/var/lib/flatpak/exports/bin/com.google.Chrome", 9222, "/tmp/profile")
        self.assertEqual(cmd[:3], ["flatpak", "run", "--filesystem=/tmp/profile"])
        self.assertIn("--remote-debugging-port=9222", cmd)

    def test_regular_command_uses_the_executable(self):
        cmd = browser.browser_command("/usr/bin/chromium", 9333, "/tmp/profile")
        self.assertEqual(cmd[0], "/usr/bin/chromium")
        self.assertIn("--user-data-dir=/tmp/profile", cmd)

    def test_wayground_browser_override(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder) / "my-chrome"
            fake.write_text("", encoding="utf-8")
            fake.chmod(0o755)
            with patch.dict(os.environ, {"WAYGROUND_BROWSER": str(fake)}, clear=False):
                path, name = browser.find_browser_exe()
        self.assertEqual(path, str(fake))
        self.assertEqual(name, "Chrome")

    def test_broken_override_falls_back_to_auto_detect(self):
        with patch.dict(os.environ, {"WAYGROUND_BROWSER": "/nonexistent/browser"}, clear=False), \
             patch.object(browser.shutil, "which",
                          side_effect=lambda name: "/usr/bin/chromium" if name == "chromium" else None), \
             patch.object(browser, "_executable",
                          side_effect=lambda p: bool(p) and p == "/usr/bin/chromium"):
            self.assertEqual(browser.manual_override(), None)


if __name__ == "__main__":
    unittest.main()
