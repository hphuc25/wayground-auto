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


if __name__ == "__main__":
    unittest.main()
