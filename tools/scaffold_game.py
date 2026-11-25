#!/usr/bin/env python3
r"""Create the starting files for a new game: a profile skeleton and a page in docs/games/.

    python3 tools/scaffold_game.py --appid 12345 --name "Some Game" --launcher Launcher.exe --game Game.exe
    python3 tools/scaffold_game.py --appid 12345 --name "Some Game" --skip-args=-nodialog --format reg --config-rel user.reg
                                   --required-section 'Software\\Vendor\\Some Game\\Video Settings'
    python3 tools/scaffold_game.py ... --dry-run          print what would be written, write nothing

It never overwrites a file and never registers the game: `profiles/__init__.py` is yours to edit once the facts in the profile
are real. Until the page has its Summary and Support level rows and the game is listed in docs/games/README.md, the tests fail on
purpose (docs/adding-a-game.md, step 5).
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROFILE = '''"""{name} (appid {appid}).

TODO: say how Steam starts the game, what the real program is, where the launcher keeps its choices and how you know.
Facts and the manual test: docs/games/{appid}-{slug_dash}.md
"""
from .base import Option, Profile, Setting  # noqa: F401  (used once you add settings)


class {cls}(Profile):
    appid = "{appid}"
    name = "{name}"
    revision = 1
    support = "full"
    launcher_exe = "{launcher}"{skip_line}
    game_exe = "{game}"
    config_rel = "{config_rel}"           # relative to the Proton prefix (pfx/)
    config_format = "{fmt}"{required_line}

    # TODO: only values you have SEEN in the real file or in the launcher's own presets (docs/safety-rules.md, rule 11).
    settings = ()


PROFILE = {cls}()
'''


def camel(slug):
    return "".join(part.capitalize() for part in re.split(r"[_\-]+", slug) if part)


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def build(args):
    slug = args.slug or slugify(args.name)
    if not re.fullmatch(r"[a-z][a-z0-9_]*", slug):
        raise ValueError("slug %r must be lowercase letters, digits and underscores" % slug)
    if not args.appid.isdigit():
        raise ValueError("--appid must be the number in the Steam store URL")
    if not args.launcher.lower().endswith(".exe") or not (args.game or args.launcher).lower().endswith(".exe"):
        raise ValueError("--launcher and --game are .exe file names")
    if args.skip_args and not args.skip_args.startswith("-"):
        raise ValueError("--skip-args is a command-line switch such as -nodialog")
    game = args.game or args.launcher
    if not args.skip_args and game == args.launcher:
        raise ValueError("without --skip-args the launcher and the game must be two different programs")
    if args.format == "reg" and not args.required_section:
        raise ValueError("a registry game needs --required-section (the key that exists once its window ran)")
    skip_line = '\n    skip_args = "%s"                      # the window is a dialog of the game exe: add this switch' % args.skip_args \
        if args.skip_args else ""
    required_line = '\n    required_section = %r' % args.required_section if args.required_section else ""
    profile = PROFILE.format(
        name=args.name, appid=args.appid, slug_dash=slug.replace("_", "-"), cls=camel(slug), launcher=args.launcher, game=game,
        config_rel=args.config_rel, fmt=args.format, skip_line=skip_line, required_line=required_line)
    template = (ROOT / "docs" / "games" / "_template.md").read_text()
    page = template.replace("GAME NAME", args.name).replace("00000", args.appid)
    return slug, profile, page


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--appid", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--slug", help="module name, default: the game name in snake_case")
    ap.add_argument("--launcher", default="Launcher.exe", help="the program Steam starts (the window)")
    ap.add_argument("--game", help="the real game program (default: same as --launcher, for a dialog inside the game)")
    ap.add_argument("--skip-args", help="a switch that skips the window, written with an equals sign: --skip-args=-nodialog "
                    "(no executable swap then)")
    ap.add_argument("--format", choices=("ini", "reg"), default="ini")
    ap.add_argument("--config-rel", default="drive_c/users/steamuser/Documents/TODO/Settings.ini",
                    help="the settings file relative to the Proton prefix (pfx/)")
    ap.add_argument("--required-section", help="a section that exists once the game's window ran at least once")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root)
    try:
        slug, profile, page = build(args)
    except ValueError as exc:
        print("error:", exc, file=sys.stderr)
        return 2
    targets = [(root / "py_modules" / "skip_launcher" / "profiles" / (slug + ".py"), profile),
               (root / "docs" / "games" / ("%s-%s.md" % (args.appid, slug.replace("_", "-"))), page)]
    clash = [p for p, _ in targets if p.exists()]
    if clash:
        print("error: refusing to overwrite:", ", ".join(str(p.relative_to(root)) for p in clash), file=sys.stderr)
        return 1
    for path, text in targets:
        print(("would write " if args.dry_run else "wrote ") + str(path.relative_to(root)))
        if not args.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print("\nNext: fill in the facts, register the profile in py_modules/skip_launcher/profiles/__init__.py, add the game to\n"
          "docs/games/README.md, add its strings to src/i18n/en.json and pt-BR.json, write tests, then run\n"
          "python3 tools/gen_supported_games.py. See docs/adding-a-game.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
