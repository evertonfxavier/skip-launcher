"""Max Payne: the settings are keys of Wine's user.reg, and the skip is the `-nodialog` launch option."""
import json
import os
import unittest

from fixtures import MP_APPID, USER_REG, Library
from skip_launcher import steam
from skip_launcher.engine import Engine
from skip_launcher.regutil import RegText

VIDEO = r"Software\\Remedy Entertainment\\Max Payne\\Video Settings"
OTHER = r"Software\\Remedy Entertainment\\Max Payne\\Other Settings"


def make(test, ini=True, state_flags=4):
    lib = Library(test, MP_APPID, "Max Payne")
    lib.install(state_flags)
    if ini:
        lib.write_ini(USER_REG.encode())
    return lib, Engine(lib.home, lib.settings, proc_root=lib.proc, clock=lambda: 1000)


def value(lib, section, key):
    return RegText(lib.read_ini()).get(section, key)


class MaxPayneEngineTests(unittest.TestCase):
    def test_current_options_are_read_from_the_registry(self):
        lib, eng = make(self)
        game = eng.get_game(MP_APPID)
        self.assertEqual(game["status"]["code"], "ok")
        cur = {s["id"]: s["current"] for s in game["settings"]}
        self.assertEqual(cur["resolution"], "1920x1080")
        self.assertEqual(cur["auto_aim"], "on")
        self.assertEqual(cur["tips"], "on")

    def test_a_resolution_changes_two_lines_and_nothing_else(self):
        lib, eng = make(self)
        before = lib.read_ini().decode().splitlines()
        res = eng.set_option(MP_APPID, "resolution", "1280x720")
        self.assertTrue(res["ok"] and res["changed"], res)
        after = lib.read_ini().decode().splitlines()
        self.assertEqual(len(before), len(after))
        diff = sorted((a, b) for a, b in zip(before, after) if a != b)
        self.assertEqual(diff, [('"Display Height"=dword:00000438', '"Display Height"=dword:000002d0'),
                                ('"Display Width"=dword:00000780', '"Display Width"=dword:00000500')])
        self.assertEqual(os.listdir(os.path.dirname(lib.ini_path)), ["user.reg"])          # no temp file left

    def test_restore_gives_back_the_same_bytes_and_the_backup_is_the_original(self):
        lib, eng = make(self)
        original = lib.read_ini()
        eng.set_option(MP_APPID, "resolution", "1024x768")
        eng.set_option(MP_APPID, "crosshair", "off")
        self.assertTrue(eng.get_game(MP_APPID)["changed"])
        backup = os.path.join(lib.settings, "backups", MP_APPID, "user.reg.orig")
        with open(backup, "rb") as f:
            self.assertEqual(f.read(), original)
        self.assertTrue(eng.restore(MP_APPID)["changed"])
        self.assertEqual(lib.read_ini(), original)
        self.assertFalse(eng.get_game(MP_APPID)["changed"])

    def test_a_key_that_did_not_exist_is_removed_again_on_restore(self):
        lib, eng = make(self)
        text = USER_REG.replace('"Crosshair Toggle"=dword:00000001\n', "")
        lib.write_ini(text.encode())
        eng.set_option(MP_APPID, "crosshair", "off")
        self.assertEqual(value(lib, OTHER, "Crosshair Toggle"), "dword:00000000")
        eng.restore(MP_APPID)
        self.assertEqual(lib.read_ini(), text.encode())

    def test_before_the_dialog_ever_ran_nothing_is_created(self):
        lib, eng = make(self, ini=False)
        lib.write_ini(b"WINE REGISTRY Version 2\n\n[Software\\\\Valve\\\\Steam] 1\n")
        before = lib.read_ini()
        self.assertEqual(eng.get_game(MP_APPID)["status"]["code"], "no_config")
        self.assertEqual(eng.set_option(MP_APPID, "resolution", "1280x720")["status"]["code"], "no_config")
        self.assertEqual(lib.read_ini(), before)

    def test_a_broken_registry_file_is_unreadable_and_untouched(self):
        lib, eng = make(self)
        lib.write_ini(b"\xff\xfe\x00")
        self.assertEqual(eng.get_game(MP_APPID)["status"]["code"], "unreadable")
        self.assertEqual(eng.set_option(MP_APPID, "tips", "off")["status"]["code"], "unreadable")
        self.assertEqual(lib.read_ini(), b"\xff\xfe\x00")

    def test_nothing_is_written_while_any_process_of_the_prefix_lives(self):
        lib, eng = make(self)
        before = lib.read_ini()
        # the game is gone but wineserver of the prefix is still alive (it saves user.reg when it exits)
        lib.fake_environ({"WINEPREFIX": lib.prefix, "PATH": "/usr/bin"})
        res = eng.set_option(MP_APPID, "resolution", "1280x720")
        self.assertEqual(res["status"]["code"], "running")
        self.assertEqual(eng.restore(MP_APPID)["status"]["code"], "running")
        self.assertEqual(lib.read_ini(), before)

    def test_the_guard_sees_the_compat_data_path_and_ignores_other_prefixes(self):
        lib, _ = make(self)
        app = steam.find_app(lib.home, MP_APPID)
        self.assertFalse(steam.prefix_in_use(app, lib.proc))
        lib.fake_environ({"WINEPREFIX": os.path.join(lib.steamapps, "compatdata", "999", "pfx")}, pid="1")
        lib.fake_environ({"STEAM_COMPAT_DATA_PATH": os.path.join(lib.steamapps, "compatdata", MP_APPID, "")}, pid="2")
        self.assertTrue(steam.prefix_in_use(app, lib.proc))
        os.remove(os.path.join(lib.proc, "2", "environ"))
        self.assertFalse(steam.prefix_in_use(app, lib.proc))

    def test_the_config_records_originals_as_raw_registry_values(self):
        lib, eng = make(self)
        eng.set_option(MP_APPID, "resolution", "1280x800")
        with open(os.path.join(lib.settings, "config.json"), encoding="utf-8") as f:
            rec = json.load(f)["games"][MP_APPID]
        self.assertEqual(rec["originals"][VIDEO + "|Display Width"], "dword:00000780")
        self.assertEqual(rec["originals"][VIDEO + "|Display Height"], "dword:00000438")


