"""The version logic of the release pipeline (scripts/ci_version.py): no network, no git."""
import importlib.util
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ci_version.py"
spec = importlib.util.spec_from_file_location("ci_version", SCRIPT)
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)

HEAD = "a" * 40
OLD = "b" * 40


def tags(*pairs):
    return {"v" + v: sha for v, sha in pairs}


class DecideTest(unittest.TestCase):
    def test_a_version_without_a_tag_is_released_as_declared(self):
        self.assertEqual(ci.decide("0.4.0", HEAD, tags(("0.3.1", OLD))), ("0.4.0", False))

    def test_no_tags_at_all(self):
        self.assertEqual(ci.decide("0.1.0", HEAD, {}), ("0.1.0", False))

    def test_a_rerun_of_the_released_commit_changes_nothing(self):
        self.assertEqual(ci.decide("0.3.1", HEAD, tags(("0.3.1", HEAD))), ("0.3.1", False))

    def test_a_new_commit_on_a_released_version_gets_the_next_patch(self):
        self.assertEqual(ci.decide("0.3.1", HEAD, tags(("0.3.1", OLD))), ("0.3.2", True))

    def test_taken_patch_numbers_are_skipped(self):
        taken = tags(("0.3.1", OLD), ("0.3.2", OLD), ("0.3.3", OLD))
        self.assertEqual(ci.decide("0.3.1", HEAD, taken), ("0.3.4", True))

    def test_minor_and_major_stay_put(self):
        self.assertEqual(ci.decide("1.2.9", HEAD, tags(("1.2.9", OLD))), ("1.2.10", True))

    def test_a_prerelease_is_never_bumped(self):
        self.assertEqual(ci.decide("0.4.0-beta.1", HEAD, tags(("0.4.0-beta.1", OLD))), ("0.4.0-beta.1", False))

    def test_a_version_that_is_not_semver_is_refused(self):
        with self.assertRaises(ValueError):
            ci.decide("latest", HEAD, {})


class ParseTagsTest(unittest.TestCase):
    def test_lightweight_and_annotated_tags(self):
        out = "\n".join([
            "%s\trefs/tags/v0.3.1" % OLD,
            "%s\trefs/tags/v0.3.2" % ("c" * 40),
            "%s\trefs/tags/v0.3.2^{}" % HEAD,            # annotated: the peeled commit is the one that counts
            "%s\trefs/heads/main" % HEAD,                # not a tag
            "garbage",
        ])
        parsed = ci.parse_tags(out)
        self.assertEqual(parsed, {"v0.3.1": OLD, "v0.3.2": HEAD})


class ApplyTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, "package.json")

    def write(self, text):
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            f.write(text)

    def read(self):
        with open(self.path, "r", encoding="utf-8", newline="") as f:
            return f.read()

    def test_only_the_version_field_changes(self):
        before = '{\n  "name": "x",\n  "version": "0.3.1",\n  "dependencies": {"version": "9.9.9"}\n}\n'
        self.write(before)
        ci.apply_version(self.path, "0.3.2")
        self.assertEqual(self.read(), before.replace('"version": "0.3.1"', '"version": "0.3.2"'))

    def test_a_file_without_a_version_is_an_error(self):
        self.write('{"name": "x"}\n')
        with self.assertRaises(ValueError):
            ci.apply_version(self.path, "0.3.2")
        self.assertEqual(self.read(), '{"name": "x"}\n')

    def test_a_bad_version_is_refused_and_the_file_untouched(self):
        self.write('{"version": "0.3.1"}\n')
        with self.assertRaises(ValueError):
            ci.apply_version(self.path, "0.3")
        self.assertEqual(self.read(), '{"version": "0.3.1"}\n')


CHANGELOG = """# Changelog

## [Unreleased]

### Added
- A new thing.

## [0.3.1]

First published release.

[Unreleased]: https://github.com/o/r/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/o/r/releases/tag/v0.3.1
"""


class ChangelogTest(unittest.TestCase):
    def test_unreleased_becomes_the_new_version(self):
        out = ci.promote_changelog(CHANGELOG, "0.3.2", "2026-11-24")
        self.assertIn("## [Unreleased]\n\n## [0.3.2] - 2026-11-24\n\n### Added\n- A new thing.", out)
        self.assertIn("[Unreleased]: https://github.com/o/r/compare/v0.3.2...HEAD", out)
        self.assertIn("[0.3.2]: https://github.com/o/r/compare/v0.3.1...v0.3.2", out)
        self.assertIn("[0.3.1]: https://github.com/o/r/releases/tag/v0.3.1", out)   # old link kept
        self.assertEqual(out.count("## [Unreleased]"), 1)

    def test_promoting_twice_changes_nothing(self):
        once = ci.promote_changelog(CHANGELOG, "0.3.2", "2026-11-24")
        self.assertEqual(ci.promote_changelog(once, "0.3.2", "2026-11-25"), once)

    def test_a_changelog_without_unreleased_is_an_error(self):
        with self.assertRaises(ValueError):
            ci.promote_changelog("# Changelog\n\n## [0.3.1]\n", "0.3.2", "2026-11-24")

    def test_without_a_compare_link_the_sections_still_move(self):
        out = ci.promote_changelog("## [Unreleased]\n\n- x\n", "0.3.2", "2026-11-24")
        self.assertIn("## [0.3.2] - 2026-11-24", out)

    def test_stamp_writes_both_files_or_neither(self):
        with tempfile.TemporaryDirectory() as d:
            pkg, log = os.path.join(d, "package.json"), os.path.join(d, "CHANGELOG.md")
            with open(pkg, "w") as f:
                f.write('{"version": "0.3.1"}\n')
            with open(log, "w") as f:
                f.write("# no unreleased section here\n")
            with self.assertRaises(ValueError):
                ci.stamp("0.3.2", "2026-11-24", pkg, log)
            with open(pkg) as f:                                  # nothing half-done
                self.assertEqual(f.read(), '{"version": "0.3.1"}\n')
            with open(log, "w") as f:
                f.write(CHANGELOG)
            ci.stamp("0.3.2", "2026-11-24", pkg, log)
            with open(pkg) as f:
                self.assertEqual(f.read(), '{"version": "0.3.2"}\n')
            with open(log) as f:
                self.assertIn("## [0.3.2] - 2026-11-24", f.read())

    def test_the_real_changelog_satisfies_the_health_test_after_a_bump(self):
        """The repository-health test wants '[<package.json version>]' in CHANGELOG.md: a bump must keep it true."""
        root = Path(__file__).resolve().parents[1]
        real = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## [Unreleased]", real)
        self.assertIn("[0.99.0]", ci.promote_changelog(real, "0.99.0", "2026-01-01"))


