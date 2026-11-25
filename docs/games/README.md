# Game catalog

One page per game, named `<appid>-<slug>.md`. A page holds **facts about that game**: how it starts, where its launcher keeps its
choices, which values were seen, what was and was not verified. Generic lessons belong in the main [docs](../README.md).

| appid | Game | Skips with | Settings in | Profile | Page |
|-------|------|------------|-------------|---------|------|
| 35140 | Batman: Arkham Asylum GOTY Edition | swap `BmLauncher.exe` for `ShippingPC-BmGame.exe` | `UserEngine.ini` (UTF-16) | `batman_aa.py` | [35140](35140-batman-arkham-asylum.md) |
| 12140 | Max Payne | `-nodialog` | Wine registry (`user.reg`) | `max_payne.py` | [12140](12140-max-payne.md) |
| 12150 | Max Payne 2: The Fall of Max Payne | `-nodialog` | Wine registry (`user.reg`) | `max_payne_2.py` | [12150](12150-max-payne-2.md) |

Keep this table in sync with `PROFILES` (a test fails when a game is missing here). The support level of each game, which feeds
[SUPPORTED_GAMES.md](../../SUPPORTED_GAMES.md), is a row of its page.

## Adding a page

`python3 tools/scaffold_game.py --appid <id> --name "<Game>" ...` creates the profile skeleton and a page from
[`_template.md`](_template.md). Fill every section; write "unknown" rather than guess. The full walk-through is in
[adding-a-game.md](../adding-a-game.md).
