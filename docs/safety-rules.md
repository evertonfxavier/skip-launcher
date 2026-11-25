# Safety rules

Skip Launcher changes a game's launch option in Steam and, for most games, writes the settings file (or the Wine registry file) of
that game's Proton prefix, on a device that can lose power at any moment. These rules are what makes that acceptable. **A pull
request that breaks one will not be merged**, however nice the feature. Each rule says *why*, so you can judge new situations the
rules did not foresee.

| # | Rule | Why |
|---|------|-----|
| 1 | **Never modify a game's own files for the skip.** Skipping is a launch option only; a game that needs a file replaced is out of scope. | Steam updates and *Verify integrity* must not be able to undo, or be confused by, what we did. |
| 2 | **Analyse on copies.** Copy the launcher, its ini or the registry file to your computer; the plugin engine is the only thing that writes on the Deck. | A mistaken experiment must never hit the only copy. |
| 3 | **Never write while the game runs, installs or updates**, nor while any process of its Proton prefix is alive. | Writing into files in use corrupts them; Wine keeps the registry in memory and would overwrite our edit on exit. |
| 4 | **Never create or guess a missing settings file.** If it does not exist, or cannot be decoded, say so and write nothing. | A file we invented may be read by the game in a way nobody tested. |
| 5 | **The way back is on disk before the first write:** a whole-file copy and the value every key had before our first change (`null` when the key did not exist). | A crash or power cut after the first write must still leave a way back. |
| 6 | **Undo must be exact, key by key.** *Put the original settings back* restores each recorded value (and removes keys that did not exist), and a test proves the file is byte-identical. | A "restore" that leaves the file slightly different is a bug nobody can see. |
| 7 | **Atomic writes:** temp file, `fsync`, `os.replace`; on failure leave the old file and no temp. | A power cut must leave the old file or the new one, never half of one. |
| 8 | **Change only the lines you were asked to change.** Keep the encoding, the BOM, the line endings, the comments and every untouched line byte for byte. | Games and launchers are picky; a re-encoded file may stop loading. |
| 9 | **Do not guess a value.** The current option is the one whose every entry matches the file; otherwise the UI says *custom* and leaves it alone. | Showing a wrong value as if it were right is worse than showing none. |
| 10 | **Keep other launch options.** Turning the skip on adds only our text; turning it off removes only our text. | The player's own options (`gamemoderun`, `-windowed`, …) are theirs. |
| 11 | **Offer only values you have seen.** A setting appears in a profile only if its key and value format were read from the real file or the launcher's own presets. | An invented scale (gamma, quality) can produce a game that looks broken. |
| 12 | **Show errors, and show them before "pending".** | A failing write that reads as "will be applied" hides the problem forever. |
| 13 | **Standard library only in the backend; bounded memory.** | The Deck has no pip, and limited memory and time. |
| 14 | **Bump the profile `revision`** when its entries change meaning. | A change in what an option writes must be visible. |
| 15 | **No game files, no secrets in the repository, commands or docs.** | Licensing, and they end up in logs and history. |

## How to apply them when you write code

For every place that writes, ask three questions:

1. **What was checked before this write?** If the answer is "nothing", it is a bug.
2. **If the power dies right after this call, what is on disk, and how does the next run recover?** Write a test that simulates exactly that.
3. **Could this read a file we already changed as if it were the original?** The recorded originals come from the first change only; later changes never overwrite them.

`tests/test_engine.py` and `tests/test_max_payne.py` show the pattern: each kind of settings file has tests for exact undo, refusal and the running-game guard. A new kind of file (a new adapter next to `iniutil.py` and `regutil.py`) needs the same, plus an entry in [architecture.md](architecture.md).