class EmptyNotesTest(unittest.TestCase):
    def test_detects_an_empty_unreleased_section(self):
        self.assertTrue(ci.unreleased_is_empty("## [Unreleased]\n\n## [0.3.3] - d\n\nx\n"))
        self.assertTrue(ci.unreleased_is_empty("## [Unreleased]\n\n[Unreleased]: https://x/compare/v1.0.0...HEAD\n"))
        self.assertTrue(ci.unreleased_is_empty("## [Unreleased]\n"))

    def test_notes_under_unreleased_are_notes(self):
        self.assertFalse(ci.unreleased_is_empty("## [Unreleased]\n\n### Added\n- a thing\n\n## [0.3.3]\n"))

    def test_no_unreleased_section_is_not_reported_as_empty(self):
        self.assertFalse(ci.unreleased_is_empty("# Changelog\n\n## [0.3.3]\n"))

    def test_stamp_reports_whether_the_release_has_notes(self):
        with tempfile.TemporaryDirectory() as d:
            pkg, log = os.path.join(d, "package.json"), os.path.join(d, "CHANGELOG.md")
            with open(pkg, "w") as f:
                f.write('{"version": "0.3.1"}\n')
            with open(log, "w") as f:
                f.write("## [Unreleased]\n\n## [0.3.1]\n")
            self.assertFalse(ci.stamp("0.3.2", "2026-11-24", pkg, log))       # still stamped, but flagged
            with open(log) as f:
                self.assertIn("## [0.3.2] - 2026-11-24", f.read())
            with open(log, "w") as f:
                f.write("## [Unreleased]\n\n- a note\n\n## [0.3.2]\n")
            self.assertTrue(ci.stamp("0.3.3", "2026-11-24", pkg, log))

    def test_the_cli_prints_a_warning_annotation_and_still_succeeds(self):
        with tempfile.TemporaryDirectory() as d:
            pkg, log = os.path.join(d, "package.json"), os.path.join(d, "CHANGELOG.md")
            with open(pkg, "w") as f:
                f.write('{"version": "0.3.1"}\n')
            with open(log, "w") as f:
                f.write("## [Unreleased]\n\n## [0.3.1]\n")
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = ci.main(["stamp", "--version", "0.3.2", "--date", "2026-11-24", "--package", pkg, "--changelog", log])
        self.assertEqual(code, 0)
        self.assertIn("::warning title=Release v0.3.2 has no notes::", out.getvalue())

    def test_the_cli_is_quiet_when_there_are_notes(self):
        with tempfile.TemporaryDirectory() as d:
            pkg, log = os.path.join(d, "package.json"), os.path.join(d, "CHANGELOG.md")
            with open(pkg, "w") as f:
                f.write('{"version": "0.3.1"}\n')
            with open(log, "w") as f:
                f.write("## [Unreleased]\n\n### Added\n- x\n\n## [0.3.1]\n")
            out = io.StringIO()
            with redirect_stdout(out):
                ci.main(["stamp", "--version", "0.3.2", "--date", "2026-11-24", "--package", pkg, "--changelog", log])
        self.assertNotIn("::warning", out.getvalue())


class CliTest(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = ci.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_decide_prints_github_output_lines(self):
        with tempfile.TemporaryDirectory() as d:
            tag_file = os.path.join(d, "tags.txt")
            with open(tag_file, "w") as f:
                f.write("%s\trefs/tags/v0.3.1\n" % OLD)
            code, out, _ = self.run_cli("decide", "--version", "0.3.1", "--head", HEAD, "--tags", tag_file)
        self.assertEqual(code, 0)
        self.assertEqual(out.split(), ["version=0.3.2", "bump=true"])

    def test_missing_tags_file_is_a_clean_error(self):
        code, _, err = self.run_cli("decide", "--version", "0.3.1", "--head", HEAD, "--tags", "/nonexistent/tags")
        self.assertEqual(code, 1)
        self.assertIn("ci_version", err)


if __name__ == "__main__":
    unittest.main()
