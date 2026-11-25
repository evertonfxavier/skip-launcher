"""Ties the backend to the UI catalogs: a status code or a setting the UI cannot translate fails here."""
import json
import os
import re
import unittest

import fixtures  # noqa: F401
from skip_launcher import status_codes
from skip_launcher.profiles import PROFILES

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def catalog(lang):
    with open(os.path.join(ROOT, "src", "i18n", lang + ".json"), encoding="utf-8") as f:
        return json.load(f)


class CatalogTests(unittest.TestCase):
    def test_catalogs_have_the_same_keys(self):
        en, pt = catalog("en"), catalog("pt-BR")
        self.assertEqual(sorted(en), sorted(pt))
        for key, value in pt.items():
            self.assertEqual(sorted(re.findall(r"\{\w+\}", value)), sorted(re.findall(r"\{\w+\}", en[key])), key)

    def test_every_code_is_translated_and_every_engine_code_is_listed(self):
        en = catalog("en")
        for code in status_codes.CODES:
            self.assertIn("code." + code, en)
        with open(os.path.join(ROOT, "py_modules", "skip_launcher", "engine.py"), encoding="utf-8") as f:
            used = set(re.findall(r'_status\(\s*"[a-z]+",\s*"([a-z_]+)"', f.read()))
        self.assertTrue(used)
        self.assertLessEqual(used, set(status_codes.CODES))
        self.assertLessEqual({"ok", "running", "no_config", "write_failed"}, used)

    def test_every_setting_has_a_translated_name_and_option_labels_where_not_numeric(self):
        for lang in ("en", "pt-BR"):
            cat = catalog(lang)
            for profile in PROFILES.values():
                for s in profile.settings:
                    self.assertIn("setting." + s.id, cat, s.id)
                    self.assertIn("group." + s.group, cat)
                    if s.note_key:
                        self.assertIn(s.note_key, cat)
                    if s.kind == "choice" and s.id != "resolution":
                        for o in s.options:
                            if not re.fullmatch(r"\d+x", o.id):
                                self.assertIn("option.%s.%s" % (s.id, o.id), cat, (s.id, o.id))


class ProfileTests(unittest.TestCase):
    def test_profile_facts(self):
        for appid, p in PROFILES.items():
            self.assertEqual(appid, p.appid)
            self.assertTrue(p.launcher_exe.endswith(".exe") and p.game_exe.endswith(".exe"))
            if p.skip_args:                       # the window is a dialog of the game exe: nothing to swap
                self.assertEqual(p.launcher_exe, p.game_exe)
                self.assertTrue(p.skip_args.startswith("-"))
            else:
                self.assertNotEqual(p.launcher_exe, p.game_exe)
            self.assertIn(p.config_format, ("ini", "reg"))
            if p.config_format == "reg":
                self.assertTrue(p.required_section)
            self.assertFalse(os.path.isabs(p.config_rel))
            ids = [s.id for s in p.settings]
            self.assertEqual(len(ids), len(set(ids)))
            for s in p.settings:
                oids = [o.id for o in s.options]
                self.assertEqual(len(oids), len(set(oids)), s.id)
                self.assertTrue(all(o.entries for o in s.options))

    def test_options_of_one_setting_never_look_alike(self):
        """Two options with the same entries could never be told apart when reading the file."""
        for p in PROFILES.values():
            for s in p.settings:
                seen = [tuple(o.entries) for o in s.options]
                self.assertEqual(len(seen), len(set(seen)), s.id)


if __name__ == "__main__":
    unittest.main()
