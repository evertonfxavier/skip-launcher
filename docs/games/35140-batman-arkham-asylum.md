# Batman: Arkham Asylum GOTY Edition (appid 35140)

## At a glance
| | |
|--|--|
| Steam appid | 35140 |
| Launcher skipped | `Binaries/BmLauncher.exe` -> `Binaries/ShippingPC-BmGame.exe` |
| Settings file | `UserEngine.ini` (UTF-16 LE with BOM) in the Proton prefix |
| Profile | `profiles/batman_aa.py`, revision 1 |
| Status | skip proven by hand on the Deck (2026-11-25); plugin v0.1.0 installed and the panel, the skip toggle and the settings (resolution, anti-aliasing, subtitles read back from `UserEngine.ini`) confirmed working by the user |
| Summary | Starts Batman straight into the game, without the mouse-only launcher window, and lets you change the launcher's video, detail, PhysX and subtitle settings from the plugin with a controller. |
| Support level | confirmed |

- NOT verified: that the game itself shows every changed value (only resolution, anti-aliasing and subtitles were changed and read back from the file); the Original button was not tested in this round.
- NOT verified: a game that has never been opened (no `UserEngine.ini`): the plugin only says to open it once and never creates the file.

## How the game starts
- Steam launches `Binaries/BmLauncher.exe` (the only launch entry in `appinfo.vdf`). It is a .NET WinForms app:
  display settings, control (keyboard) bindings, readme, "Launch". It is mouse-only, which is the problem on a TV.
- The real game is `Binaries/ShippingPC-BmGame.exe`. `BmGame/Config/Launcher.ini` (`[Launcher.Settings]`) says the
  launcher starts it with `Game="ShippingPC-BmGame.exe"` and `GameCommandLine=""`: **no arguments**, so running the
  game exe directly is the same launch. `steam_appid.txt` sits next to it.
- `BmStartApp.exe` is not a Steam launch entry.

## Where the launcher keeps its choices
`<prefix>/drive_c/users/steamuser/Documents/Square Enix/Batman Arkham Asylum GOTY/BmGame/Config/`
(`UserConfigPath` in Launcher.ini). Files are **UTF-16 LE with BOM**, CRLF.
- `UserEngine.ini` `[SystemSettings]`: `Fullscreen UseVsync AllowD3D10 ResX ResY EffectsLevel MaxMultisamples`
  plus the detail keys `DynamicLights DepthOfField LensFlares Bloom DynamicShadows MotionBlur Distortion FogVolumes
  DisableSphericalHarmonicLights AmbientOcclusion DetailMode MaxShadowResolution Stereo IniVersion`.
- `UserEngine.ini` `[Engine.Engine]`: `PhysXLevel`, `bPhysXuseGRB`, `bPhysXPatched`, `Language`, `bSubtitlesEnabled`.
- `UserInput.ini` / `UserGame.ini`: keyboard bindings only (not needed for controller play).
- Presets live in `Launcher.ini`: `[SystemSettings_High|Medium|Low]` and `[DetailSettings_VeryHigh|High|Medium|Low]`.
  `IniVersion=5.8`: a different version makes the launcher re-create the user ini files.
- Deck sample (read only): 1920x1080, fullscreen, vsync, EffectsLevel 3, PhysXLevel 0.

## Plan for the plugin
- Skip: rewrite the `BmLauncher.exe` argument of Steam's command to `ShippingPC-BmGame.exe` from the launch option
  (no game file touched):
  `bash -c 'exec "${@/BmLauncher.exe/ShippingPC-BmGame.exe}"' _ %command%` (argument rewrite checked locally).
- Settings: edit the keys above in `UserEngine.ini` from the plugin UI, with a backup and an exact undo.
- If `UserEngine.ini` does not exist (game never opened): write the launcher's own defaults for the chosen preset.

## Open questions (answered on the Deck, 2026-11-25)
1. Does the game start and reach the menu with the rewritten command, with the controller only? **Yes** (tested by hand).
2. Does Steam's overlay/Steam Input still work (the process tree changes)?
3. Is a Proton `waitforexitandrun` run of the game exe stable (the game exe alone vs. launcher-spawned child)?
