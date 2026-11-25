import contextlib
import importlib.util
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("scaffold_game", ROOT / "tools" / "scaffold_game.py")
scaffold = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scaffold)


def temp_root(test):
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    root = Path(tmp.name)
    (root / "docs" / "games").mkdir(parents=True)
    shutil.copy(ROOT / "docs" / "games" / "_template.md", root / "docs" / "games" / "_template.md")
    return root


class ScaffoldTests(unittest.TestCase):
    def run_tool(self, root, *argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return scaffold.main(["--root", str(root), *argv])

    def test_creates_an_importable_profile_and_a_page_for_an_exe_swap_game(self):
        root = temp_root(self)
        self.assertEqual(self.run_tool(root, "--appid", "777", "--name", "Some Game", "--launcher", "Start.exe", "--game", "Real.exe"), 0)
        profile = root / "py_modules" / "skip_launcher" / "profiles" / "some_game.py"
        page = root / "docs" / "games" / "777-some-game.md"
        text = profile.read_text()
        compile(text, str(profile), "exec")
        self.assertIn('appid = "777"', text)
        self.assertIn('launcher_exe = "Start.exe"', text)
        self.assertNotIn("skip_args", text)
        self.assertIn("# Some Game (appid 777)", page.read_text())
        self.assertIn("| Support level | unconfirmed |", page.read_text())

    def test_a_registry_dialog_game(self):
        root = temp_root(self)
        self.assertEqual(self.run_tool(
            root, "--appid", "888", "--name", "Dialog Game", "--launcher", "dg.exe", "--skip-args=-nodialog",
            "--format", "reg", "--config-rel", "user.reg", "--required-section", r"Software\\Vendor\\Dialog Game\\Video Settings"), 0)
        text = (root / "py_modules" / "skip_launcher" / "profiles" / "dialog_game.py").read_text()
        compile(text, "dialog_game.py", "exec")
        self.assertIn('skip_args = "-nodialog"', text)
        self.assertIn('config_format = "reg"', text)
        self.assertIn("required_section", text)
        self.assertIn('game_exe = "dg.exe"', text)

    def test_dry_run_writes_nothing(self):
        root = temp_root(self)
        self.assertEqual(self.run_tool(root, "--appid", "1", "--name", "X Game", "--game", "x.exe", "--dry-run"), 0)
        self.assertFalse((root / "py_modules").exists())
        self.assertEqual(sorted(p.name for p in (root / "docs" / "games").iterdir()), ["_template.md"])

    def test_refuses_to_overwrite(self):
        root = temp_root(self)
        args = ("--appid", "9", "--name", "Twice", "--game", "t.exe")
        self.assertEqual(self.run_tool(root, *args), 0)
        profile = root / "py_modules" / "skip_launcher" / "profiles" / "twice.py"
        profile.write_text("# my work\n")
        self.assertEqual(self.run_tool(root, *args), 1)
        self.assertEqual(profile.read_text(), "# my work\n")

    def test_refuses_nonsense_input(self):
        root = temp_root(self)
        for argv in (("--appid", "abc", "--name", "A", "--game", "a.exe"),
                     ("--appid", "1", "--name", "A", "--launcher", "A.exe"),                       # same exe, no switch
                     ("--appid", "1", "--name", "A", "--game", "a.exe", "--skip-args=nodialog"),
                     ("--appid", "1", "--name", "A", "--game", "a.exe", "--format", "reg"),        # no required section
                     ("--appid", "1", "--name", "A", "--game", "a.exe", "--slug", "Bad Slug")):
            self.assertEqual(self.run_tool(root, *argv), 2, argv)
        self.assertFalse((root / "py_modules").exists())


if __name__ == "__main__":
    unittest.main()
