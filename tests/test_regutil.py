import unittest

import fixtures  # noqa: F401
from fixtures import USER_REG
from skip_launcher.regutil import RegError, RegText

VIDEO = r"Software\\Remedy Entertainment\\Max Payne\\Video Settings"
OTHER = r"Software\\Remedy Entertainment\\Max Payne\\Other Settings"


def reg(text=USER_REG):
    return RegText(text.encode())


class RegTextTests(unittest.TestCase):
    def test_an_untouched_document_is_byte_identical(self):
        self.assertEqual(reg().dumps(), USER_REG.encode())
        crlf = USER_REG.replace("\n", "\r\n")
        self.assertEqual(RegText(crlf.encode()).dumps(), crlf.encode())

    def test_reads_values_without_case_and_returns_none_for_missing(self):
        r = reg()
        self.assertEqual(r.get(VIDEO, "Display Width"), "dword:00000780")
        self.assertEqual(r.get(VIDEO.upper(), "display width"), "dword:00000780")
        self.assertEqual(r.get(VIDEO, "Driver"), '"ATI Radeon HD 5600 Series"')
        self.assertIsNone(r.get(VIDEO, "Nope"))
        self.assertIsNone(r.get(r"Software\\Nothing", "Display Width"))

    def test_set_changes_only_that_line(self):
        r = reg()
        r.set(VIDEO, "Display Width", "dword:00000500")
        old, new = USER_REG.splitlines(), r.dumps().decode().splitlines()
        self.assertEqual(len(old), len(new))
        diff = [(a, b) for a, b in zip(old, new) if a != b]
        self.assertEqual(diff, [('"Display Width"=dword:00000780', '"Display Width"=dword:00000500')])

    def test_a_key_is_not_found_in_the_neighbouring_section(self):
        r = reg()
        self.assertIsNone(r.get(OTHER, "Display Width"))
        self.assertEqual(r.get(OTHER, "AutoAim Toggle"), "dword:00000001")

    def test_a_new_key_goes_at_the_end_of_its_section_before_the_blank_line(self):
        r = reg()
        r.set(OTHER, "Extra", "dword:00000002")
        lines = r.dumps().decode().splitlines()
        i = lines.index('"Extra"=dword:00000002')
        self.assertEqual(lines[i - 1], '"Other Settings Version"=dword:00000002')
        self.assertEqual(lines[i + 1], "")
        self.assertTrue(lines[i + 2].startswith("[Software\\\\Remedy Entertainment\\\\Max Payne\\\\Video"))
        r.remove(OTHER, "Extra")
        self.assertEqual(r.dumps(), USER_REG.encode())

    def test_a_missing_section_is_never_created(self):
        r = reg()
        self.assertFalse(r.has_section(r"Software\\Nothing"))
        with self.assertRaises(RegError):
            r.set(r"Software\\Nothing", "A", "dword:00000001")
        self.assertEqual(r.dumps(), USER_REG.encode())

    def test_line_breaks_and_bad_bytes_are_refused(self):
        with self.assertRaises(RegError):
            reg().set(VIDEO, "Display Width", "dword:1\n[evil]")
        with self.assertRaises(RegError):
            RegText(b"\xff\xfe\x00")

    def test_timestamps_and_other_sections_are_kept(self):
        r = reg()
        r.set(VIDEO, "Display Height", "dword:000002d0")
        text = r.dumps().decode()
        self.assertIn("[Software\\\\Remedy Entertainment\\\\Max Payne\\\\Video Settings] 1795560333\n#time=1dd7c6583a4a9ea", text)
        self.assertIn('"SteamPath"="C:\\\\Program Files (x86)\\\\Steam"', text)


if __name__ == "__main__":
    unittest.main()
