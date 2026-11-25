import json
import os
import unittest

from fixtures import APPID, USER_ENGINE, Library, utf16
from skip_launcher.engine import Engine
from skip_launcher.iniutil import IniText


def make(test, installed=True, ini=True, state_flags=4):
    lib = Library(test)
    if installed:
        lib.install(state_flags)
    if ini:
        lib.write_ini()
    return lib, Engine(lib.home, lib.settings, proc_root=lib.proc, clock=lambda: 1000)


def value(lib, section, key):
    return IniText(lib.read_ini()).get(section, key)


class StatusTests(unittest.TestCase):
    def test_unknown_game(self):
        _, eng = make(self)
        self.assertEqual(eng.get_game("999")["status"]["code"], "unknown_game")
        self.assertEqual(eng.set_option("999", "vsync", "off")["status"]["code"], "unknown_game")

    def test_not_installed(self):
        _, eng = make(self, installed=False, ini=False)
        self.assertEqual(eng.get_game(APPID)["status"]["code"], "not_installed")
        self.assertFalse(eng.list_games()[0]["installed"])

    def test_updating_game_is_not_touched(self):
        lib, eng = make(self, state_flags=1026)
        before = lib.read_ini()
        self.assertEqual(eng.set_option(APPID, "vsync", "off")["status"]["code"], "not_ready")
        self.assertEqual(lib.read_ini(), before)

    def test_running_game_is_not_touched_in_any_spelling(self):
        lib, eng = make(self)
        before = lib.read_ini()
        lib.fake_process("/x/reaper SteamLaunch AppId=%s -- /x/proton waitforexitandrun /x/y.exe" % APPID)
        res = eng.set_option(APPID, "vsync", "off")
        self.assertFalse(res["ok"])
        self.assertEqual(res["status"]["code"], "running")
        self.assertEqual(eng.restore(APPID)["status"]["code"], "running")
        self.assertEqual(lib.read_ini(), before)
        self.assertEqual(eng.get_game(APPID)["status"]["code"], "running")      # still readable while it runs

    def test_missing_ini_is_reported_and_never_created(self):
        lib, eng = make(self, ini=False)
        self.assertEqual(eng.get_game(APPID)["status"]["code"], "no_config")
        self.assertEqual(eng.set_option(APPID, "vsync", "off")["status"]["code"], "no_config")
        self.assertFalse(os.path.exists(lib.ini_path))
        self.assertEqual(eng.list_games()[0]["status"]["code"], "no_config")

    def test_undecodable_ini_is_unreadable_and_untouched(self):
        lib, eng = make(self, ini=False)
        lib.write_ini(b"\xff\xfe\x00")
        self.assertEqual(eng.set_option(APPID, "vsync", "off")["status"]["code"], "unreadable")
        self.assertEqual(lib.read_ini(), b"\xff\xfe\x00")


class ReadTests(unittest.TestCase):
    def test_current_options_of_the_launchers_own_file(self):
        _, eng = make(self)
        game = eng.get_game(APPID)
        self.assertEqual(game["status"]["code"], "ok")
        cur = {s["id"]: s["current"] for s in game["settings"]}
        self.assertEqual(cur["resolution"], "1920x1080")
        self.assertEqual(cur["fullscreen"], "on")
        self.assertEqual(cur["vsync"], "on")
        self.assertEqual(cur["antialiasing"], "off")
        self.assertEqual(cur["detail"], "very_high")
        self.assertEqual(cur["effects"], "high")
        self.assertEqual(cur["physx"], "off")
        self.assertEqual(cur["subtitles"], "off")
        self.assertFalse(game["changed"])

    def test_a_value_no_option_matches_reads_as_custom(self):
        lib, eng = make(self, ini=False)
        lib.write_ini(utf16(USER_ENGINE.replace("ResX=1920", "ResX=1111")))
        cur = {s["id"]: s["current"] for s in eng.get_game(APPID)["settings"]}
        self.assertIsNone(cur["resolution"])

    def test_json_serialisable(self):
        _, eng = make(self)
        json.dumps(eng.get_game(APPID))
        json.dumps(eng.list_games())


