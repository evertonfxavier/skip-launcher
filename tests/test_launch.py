import shlex
import subprocess
import unittest

import fixtures  # noqa: F401
from skip_launcher import launch

L, G = "BmLauncher.exe", "ShippingPC-BmGame.exe"
WRAP = "bash -c 'exec \"${@/BmLauncher.exe/ShippingPC-BmGame.exe}\"' _ %command%"


class LaunchOptionTests(unittest.TestCase):
    def test_wrapper_is_exactly_the_line_tested_on_the_deck(self):
        self.assertEqual(launch.wrapper(L, G), WRAP)

    def test_enable_disable_roundtrip(self):
        for before in ("", "%command%", "FOO=1 %command% -x", "-windowed", "  -windowed -x ", "gamemoderun %command%"):
            on = launch.enable(before, L, G)
            self.assertTrue(launch.is_enabled(on, L, G), before)
            self.assertEqual(launch.enable(on, L, G), on)                 # idempotent
            off = launch.disable(on, L, G)
            self.assertFalse(launch.is_enabled(off, L, G))
            self.assertEqual(launch.disable(off, L, G), off)
            expected = "" if before.strip() == "%command%" else " ".join(before.split())
            self.assertEqual(" ".join(off.split()), expected, before)

    def test_other_options_are_kept_around_the_wrapper(self):
        self.assertEqual(launch.enable("FOO=1 %command% -x", L, G), "FOO=1 " + WRAP + " -x")
        self.assertEqual(launch.enable("-windowed", L, G), WRAP + " -windowed")

    def test_the_manually_typed_line_counts_as_enabled(self):
        self.assertTrue(launch.is_enabled(WRAP, L, G))
        self.assertEqual(launch.disable(WRAP, L, G), "")

    def test_the_wrapper_really_rewrites_only_the_launcher_argument(self):
        argv = ["/x/steam-launch-wrapper", "--", "/x/proton", "waitforexitandrun",
                "/lib/Batman Arkham Asylum GOTY/Binaries/BmLauncher.exe", "-foo"]
        # What Steam's shell does with the wrapper: split it into words, put the command where %command% stands.
        words = shlex.split(launch.wrapper(L, G))
        self.assertEqual(words[:2], ["bash", "-c"])
        self.assertEqual(words[-1], "%command%")
        words[2] = words[2].replace("exec ", "exec printf '%s\\n' ", 1)         # print instead of running the game
        out = subprocess.run(words[:-1] + argv, capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(out[:-2], argv[:-2])
        self.assertEqual(out[-2], "/lib/Batman Arkham Asylum GOTY/Binaries/ShippingPC-BmGame.exe")
        self.assertEqual(out[-1], "-foo")


class ArgumentOptionTests(unittest.TestCase):
    A = "-nodialog"

    def test_roundtrip_keeps_everything_else(self):
        for before in ("", "FOO=1 %command%", "%command% -x", "-x", "%command% -windowed -x", "gamemoderun %command% -x"):
            on = launch.enable_args(before, self.A)
            self.assertTrue(launch.args_enabled(on, self.A), before)
            self.assertEqual(launch.enable_args(on, self.A), on)             # idempotent
            self.assertEqual(launch.disable_args(on, self.A), before, before)

    def test_a_bare_command_goes_back_to_empty(self):
        self.assertEqual(launch.disable_args(launch.enable_args("%command%", self.A), self.A), "")

    def test_only_the_whole_word_counts(self):
        self.assertFalse(launch.args_enabled("%command% -nodialogs", self.A))
        self.assertFalse(launch.args_enabled("%command% x-nodialog", self.A))
        self.assertEqual(launch.disable_args("%command% -nodialogs", self.A), "%command% -nodialogs")

    def test_the_word_lands_right_after_the_command(self):
        self.assertEqual(launch.enable_args("%command% -x", self.A), "%command% -nodialog -x")
        self.assertEqual(launch.enable_args("-x", self.A), "-x -nodialog")      # no %command%: Steam appends it anyway
        self.assertEqual(launch.enable_args("", self.A), "%command% -nodialog")

    def test_the_line_typed_by_hand_counts_and_dispatch_follows_the_profile(self):
        from skip_launcher.profiles import PROFILES
        mp, batman = PROFILES["12140"], PROFILES["35140"]
        self.assertTrue(launch.profile_enabled("%command% -nodialog", mp))
        self.assertEqual(launch.profile_enable("", mp), "%command% -nodialog")
        self.assertEqual(launch.profile_disable("%command% -nodialog", mp), "")
        self.assertEqual(launch.profile_enable("", batman), WRAP)
        self.assertFalse(launch.profile_enabled("%command% -nodialog", batman))


if __name__ == "__main__":
    unittest.main()
