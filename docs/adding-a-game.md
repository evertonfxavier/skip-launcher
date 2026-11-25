# Adding a game

Skip Launcher works game by game: every launcher starts the game and keeps its choices in its own way. This guide takes you from
"this game opens a window I cannot use with a controller" to a pull request. You do not need a Steam Deck for the first steps, but
step 3 and the final proof need one (yours or a friend's).

It also helps to read [safety-rules.md](safety-rules.md) and [architecture.md](architecture.md) first.

## Before you start

- **Is it a fit?** The game must be single-player or co-op (no anti-cheat, no online ranked play), run through Proton, and open a
  window before the game that you can skip without replacing any game file.
- **Is someone on it?** Search the [issues](https://github.com/evertonfxavier/skip-launcher/issues); [request the game](https://github.com/evertonfxavier/skip-launcher/issues/new?template=game_request.yml) if there is none, and say you will work on it.
- You need the game installed, **opened at least once through its own window** (so it has saved its settings), and a way to copy files off the Deck (`scp`; see [development.md](development.md#working-with-a-real-deck)).

## The two kinds of launcher

| You see | It is | The skip |
|---------|-------|----------|
| Steam starts `Launcher.exe`; the game is a different `.exe` that the launcher starts | a **separate launcher** | the *executable swap* launch option (Batman: Arkham Asylum) |
| Steam starts `Game.exe` and the window is the game's own start-up dialog | a **dialog inside the game** | a command-line switch the game understands, such as `-nodialog` (Max Payne) |

The settings of the window live in an `.ini` file or in the Windows registry (which under Proton is the text file `user.reg`). Both are supported.
Anything else (an XML or binary file) needs a new adapter: see [architecture.md](architecture.md#adding-things).

## Step by step

### 1. Find the game on your Deck

The Steam app id is the number in the store URL. The install folder is in
`~/.local/share/Steam/steamapps/common/` (or another library), and the Wine prefix with the game's settings is
`steamapps/compatdata/<appid>/pfx/`.

### 2. Look around (read-only)

- Which programs are in the install folder? Copy the small ones to your computer and read their strings (ASCII and UTF-16): a launcher
  usually names the game program, an ini file and the command line it uses; a game that has a start-up dialog often lists switches
  such as `nodialog` or `skipstartup`.
- Is there a config next to the launcher (`Launcher.ini`) that says how the game is started and with which arguments?
- Never edit anything in the game folder while looking, and do it on copies.

### 3. Prove the skip by hand

Before writing code, make sure the idea works. In Steam, game, Properties, General, **Launch options**, type:

- executable swap: `bash -c 'exec "${@/Launcher.exe/Game.exe}"' _ %command%` (with the real names);
- command-line switch: `%command% -nodialog` (with the real switch).

Start the game with a controller only. Does it open straight into the game? Do the controls work? Write down what you saw. Only a player can
confirm this step, and it is the evidence a reviewer wants first.

### 4. Find where the window keeps its choices

Open the game's window, change **one** option, press *Play*, quit, and compare the files in the prefix (modified time, then contents)
before and after. The difference is the profile. Note:

- the file and its **encoding** (a BOM at the start of the file means UTF-16);
- for the registry: the key path in `pfx/user.reg` (backslashes are doubled in that file) and the value format (`dword:00000780`);
- the keys and the values you saw for each option. **Only offer values you have seen** in the real file or in the launcher's own
  presets ([safety rule 11](safety-rules.md)).

### 5. Create the starting files

```bash
python3 tools/scaffold_game.py --appid 12345 --name "Some Game" --launcher Launcher.exe --game Game.exe
python3 tools/scaffold_game.py --appid 12345 --name "Some Game" --skip-args=-nodialog --format reg --config-rel user.reg --required-section 'Software\\Vendor\\Some Game\\Video Settings'
```

It writes `py_modules/skip_launcher/profiles/<slug>.py` and `docs/games/<appid>-<slug>.md`, and nothing else; it never overwrites. Then:

1. **Fill in the profile.** Settings are `toggle`s and `choice`s made of options; one option writes one or more `(section, key, value)` entries. Look at
   `profiles/batman_aa.py` (ini) and `profiles/max_payne.py` (registry) for the pattern.
2. **Register it** in `profiles/__init__.py`.
3. **Add the strings** to `src/i18n/en.json` and `src/i18n/pt-BR.json`: `setting.<id>`, `option.<setting>.<option>` (not for numeric ids such as `1280x720`), `group.<group>` and any `note_key`.
4. **Write the page** `docs/games/<appid>-<slug>.md`. Its *At a glance* table needs a `Summary` row and a `Support level` row (`confirmed`, `partly confirmed` or `unconfirmed`); list what you could not verify as `- NOT verified:` lines. Add the game to the table in [docs/games/README.md](games/README.md).
5. **Regenerate the list:** `python3 tools/gen_supported_games.py`. The tests fail until you do.

### 6. Write the tests

Tests never need game files: build a small synthetic fixture with the **real layout** (`tests/fixtures.py` has a Batman `UserEngine.ini` and a Max Payne `user.reg`).
At the very least:

- the current option is read correctly, and a value that matches no option reads as *custom*;
- a change touches only its lines (compare the file line by line before and after);
- **restore gives back the very same bytes**, including a key that did not exist;
- a missing, unreadable or not-yet-saved settings file is reported and **nothing is created**;
- nothing is written while the game runs (`fixtures.fake_process`) or, for registry games, while its prefix is alive (`fixtures.fake_environ`).

`tests/test_consistency.py` then checks that every setting and option has its translations and that the profile's facts make sense.

### 7. Try it on the Deck

```bash
pnpm run build:zip        # out/skip-launcher-vX.Y.Z.zip
```

Install it with Decky's Developer mode (**Install Plugin from ZIP**), open the panel and check that the game is listed with the values you expect. Change one
setting, start the game, look; then press *Put the original settings back* and check the file is as it was. [development.md](development.md) shows how to look before you install.

### 8. Verify on the real game

Collect the evidence for the pull request:

- the launch option you tested, and what the game did;
- the settings file lines before and after a change, and after restoring (the same bytes);
- the output of the tests;
- a screenshot of the panel or the game, if you have one.

### 9. Open the pull request

Fill in the template. Honest wording matters more than a green label: a game that starts without its window but whose settings you could
not test is **partly confirmed**, and that is a fine answer.

## Lessons from the first games

- A "launcher" is sometimes just a dialog inside the game: look for command-line switches in the program's strings before looking for an executable to swap.
- The registry under Proton is a text file, but Wine keeps it in memory while any process of the prefix lives and writes it on exit: never edit it then.
- A game that has never been opened has no settings file, or a registry section with no values: the plugin waits instead of inventing them.
- A launcher's own presets (its `Launcher.ini`, its detail levels) are the best source of values: they are what the window would have written.
- Keys that look like toggles may not be (Max Payne 2's `Crosshair Index`): offer only what you understand.

## If it turns out not to be feasible

That is a useful result too. Write down in the game's page what you found (what Steam starts, where the settings live, why the skip does not work) and open or update the
issue. The next person will not have to repeat it.

## Getting help

Open an [issue](https://github.com/evertonfxavier/skip-launcher/issues/new/choose) with what you tried and what you saw. Half-formed notes are welcome.