class WriteTests(unittest.TestCase):
    def test_set_option_changes_only_its_keys_and_keeps_encoding(self):
        lib, eng = make(self)
        before = lib.read_ini()
        res = eng.set_option(APPID, "resolution", "1280x800")
        self.assertTrue(res["ok"] and res["changed"])
        after = lib.read_ini()
        self.assertTrue(after.startswith(b"\xff\xfe"))
        self.assertEqual(after.decode("utf-16"),
                         before.decode("utf-16").replace("ResX=1920", "ResX=1280").replace("ResY=1080", "ResY=800"))
        self.assertEqual(eng.get_game(APPID)["settings"][0]["current"], "1280x800")
        self.assertTrue(eng.get_game(APPID)["changed"])

    def test_multi_key_option_sets_all_keys(self):
        lib, eng = make(self)
        eng.set_option(APPID, "detail", "low")
        self.assertEqual(value(lib, "SystemSettings", "MaxShadowResolution"), "256")
        self.assertEqual(value(lib, "SystemSettings", "DetailMode"), "0")
        self.assertEqual(value(lib, "SystemSettings", "Bloom"), "False")
        cur = {s["id"]: s["current"] for s in eng.get_game(APPID)["settings"]}
        self.assertEqual(cur["detail"], "low")
        self.assertEqual(cur["motion_blur"], "off")

    def test_setting_the_same_value_writes_nothing(self):
        lib, eng = make(self)
        before = os.stat(lib.ini_path).st_mtime_ns
        res = eng.set_option(APPID, "vsync", "on")
        self.assertTrue(res["ok"])
        self.assertFalse(res["changed"])
        self.assertEqual(os.stat(lib.ini_path).st_mtime_ns, before)

    def test_unknown_setting_or_option(self):
        lib, eng = make(self)
        before = lib.read_ini()
        self.assertEqual(eng.set_option(APPID, "nope", "on")["status"]["code"], "unknown_setting")
        self.assertEqual(eng.set_option(APPID, "vsync", "maybe")["status"]["code"], "unknown_setting")
        self.assertEqual(lib.read_ini(), before)

    def test_no_temp_file_is_left_behind(self):
        lib, eng = make(self)
        eng.set_option(APPID, "vsync", "off")
        self.assertEqual([n for n in os.listdir(os.path.dirname(lib.ini_path)) if n.endswith(".tmp")], [])

    def test_the_way_back_is_on_disk_before_the_first_write(self):
        lib, eng = make(self)
        before = lib.read_ini()
        seen = {}
        real = __import__("skip_launcher.engine", fromlist=["_write_atomic"])._write_atomic

        def spy(path, data):
            if path == lib.ini_path:
                with open(eng.config_path) as f:
                    seen["record"] = json.load(f)
                with open(eng._backup_path(APPID), "rb") as f:
                    seen["backup"] = f.read()
            return real(path, data)

        import skip_launcher.engine as mod
        mod._write_atomic = spy
        self.addCleanup(setattr, mod, "_write_atomic", real)
        eng.set_option(APPID, "vsync", "off")
        self.assertEqual(seen["backup"], before)
        self.assertEqual(seen["record"]["games"][APPID]["originals"], {"SystemSettings|UseVsync": "True"})


class FailureTests(unittest.TestCase):
    def test_a_failing_replace_leaves_the_old_file_and_no_temp(self):
        lib, eng = make(self)
        before = lib.read_ini()
        real = os.replace

        def boom(src, dst):
            if dst == lib.ini_path:
                raise OSError("disk went away")
            return real(src, dst)

        os.replace = boom
        self.addCleanup(setattr, os, "replace", real)
        res = eng.set_option(APPID, "vsync", "off")
        os.replace = real
        self.assertFalse(res["ok"])
        self.assertEqual(res["status"]["code"], "write_failed")
        self.assertEqual(lib.read_ini(), before)
        self.assertEqual([n for n in os.listdir(os.path.dirname(lib.ini_path)) if n.endswith(".tmp")], [])
        self.assertTrue(eng.restore(APPID)["ok"])                       # the recorded way back still works
        self.assertEqual(lib.read_ini(), before)

    def test_running_guard_sees_the_install_path_and_the_windows_form(self):
        lib, eng = make(self)
        exe = os.path.join(lib.install_path, "Binaries", "ShippingPC-BmGame.exe")
        for cmd in (exe, "Z:" + exe.replace("/", "\\")):
            lib.fake_process(cmd, pid="77")
            self.assertEqual(eng.set_option(APPID, "vsync", "off")["status"]["code"], "running", cmd)
        self.assertEqual(IniText(lib.read_ini()).get("SystemSettings", "UseVsync"), "True")

    def test_appid_must_be_a_whole_token(self):
        lib, eng = make(self)
        lib.fake_process("/x/reaper AppId=351400 -- /x/proton")
        self.assertTrue(eng.set_option(APPID, "vsync", "off")["ok"])


class RestoreTests(unittest.TestCase):
    def test_restore_gives_back_the_exact_bytes(self):
        lib, eng = make(self)
        before = lib.read_ini()
        for sid, oid in (("resolution", "1280x720"), ("detail", "low"), ("physx", "normal"), ("vsync", "off"),
                         ("subtitles", "on"), ("antialiasing", "4x")):
            self.assertTrue(eng.set_option(APPID, sid, oid)["ok"])
        self.assertNotEqual(lib.read_ini(), before)
        res = eng.restore(APPID)
        self.assertTrue(res["ok"] and res["changed"])
        self.assertEqual(lib.read_ini(), before)
        self.assertFalse(eng.get_game(APPID)["changed"])
        self.assertEqual(eng.restore(APPID)["changed"], False)                   # nothing left to restore

    def test_first_recorded_value_wins_over_later_changes(self):
        lib, eng = make(self)
        eng.set_option(APPID, "vsync", "off")
        eng.set_option(APPID, "vsync", "on")
        eng.set_option(APPID, "vsync", "off")
        eng.restore(APPID)
        self.assertEqual(value(lib, "SystemSettings", "UseVsync"), "True")

    def test_restore_is_exact_per_key_when_the_file_was_rewritten_meanwhile(self):
        lib, eng = make(self)
        eng.set_option(APPID, "vsync", "off")
        # the launcher (or the game) rewrites another key in between
        ini = IniText(lib.read_ini())
        ini.set("SystemSettings", "ResX", "1600")
        with open(lib.ini_path, "wb") as f:
            f.write(ini.dumps())
        eng.restore(APPID)
        self.assertEqual(value(lib, "SystemSettings", "UseVsync"), "True")
        self.assertEqual(value(lib, "SystemSettings", "ResX"), "1600")          # not ours: left alone

    def test_a_key_that_did_not_exist_is_removed_again(self):
        lib, eng = make(self, ini=False)
        lib.write_ini(utf16(USER_ENGINE.replace("bSubtitlesEnabled=FALSE\r\n", "")))
        before = lib.read_ini()
        eng.set_option(APPID, "subtitles", "on")
        self.assertEqual(value(lib, "Engine.Engine", "bSubtitlesEnabled"), "True")
        eng.restore(APPID)
        self.assertEqual(lib.read_ini(), before)


if __name__ == "__main__":
    unittest.main()
