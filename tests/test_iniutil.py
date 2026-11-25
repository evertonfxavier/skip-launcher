import unittest

from fixtures import USER_ENGINE, utf16  # noqa: F401  (also puts py_modules on sys.path)
from skip_launcher.iniutil import IniError, IniText


class IniTextTests(unittest.TestCase):
    def test_untouched_roundtrip_is_byte_identical(self):
        for raw in (utf16(USER_ENGINE), USER_ENGINE.encode("utf-8"), b"\xef\xbb\xbf" + USER_ENGINE.encode("utf-8"),
                    utf16(USER_ENGINE.replace("\r\n", "\n")), utf16(USER_ENGINE.rstrip("\r\n"))):
            self.assertEqual(IniText(raw).dumps(), raw)

    def test_get_is_case_insensitive_and_missing_is_default(self):
        ini = IniText(utf16(USER_ENGINE))
        self.assertEqual(ini.get("systemsettings", "resx"), "1920")
        self.assertEqual(ini.get("SystemSettings", "Nope", "x"), "x")
        self.assertIsNone(ini.get("Nope", "ResX"))

    def test_set_changes_only_that_line_and_keeps_utf16_crlf(self):
        raw = utf16(USER_ENGINE)
        ini = IniText(raw)
        ini.set("SystemSettings", "ResX", "1280")
        out = ini.dumps()
        self.assertTrue(out.startswith(b"\xff\xfe"))
        self.assertEqual(out.decode("utf-16"), USER_ENGINE.replace("ResX=1920", "ResX=1280"))

    def test_same_key_in_another_section_is_left_alone(self):
        ini = IniText(("[A]\r\nX=1\r\n\r\n[B]\r\nX=2\r\n").encode())
        ini.set("B", "X", "9")
        self.assertEqual(ini.dumps().decode(), "[A]\r\nX=1\r\n\r\n[B]\r\nX=9\r\n")

    def test_new_key_goes_at_the_end_of_its_section_before_the_blank_line(self):
        ini = IniText(("[A]\r\nX=1\r\n\r\n[B]\r\nY=2\r\n").encode())
        ini.set("A", "Z", "3")
        self.assertEqual(ini.dumps().decode(), "[A]\r\nX=1\r\nZ=3\r\n\r\n[B]\r\nY=2\r\n")

    def test_new_key_in_last_section_without_trailing_newline(self):
        ini = IniText(b"[A]\r\nX=1")
        ini.set("A", "Z", "3")
        self.assertEqual(ini.dumps(), b"[A]\r\nX=1\r\nZ=3\r\n")

    def test_new_section_is_appended(self):
        ini = IniText(b"[A]\r\nX=1\r\n")
        ini.set("New", "K", "v")
        self.assertEqual(ini.dumps(), b"[A]\r\nX=1\r\n\r\n[New]\r\nK=v\r\n")

    def test_remove_and_comments(self):
        ini = IniText(b"[A]\r\n;X=0\r\nX=1\r\n")
        self.assertEqual(ini.get("A", "X"), "1")
        self.assertTrue(ini.remove("A", "X"))
        self.assertFalse(ini.remove("A", "X"))
        self.assertEqual(ini.dumps(), b"[A]\r\n;X=0\r\n")

    def test_value_with_line_break_is_refused(self):
        with self.assertRaises(IniError):
            IniText(b"[A]\r\n").set("A", "X", "1\r\n[Evil]")

    def test_undecodable_file_is_an_error(self):
        with self.assertRaises(IniError):
            IniText(b"\xff\xfe\x00")                       # odd number of bytes after the BOM


if __name__ == "__main__":
    unittest.main()
