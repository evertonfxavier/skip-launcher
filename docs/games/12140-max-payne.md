# Max Payne (appid 12140)

## At a glance
| | |
|--|--|
| Steam appid / install dir | 12140 / `Max Payne` (build 252034, internal library) |
| Skip | launch option `%command% -nodialog`: **proven by hand on the Deck (2026-11-25)**, the game starts without the dialog |
| Settings | Wine registry (`user.reg` of the prefix), edited as text by `regutil.py`; profile `profiles/max_payne.py`, revision 1 |
| Status | **confirmed on a Steam Deck by a player (2026-11-25)**: the game starts without its dialog and the plugin's settings work; the registry edit is also covered by tests on synthetic files and on a copy of a real `user.reg` |
| Summary | Starts Max Payne straight into the game, without its startup dialog, and lets you change the resolution and the gameplay options (auto-aim, auto weapon select, bullet time aid, crosshair, tips) from the plugin with a controller. |
| Support level | confirmed |

- NOT verified: the audio, gamma, LOD and driver values (not offered: their scale is not known).

## How the game starts
- There is **no separate launcher exe**. `maxpayne.exe` (6.3 MB) and `testapp.exe` (5.0 MB, a second build of the same
  engine) both contain the class `CMaxPayneStartupDialog`: the window that opens before the game is the game's own startup
  dialog (resolution, driver, HW acceleration, ...). So the Batman trick (rewrite the exe in Steam's command) does not apply.
- The exe knows the command-line words `nodialog` and `skipstartup` (next to `developer`, `window`, `profile`, `screenshot`
  in its option table). `nodialog` is the community's flag to start without the startup dialog and with the last saved
  settings; `skipstartup` skips the intro movies. **Proven by hand**: a player set `%command% -nodialog` on a Steam Deck (2026-11-25) and the game started straight in.
- The skip is the launch option `%command% -nodialog` (the plugin adds only that text and removes only that text; other options stay).

## Where the dialog keeps its choices
Wine registry of the prefix, `compatdata/12140/pfx/user.reg` (plain text, section names with doubled backslashes), key
`Software\\Remedy Entertainment\\Max Payne\\...`. Written when the dialog is accepted (sections show the time of the last run):
- `Video Settings`: `Display Width`, `Display Height`, `Display Bits Per Pixel` (dword), `Driver` (string), `HW Acceleration Level`,
  `CPU Driver`, `Gamma`, `LOD Bias`, `Mipmap Bias`, `Framerate Smoothness`, `Video Settings Version`.
- `Other Settings`: `AutoAim Toggle`, `AutoWeaponSelect Toggle`, `BulletTimeAid Toggle`, `Crosshair Toggle`, `EnableTips Toggle`.
- `Audio Settings` (`Effects Volume`, `Music Volume`), `Game Level`, `Input Settings` (keyboard/mouse bindings; not needed with a pad).
- Values are `dword:xxxxxxxx` (hex). Example on this Deck: 1920x1080, 16 bits.

## Risks to settle before writing a profile
1. Wine keeps the registry in the wineserver while a game runs and saves it on exit: edit `user.reg` only when no process of the
   prefix is alive (the running guard already checks the install path; add a check for `wineserver` of that prefix).
2. `iniutil` edits ini text. `user.reg` needs its own small reader/writer (section = `[Software\\...]`, `"Key"=dword:...`, timestamp
   lines `#time=` and the `[section] <unix time>` header). Design the adapter and test it on this copy first.
3. Which dialog values matter (a before/after test by the player: change one option in the dialog, see which key changes).

## Next steps
1. Done: the launch option works (player's test).
2. Done in code: `regutil.py`, `launch.enable_args`, the prefix guard, the profile and its tests.
3. Install, then check on the Deck: the panel lists the game, a resolution change lands in `user.reg`, the game honours it,
   Original puts the values back.
