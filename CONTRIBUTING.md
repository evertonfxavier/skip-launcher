# Contributing to Skip Launcher

Thank you for wanting to help. This project is young, every game is a new puzzle, and **you do not need to be a programmer to
contribute**. This page shows the ways in, from five minutes to a weekend, and what we expect from every change.

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

| I want to… | Effort | How |
|------------|--------|-----|
| Tell whether a game works on a Deck | 5 min | [Deck report](https://github.com/evertonfxavier/skip-launcher/issues/new?template=deck_report.yml). The most valuable thing you can do: nobody can confirm a game starts and keeps its settings without playing it. |
| Ask for a game | 5 min | [Game request](https://github.com/evertonfxavier/skip-launcher/issues/new?template=game_request.yml) |
| Report a bug | 10 min | [Bug report](https://github.com/evertonfxavier/skip-launcher/issues/new?template=bug_report.yml) |
| Fix a typo, improve the docs, translate | 15 min | Open a pull request (see [Pull requests](#pull-requests)) |
| Translate the plugin into your language | 1 h | [Translate the plugin](#translate-the-plugin) |
| Add support for a game | a few hours | [docs/adding-a-game.md](docs/adding-a-game.md) |
| Improve the engine or the UI | varies | [docs/development.md](docs/development.md) |

Not sure where to start? Open an issue and say what you would like to do: half-formed ideas are welcome.

## Before you write code

1. **Search the [issues](https://github.com/evertonfxavier/skip-launcher/issues)** to see whether someone is already on it.
2. **For anything bigger than a small fix, open an issue first** and say what you plan. It saves you from building something we cannot merge.
3. **Read [docs/safety-rules.md](docs/safety-rules.md).** This tool edits files that belong to people's games. Those rules are not negotiable.

## Set up

You need Node.js 20+, pnpm 9+ and Python 3.9+ (the backend uses only the standard library).

```bash
git clone https://github.com/<your-fork>/skip-launcher.git
cd skip-launcher
pnpm install
python3 -W error::ResourceWarning -m unittest discover -s tests   # should be green before you change anything
```

The [development guide](docs/development.md) explains the project layout, every command, and how to try your build on a real Steam Deck.

## What we expect from every change

- **Tests pass:** `python3 -W error::ResourceWarning -m unittest discover -s tests`, `node --test tests/ui/*.test.mjs` and `npx tsc --noEmit -p .`
- **Safety rules hold** ([docs/safety-rules.md](docs/safety-rules.md)). Anything that writes a settings file or a launch option needs tests for exact undo, for refusing a missing or unreadable file, and for not writing while the game runs.
- **No game files** in the repository: no executables, no copies of a game's ini or registry. Tests use small synthetic fixtures with the real layout.
- **Generated files are regenerated, not edited:** `SUPPORTED_GAMES.md` and the PNGs in `assets/`. Run `python3 tools/gen_supported_games.py` or `pnpm run brand`.
- **English** for code, identifiers, docs and UI strings. If you change the English README, update `README.pt-BR.md` too, or say in the pull request that you could not.
- **Honest docs:** a game's page says what was verified and what was not. "Unconfirmed" is a fine answer.
- **A changelog line** under *Unreleased* in [CHANGELOG.md](CHANGELOG.md) for anything a user would notice.

You do not need to bump the version: maintainers do that when they cut a release.

## Translate the plugin

All text of the panel lives in [`src/i18n/`](src/i18n): `en.json` is the source and `pt-BR.json` is the first translation.

1. Copy `en.json` to `<code>.json` (for example `es.json`) and translate the values. Keep every `{placeholder}` and keep proper names (Steam, Proton, the game titles) as they are.
2. Register the language in `src/i18n/core.ts` (the `Lang` type), `src/i18n/index.ts` and `src/lib/lang.ts` (follow what `pt-BR` does).
3. Run `python3 -W error::ResourceWarning -m unittest discover -s tests`: `tests/test_consistency.py` fails on a missing key or a different placeholder set.
4. Say in the pull request which screens you looked at, if you could.

## Pull requests

1. **Fork** the repository and create a branch from `main` (`fix-typo-in-faq`, `add-some-game`).
2. **Keep it focused.** One topic per pull request is much easier to review than five.
3. **Write clear commits**, in the imperative: `Add Some Game profile`, `Fix undo after a failed write`.
4. **Run the checks** from [What we expect](#what-we-expect-from-every-change). CI runs them again on your pull request.
5. **Open the pull request** and fill in the template. For a new game, include the evidence listed in [docs/adding-a-game.md](docs/adding-a-game.md#8-verify-on-the-real-game) and a screenshot if you have one.
6. **Be patient and kind in review.** We will ask questions; they are about the safety of other people's games, never about you. Push more commits to the same branch; we squash on merge.

Small fixes (typos, links, wording) can go straight to a pull request, no issue needed.

## Releases

Every push to `main` is released automatically: CI tests, builds the zip and creates the GitHub release, bumping the patch version itself when the code moved on. Maintainers only set the version by hand for a bigger change. Details in [docs/development.md](docs/development.md#releases).

## Licensing of contributions

The project is under the [BSD 3-Clause licence](LICENSE). By contributing you agree that your contribution is licensed under the same terms, and that you have the right to submit it (it is your own work, or its licence allows it).

## Security

Found a way this tool could damage a game's settings, or harm a user? Please do **not** open a public issue. Follow [SECURITY.md](SECURITY.md).

## Questions

Open an [issue](https://github.com/evertonfxavier/skip-launcher/issues/new/choose) and say what you are trying to do. There are no silly questions here, and your question usually shows us a gap in the docs.