MP2_APPID = "12150"
MP2_VIDEO = r"Software\\Remedy Entertainment\\Max Payne 2\\Video Settings"
MP2_OTHER = r"Software\\Remedy Entertainment\\Max Payne 2\\Other Settings"


def mp2_reg(video=True):
    """The shape of the real Max Payne 2 registry read on the Deck (2026-11-25), shortened."""
    out = ("WINE REGISTRY Version 2\n\n"
           "[Software\\\\Remedy Entertainment\\\\Max Payne 2\\\\Other Settings] 1795608441\n#time=1dd7cd5861a6f32\n"
           '"AutoAim Toggle"=dword:00000001\n"AutoWeaponSelect Toggle"=dword:00000001\n'
           '"BulletTimeAid Toggle"=dword:00000001\n"Crosshair Index"=dword:00000000\n'
           '"EnableTips Toggle"=dword:00000001\n"Other Settings Version"=dword:00000003\n'
           '"Subtitles Toggle"=dword:00000000\n\n'
           "[Software\\\\Remedy Entertainment\\\\Max Payne 2\\\\Video Settings] 1795608441\n#time=1dd7cd5861a5da8\n")
    if video:
        out += ('"CPU Driver"=dword:00000001\n"Display Bits Per Pixel"=dword:00000020\n"Display Height"=dword:000001e0\n'
                '"Display Width"=dword:00000280\n"Driver"="ATI Radeon HD 5600 Series"\n')
    return out + "\n"


def make2(test, text):
    lib = Library(test, MP2_APPID, "Max Payne 2 The Fall of Max Payne")
    lib.install()
    lib.write_ini(text.encode())
    return lib, Engine(lib.home, lib.settings, proc_root=lib.proc, clock=lambda: 1000)


class MaxPayne2Tests(unittest.TestCase):
    def test_empty_video_section_means_not_saved_yet_and_nothing_is_written(self):
        lib, eng = make2(self, mp2_reg(video=False))      # what the first run left on the Deck
        before = lib.read_ini()
        self.assertEqual(eng.get_game(MP2_APPID)["status"]["code"], "no_config")
        self.assertEqual(eng.set_option(MP2_APPID, "resolution", "1280x720")["status"]["code"], "no_config")
        self.assertEqual(lib.read_ini(), before)

    def test_the_real_registry_reads_as_640x480_with_every_toggle_known(self):
        lib, eng = make2(self, mp2_reg())
        cur = {s["id"]: s["current"] for s in eng.get_game(MP2_APPID)["settings"]}
        self.assertEqual(cur, {"resolution": "640x480", "auto_aim": "on", "auto_weapon": "on", "bullet_time_aid": "on",
                               "tips": "on", "subtitles": "off"})

    def test_changes_touch_only_their_lines_and_restore_gives_back_the_bytes(self):
        text = mp2_reg()
        lib, eng = make2(self, text)
        self.assertTrue(eng.set_option(MP2_APPID, "resolution", "1280x720")["changed"])
        self.assertTrue(eng.set_option(MP2_APPID, "subtitles", "on")["changed"])
        after = lib.read_ini().decode().splitlines()
        diff = sorted((a, b) for a, b in zip(text.splitlines(), after) if a != b)
        self.assertEqual(len(diff), 3)
        reg = RegText(lib.read_ini())
        self.assertEqual(reg.get(MP2_VIDEO, "Display Width"), "dword:00000500")
        self.assertEqual(reg.get(MP2_VIDEO, "Display Bits Per Pixel"), "dword:00000020")      # untouched
        self.assertEqual(reg.get(MP2_OTHER, "Crosshair Index"), "dword:00000000")             # never offered
        self.assertEqual(reg.get(MP2_OTHER, "Subtitles Toggle"), "dword:00000001")
        eng.restore(MP2_APPID)
        self.assertEqual(lib.read_ini(), text.encode())

    def test_the_two_games_skip_with_the_same_word_and_have_their_own_registry_paths(self):
        from skip_launcher.profiles import PROFILES
        self.assertEqual(PROFILES["12140"].skip_args, "-nodialog")
        self.assertEqual(PROFILES["12150"].skip_args, "-nodialog")
        self.assertIn("Max Payne 2", PROFILES["12150"].required_key[0])


if __name__ == "__main__":
    unittest.main()
