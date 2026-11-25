"""The supported-games list must stay in step with the profile registry and the game pages."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "py_modules"))

import gen_supported_games as gen  # noqa: E402
from skip_launcher.profiles import PROFILES  # noqa: E402


class SupportedGamesTests(unittest.TestCase):
    def test_generated_file_is_up_to_date(self):
        stale = [str(p.relative_to(ROOT)) for p, content in gen.targets(ROOT)
                 if not p.exists() or p.read_text() != content]
        self.assertEqual(stale, [], "run: python3 tools/gen_supported_games.py")

    def test_every_registered_game_has_a_valid_page_and_is_listed(self):
        text = (ROOT / "SUPPORTED_GAMES.md").read_text()
        for appid, profile in PROFILES.items():
            page = gen.read_page(ROOT, appid)
            self.assertIn(page["level"], gen.LEVELS)
            self.assertTrue(page["summary"])
            self.assertIn(profile.name, text)
            self.assertIn("store.steampowered.com/app/%s" % appid, text)

    def test_the_readme_links_to_the_list_instead_of_repeating_it(self):
        self.assertIn("SUPPORTED_GAMES.md", (ROOT / "README.md").read_text())

    def test_a_page_without_a_support_level_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            games = Path(d) / "docs" / "games"
            games.mkdir(parents=True)
            (games / "1-x.md").write_text("| Summary | s |\n| Support level | maybe |\n")
            with self.assertRaises(gen.PageError):
                gen.read_page(Path(d), "1")


if __name__ == "__main__":
    unittest.main()
