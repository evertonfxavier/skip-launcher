"""Open-source hygiene: the files a contributor expects exist, links work, nothing stale is left behind."""
import json
import re
import struct
import unittest
from pathlib import Path

import fixtures  # noqa: F401  (puts py_modules on sys.path)
from skip_launcher.profiles import PROFILES

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md", "README.pt-BR.md", "LICENSE", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md",
    "CHANGELOG.md", "SUPPORTED_GAMES.md", "docs/README.md", "docs/faq.md", "docs/adding-a-game.md",
    "docs/development.md", "docs/safety-rules.md", "docs/architecture.md", "docs/games/README.md", "docs/games/_template.md",
    "assets/logo.svg", "assets/logo.png", "assets/logo-128.png", "assets/social-preview.png",
    ".github/pull_request_template.md", ".github/dependabot.yml", ".github/workflows/build-plugin.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml", ".github/ISSUE_TEMPLATE/game_request.yml",
    ".github/ISSUE_TEMPLATE/deck_report.yml", ".github/ISSUE_TEMPLATE/config.yml",
    "scripts/ci_version.py", "scripts/ci-build-zip.sh", "tools/gen_supported_games.py", "tools/scaffold_game.py",
]
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)|<img[^>]+src=\"([^\"]+)\"")


def slug(heading):
    text = re.sub(r"[^\w\s-]", "", heading.lower())
    return re.sub(r"\s", "-", text.strip())


def anchors(path):
    found = set()
    in_code = False
    for line in path.read_text().splitlines():
        if line.startswith("```"):
            in_code = not in_code
        elif not in_code and line.startswith("#"):
            found.add(slug(line.lstrip("#").strip()))
    return found


def markdown_files():
    files = [ROOT / n for n in ("README.md", "README.pt-BR.md", "CONTRIBUTING.md", "SECURITY.md",
                                "CHANGELOG.md", "SUPPORTED_GAMES.md", "CODE_OF_CONDUCT.md")]
    files += sorted((ROOT / "docs").rglob("*.md"))
    return [f for f in files if f.exists()]


class RepoHealthTests(unittest.TestCase):
    def test_required_files_exist(self):
        missing = [p for p in REQUIRED if not (ROOT / p).exists()]
        self.assertEqual(missing, [])

    def test_relative_links_resolve(self):
        problems = []
        for md in markdown_files():
            text = re.sub(r"```.*?```", "", md.read_text(), flags=re.S)
            for m in LINK.finditer(text):
                target = m.group(1) or m.group(2)
                if re.match(r"^(https?:|mailto:)", target):
                    continue
                path, _, frag = target.partition("#")
                dest = (md.parent / path).resolve() if path else md
                if path and not dest.exists():
                    problems.append("%s -> %s (missing)" % (md.relative_to(ROOT), target))
                elif frag and dest.suffix == ".md" and frag not in anchors(dest):
                    problems.append("%s -> %s (no such heading)" % (md.relative_to(ROOT), target))
        self.assertEqual(problems, [])

    def test_changelog_mentions_current_version(self):
        version = json.loads((ROOT / "package.json").read_text())["version"]
        self.assertIn("[%s]" % version, (ROOT / "CHANGELOG.md").read_text())
        self.assertRegex((ROOT / "CHANGELOG.md").read_text(), r"(?m)^## \[Unreleased\]")

    def test_license_is_filled_in(self):
        self.assertNotIn("Hypothetical", (ROOT / "LICENSE").read_text())

    def test_logo_png_is_512_square_and_the_others_have_their_size(self):
        data = (ROOT / "assets" / "logo.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", data[16:24]), (512, 512))
        small = (ROOT / "assets" / "logo-128.png").read_bytes()
        self.assertEqual(struct.unpack(">II", small[16:24]), (128, 128))
        social = (ROOT / "assets" / "social-preview.png").read_bytes()
        self.assertEqual(struct.unpack(">II", social[16:24]), (1280, 640))

    def test_plugin_json_image_points_to_logo(self):
        image = json.loads((ROOT / "plugin.json").read_text())["publish"]["image"]
        self.assertTrue(image.endswith("/skip-launcher/main/assets/logo.png"), image)

    def test_package_json_has_repository_metadata(self):
        pkg = json.loads((ROOT / "package.json").read_text())
        for key in ("repository", "bugs", "homepage", "license"):
            self.assertIn(key, pkg)
        self.assertIn("skip-launcher", pkg["homepage"])

    def test_issue_forms_are_linked_templates_that_exist(self):
        linked = (ROOT / "README.md").read_text() + (ROOT / "SUPPORTED_GAMES.md").read_text()
        for n in ("game_request.yml", "deck_report.yml", "bug_report.yml"):
            self.assertTrue((ROOT / ".github" / "ISSUE_TEMPLATE" / n).exists())
            self.assertIn("template=" + n, linked)

    def test_every_registered_game_has_a_page_and_a_row_in_the_catalog(self):
        index = (ROOT / "docs" / "games" / "README.md").read_text()
        for appid, profile in PROFILES.items():
            pages = list((ROOT / "docs" / "games").glob("%s-*.md" % appid))
            self.assertEqual(len(pages), 1, "docs/games/%s-*.md" % appid)
            self.assertIn("](%s)" % pages[0].name, index, "docs/games/README.md has no row for %s" % profile.name)

    def test_every_tool_compiles_and_mentioned_tools_exist(self):
        tools = sorted((ROOT / "tools").glob("*.py"))
        self.assertTrue(tools)
        for tool in tools:
            compile(tool.read_text(), str(tool), "exec")
        names = set()
        for md in markdown_files():
            names.update(re.findall(r"\btools/([a-z_]+\.py)", md.read_text()))
        missing = sorted(n for n in names if not (ROOT / "tools" / n).exists())
        self.assertEqual(missing, [])

    def test_the_workflow_builds_the_zip_this_project_ships(self):
        text = (ROOT / ".github" / "workflows" / "build-plugin.yml").read_text()
        self.assertIn("skip-launcher-v", text)
        self.assertIn("py_modules/skip_launcher/engine.py", text)
        self.assertNotIn("button-glyphs", text.lower())
        self.assertNotIn("button glyphs", text.lower())


if __name__ == "__main__":
    unittest.main()
