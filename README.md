# Skip Launcher

Decky plugin for the Steam Deck. Some Windows games open a launcher window (resolution, quality, "Launch") before the
game starts. On a TV with only a controller that window is a dead end. Skip Launcher makes Steam start the game
itself and moves that window's settings into the plugin, where a controller reaches them.

## How it works
- **Skip the launcher window**: sets the game's Steam launch option so Steam runs the real game executable instead of
  the launcher. No game file is touched, so game updates and "verify files" cannot undo it. Turning it off removes only
  the text this plugin added; other launch options you have stay as they are.
- **Settings**: the choices the launcher window used to save are edited by the plugin, directly in the game's own settings
  file in its Proton prefix. The first time a value is changed the original is recorded; "Put the original settings
  back" restores every value to what it was.
- Nothing is changed while the game is open, installing or updating.

## Supported games
The full list, with how much each game is confirmed and what is not verified yet, is in
[SUPPORTED_GAMES.md](SUPPORTED_GAMES.md) (generated from the code by `tools/gen_supported_games.py`). Today: Batman: Arkham
Asylum GOTY Edition.

Facts per game: `docs/games/`.

## Develop
```bash
python3 -W error::ResourceWarning -m unittest discover -s tests   # backend (stdlib only)
npx tsc --noEmit -p .                                              # UI types
pnpm run build && pnpm run build:zip                               # dist/ and out/skip-launcher-vX.Y.Z.zip
```
The Claude Code agents, skills and hooks used to develop this plugin (all prefixed `sl-`) live in the author's workspace, outside this repository.

## License
BSD-3-Clause.
