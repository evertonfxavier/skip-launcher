# Max Payne 2: The Fall of Max Payne (appid 12150)

## At a glance
| | |
|--|--|
| Steam appid / install dir | 12150 / `Max Payne 2 The Fall of Max Payne` (build 252035, internal library) |
| Skip | launch option `%command% -nodialog`: **proven by hand on the Deck (2026-11-25)**, the game started straight in |
| Settings | Wine registry like Max Payne 1, key names **read from the real `user.reg`** after the game ran; profile `profiles/max_payne_2.py`, revision 2: resolution, auto-aim, auto weapon select, bullet time aid, tips, subtitles |
| Status | plugin 0.2.0 installed on the Deck (2026-11-25); the panel and the settings are **not tested in the plugin UI yet** |
| Summary | Starts Max Payne 2 straight into the game, without its startup dialog, and lets you change the resolution and the gameplay options (auto-aim, auto weapon select, bullet time aid, tips, subtitles) from the plugin with a controller. |
| Support level | partly confirmed |

- NOT verified: that the game applies a resolution written by the plugin (the player proved the skip, not the settings).
- NOT verified: the crosshair (`Crosshair Index`, values unknown) and the video quality values (gamma, LOD, bits per pixel, driver) are not offered.

## How the game starts
- Same engine family as `12140-max-payne.md`: `maxpayne2.exe` (1.8 MB) and `testapp.exe` (1.5 MB) carry the game's own
  "Max Payne 2 startup dialog" (messages name it: resolution, anti-aliasing, "select a platform"). No separate launcher exe.
- Option words in the exe: `nodialog`, `skipstartup`. Idea: launch option `%command% -nodialog`. **Not tested.**
- Direct3D 9 (`D3D9.DLL`), so the dialog also has anti-aliasing and a platform choice.

## Where the dialog keeps its choices
Expected: the same `Software\\Remedy Entertainment\\Max Payne 2\\...` sections in `compatdata/12150/pfx/user.reg`, but
**`user.reg` has no Remedy section yet** (the game was never opened here), so the key names and value ranges are unknown.
Needs one run of the dialog by the player (open the game, change one option, press Play), then a read-only diff.

## What the game saved (real `user.reg`, 2026-11-25 09:08)
After the player ran the dialog and started the game: `Video Settings` has `Display Width/Height` (dword; 640x480 on that run),
`Display Bits Per Pixel` (32), `CPU Driver`, `Driver`, `Gamma`, `LOD Bias`, `Mipmap Bias`, `Framerate Smoothness`,
`HW Acceleration Level`; `Other Settings` has `AutoAim Toggle`, `AutoWeaponSelect Toggle`, `BulletTimeAid Toggle`,
`Crosshair Index` (not a toggle), `EnableTips Toggle`, `Subtitles Toggle` (0/1 dwords). The first run (08:44) had left both
sections empty, which is why the profile waits for `Display Width` before offering anything.

## Next steps
Check in the plugin on the Deck: the panel lists the game, a resolution change lands in `user.reg`, the game honours it, and
Original puts the values back.
