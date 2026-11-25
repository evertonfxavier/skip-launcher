# FAQ and troubleshooting

Short answers first; the longer ones are below. If your question is not here, [open an issue](https://github.com/evertonfxavier/skip-launcher/issues/new/choose).

- [The basics](#the-basics)
- [Is it safe for my games?](#is-it-safe-for-my-games)
- [Using it](#using-it)
- [Something is not working](#something-is-not-working)
- [Removing the plugin](#removing-the-plugin)
- [Where things live](#where-things-live)

## The basics

### What does Skip Launcher do?

Some Windows games open a small **launcher window** before the game: a screen for resolution, quality or controls, with a *Play* button
that only works with a mouse. On a Steam Deck docked to a TV, with only a controller, that window is a dead end. Skip Launcher
makes Steam start the game itself, and moves what that window used to hold (resolution, detail, subtitles…) into the plugin, where a
controller can reach it.

### How does it skip the window?

By changing the game's **launch option** in Steam. For a game with a separate launcher program (Batman: Arkham Asylum), the option
makes Steam start the real game program instead of the launcher. For a game whose window is a dialog inside the game itself (Max
Payne), the option adds the switch the game already understands (`-nodialog`). No game file is touched.

### Does it need the internet? Does it send anything anywhere?

No. The plugin has no network code. It reads and writes only the files of the games you choose.

### Why only some games?

Every launcher keeps its choices somewhere different (an ini file, the Windows registry) and starts the game in its own way, so each game
needs its own *profile*. See [SUPPORTED_GAMES.md](../SUPPORTED_GAMES.md). Yours is missing?
[Request it](https://github.com/evertonfxavier/skip-launcher/issues/new?template=game_request.yml) or [add it yourself](adding-a-game.md).

### What does "unconfirmed" mean next to a game?

Nobody has reported yet that it works on a Deck. The plugin refuses to guess, so the worst case is that it does nothing, but the honest
label helps you decide. [Tell us how it went](https://github.com/evertonfxavier/skip-launcher/issues/new?template=deck_report.yml).

## Is it safe for my games?

It was built so that you can always go back.

- **It never modifies a game's own files** (executables, data). The skip is only a launch option in Steam, so a game update or
  *Verify integrity of game files* cannot be damaged by it.
- **Before the first change to a setting**, the plugin records the value that setting had (and keeps a copy of the whole settings file). **Put the
  original settings back** restores exactly those values, key by key, even if the game rewrote the rest of the file in between.
- **It writes nothing while the game is open**, installing or updating, nor while Wine's session of that game is still alive.
- **It never creates or guesses a settings file.** If the game has not saved its settings yet, the plugin says so and waits.
- **Your other launch options are kept.** Turning the switch off removes only the text the plugin added.

The full list is in [safety-rules.md](safety-rules.md).

## Using it

### How do I go back to the original?

- For the **launcher window**: turn off *Skip the launcher window*. Only the text the plugin added is removed from the launch option.
- For the **settings**: press *Put the original settings back* (it appears once you changed something).
- By hand: in Steam, game, Properties, General, clear the launch option.

### The game got an update. What happens?

The launch option lives in Steam, not in the game's files, so it stays. The settings live in the game's Proton prefix, which updates do not touch.

### I used "Verify integrity of game files". What happens?

Nothing is lost: the plugin does not change the game's files, so there is nothing to verify away.

### Can I use it while the game is open?

You can open the panel, but changes are refused until you close the game (and, for Wine games, until its session ends, a few seconds after quitting).

### Does it work in Desktop Mode?

It is a Game Mode plugin (Decky). In Desktop Mode, set the launch option by hand as described above.

### Why is a setting greyed out or does it say "Custom"?

The value in the game's file is not one of the choices the plugin offers (for example you set an unusual resolution by hand). The
plugin never overwrites what it does not recognise: pick a value to replace it, or leave it.

### Which resolution should I choose?

The Deck's own screen is 1280x800; on a TV, pick the TV's resolution. The game's output is scaled by the system, so a lower value is
fine and easier on the battery.

## Something is not working

### Skip Launcher does not appear in the Decky list after installing

Reload Decky (Quick Access, Decky, Settings, *Reload*) or restart the Deck. Check that you installed the `.zip` from a [release](https://github.com/evertonfxavier/skip-launcher/releases/latest) and that Developer Mode is on.

### My game is not in the dropdown

It is not supported yet: see [SUPPORTED_GAMES.md](../SUPPORTED_GAMES.md) and [request it](https://github.com/evertonfxavier/skip-launcher/issues/new?template=game_request.yml).

### I cannot switch between games in the dropdown

This was a bug in version 0.2.0 (the choice snapped back to the first game) fixed in 0.2.1. Update the plugin.

### The game says "has not saved its settings yet"

The plugin only edits a settings file that already exists. Turn off *Skip the launcher window*, start the game once, press the window's *Play* or *Launch* button so it saves its settings, close the game, and come back.

### The launcher window still opens

Check the game's launch option (Steam, game, Properties, General). It must contain the text the plugin shows under *Skip the launcher window*. If another tool (or you) replaced it, turn the switch off and on again.

### The game starts but ignores my setting

Some games rewrite their settings when they start or quit. [Open a bug report](https://github.com/evertonfxavier/skip-launcher/issues/new?template=bug_report.yml) with the game, the setting and the log.

### How do I get the log for a bug report?

In Desktop Mode, open Konsole and run:

```bash
tail -n 80 "$(ls -t ~/homebrew/logs/Skip\ Launcher/*.log | head -1)"
```

It contains no personal data.

## Removing the plugin

1. For every game, turn off *Skip the launcher window* and, if you changed settings, press *Put the original settings back*.
2. Remove the plugin from Decky (Settings, Plugins).

If you forget step 1, a game just keeps the launch option the plugin set: clear it in Steam (game, Properties, General), and the launcher window comes back.

## Where things live

| What | Where |
|------|-------|
| The plugin | `~/homebrew/plugins/Skip Launcher/` |
| Recorded original values and the latest events | `~/homebrew/settings/Skip Launcher/config.json` |
| Copy of each game's settings file from before the first change | `~/homebrew/settings/Skip Launcher/backups/<appid>/` |
| Logs | `~/homebrew/logs/Skip Launcher/` and `journalctl -u plugin_loader` |
| A game's settings | inside its Proton prefix: `steamapps/compatdata/<appid>/pfx/` |
