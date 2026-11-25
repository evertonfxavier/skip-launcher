## What does this change?

<!-- One or two sentences. Link the issue if there is one: "Closes #12". -->

## Type

- [ ] Documentation or translation
- [ ] Bug fix
- [ ] New game or change to a game profile
- [ ] Engine, tools or UI
- [ ] Other:

## Checklist

- [ ] `python3 -W error::ResourceWarning -m unittest discover -s tests` passes
- [ ] `npx tsc --noEmit -p .` passes (if I touched `src/`)
- [ ] I regenerated generated files instead of editing them (`python3 tools/gen_supported_games.py`, `pnpm run brand`)
- [ ] I added a line under **Unreleased** in `CHANGELOG.md` (if a user would notice)
- [ ] No game files or copies of them are in this pull request
- [ ] I followed [docs/safety-rules.md](../docs/safety-rules.md)

## If this writes the game's settings or touches launch options (profile, engine)

- [ ] Tests prove **exact undo** (the settings file is byte-identical after a change and a restore)
- [ ] A missing or unreadable settings file is reported and **nothing is written or created**
- [ ] Nothing is written while the game or its Proton prefix is running
- [ ] The game's page in `docs/games/` says honestly what was verified and what was not

## Evidence

<!-- A screenshot, the launch option you tested, or the settings lines before and after. Optional for docs changes. -->
