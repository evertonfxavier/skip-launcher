#!/usr/bin/env python3
"""Version logic of the release pipeline (.github/workflows/build-plugin.yml). Stdlib only.

Every push to main is released. The version in package.json is what the maintainer last declared:

  * no release/tag for it yet            -> release exactly that version (a manual bump still works)
  * its tag already points at this commit -> nothing to change (a re-run of the same commit)
  * its tag exists at another commit      -> the code moved on without a new version: use the next
                                             free patch version (0.3.1 -> 0.3.2, and so on)
  * a pre-release (X.Y.Z-beta.1)          -> never bumped automatically

  ci_version.py decide --version 0.3.1 --head <sha> --tags <git ls-remote --tags output>
      prints  version=<X.Y.Z>  and  bump=true|false  (GITHUB_OUTPUT format)
  ci_version.py apply --version 0.3.2 [--file package.json]
      rewrites only the "version" field of the file, keeping the rest byte for byte
  ci_version.py stamp --version 0.3.2 --date 2026-11-24
      apply + move CHANGELOG.md's [Unreleased] section to [0.3.2] (what an automatic bump changes)
"""
import argparse
import re
import sys

PLAIN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$")
VERSION_FIELD = re.compile(r'("version"\s*:\s*")([^"]*)(")')


def parse_tags(text):
    """{tag name: commit sha} from `git ls-remote --tags` output; peeled (^{}) entries win."""
    tags, peeled = {}, {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 2 or not parts[1].startswith("refs/tags/"):
            continue
        sha, name = parts[0], parts[1][len("refs/tags/"):]
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
        else:
            tags[name] = sha
    tags.update(peeled)
    return tags


def decide(version, head, tags):
    """-> (version to release, bump?)"""
    if not SEMVER.match(version):
        raise ValueError("package.json version %r is not semver" % version)
    tag = "v" + version
    if tag not in tags or tags[tag] == head:
        return version, False
    match = PLAIN.match(version)
    if not match:                      # a pre-release is released as declared, never bumped
        return version, False
    major, minor, patch = (int(n) for n in match.groups())
    while True:
        patch += 1
        candidate = "%d.%d.%d" % (major, minor, patch)
        if "v" + candidate not in tags:
            return candidate, True


def apply_version(path, version):
    """Rewrite the first "version" field of a JSON file in place, touching nothing else."""
    if not SEMVER.match(version):
        raise ValueError("%r is not semver" % version)
    with open(path, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    new, count = VERSION_FIELD.subn(lambda m: m.group(1) + version + m.group(3), text, count=1)
    if count != 1:
        raise ValueError("no version field in %s" % path)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new)


UNRELEASED = re.compile(r"^## \[Unreleased\][ \t]*$", re.M)
UNRELEASED_LINK = re.compile(
    r"^\[Unreleased\]: (\S+?)/compare/v(\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?)\.\.\.HEAD[ \t]*$", re.M)


def promote_changelog(text, version, date):
    """Keep a Changelog release step: what sits under [Unreleased] becomes [version] - date.

    Also moves the [Unreleased] compare link and adds the [version] one. The repository-health test
    requires a section for the version in package.json, so an automatic bump has to write it too."""
    if re.search(r"^## \[%s\]" % re.escape(version), text, re.M):
        return text                                      # already promoted
    if not UNRELEASED.search(text):
        raise ValueError("CHANGELOG.md has no '## [Unreleased]' section to promote")
    text = UNRELEASED.sub("## [Unreleased]\n\n## [%s] - %s" % (version, date), text, count=1)
    link = UNRELEASED_LINK.search(text)
    if link:
        base, previous = link.group(1), link.group(2)
        replacement = "[Unreleased]: %s/compare/v%s...HEAD\n[%s]: %s/compare/v%s...v%s" % (
            base, version, version, base, previous, version)
        text = text[:link.start()] + replacement + text[link.end():]
    return text


def unreleased_is_empty(text):
    """True when `## [Unreleased]` holds no line of content (the release would have no notes)."""
    match = UNRELEASED.search(text)
    if not match:
        return False
    rest = text[match.end():]
    nxt = re.search(r"^(## \[|\[[^\]]+\]: )", rest, re.M)
    body = rest[:nxt.start()] if nxt else rest
    return not body.strip()


def stamp(version, date, package="package.json", changelog="CHANGELOG.md"):
    """Everything an automatic version bump changes: package.json and the changelog.

    Returns True when the release has notes, False when `Unreleased` was empty (the section is still
    created, so the repository-health test passes, but the release goes out without a word about it)."""
    with open(changelog, "r", encoding="utf-8", newline="") as f:
        old = f.read()
    had_notes = not unreleased_is_empty(old)
    new = promote_changelog(old, version, date)        # raises before anything is written
    apply_version(package, version)
    with open(changelog, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    return had_notes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("decide")
    d.add_argument("--version", required=True)
    d.add_argument("--head", required=True)
    d.add_argument("--tags", required=True, help="file with `git ls-remote --tags origin` output")
    a = sub.add_parser("apply")
    a.add_argument("--version", required=True)
    a.add_argument("--file", default="package.json")
    s = sub.add_parser("stamp", help="apply + promote the changelog: all an automatic bump changes")
    s.add_argument("--version", required=True)
    s.add_argument("--date", required=True, help="YYYY-MM-DD")
    s.add_argument("--package", default="package.json")
    s.add_argument("--changelog", default="CHANGELOG.md")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "stamp":
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
                raise ValueError("--date must be YYYY-MM-DD")
            had_notes = stamp(args.version, args.date, args.package, args.changelog)
            print("%s and %s now say %s" % (args.package, args.changelog, args.version))
            if not had_notes:       # a GitHub Actions annotation; it never fails the release
                print("::warning title=Release v%s has no notes::CHANGELOG.md [Unreleased] was empty. "
                      "Put the user-visible lines there in the same commit as the change." % args.version)
        elif args.cmd == "decide":
            with open(args.tags, "r", encoding="utf-8") as f:
                version, bump = decide(args.version, args.head, parse_tags(f.read()))
            print("version=%s" % version)
            print("bump=%s" % ("true" if bump else "false"))
        else:
            apply_version(args.file, args.version)
            print("%s now says %s" % (args.file, args.version))
    except (ValueError, OSError) as e:
        print("ci_version: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
