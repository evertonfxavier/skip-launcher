# Changelog

## [Unreleased]

## [0.2.1] - 2026-11-25
- Fix: choosing another game in the select snapped back to the first one. The choice is now kept outside the panel, so it survives
  Steam re-rendering (remounting) the panel.

## [0.2.0] - 2026-11-25
- Max Payne 2 (12150): skips the startup dialog the same way and offers the resolution, auto-aim, auto weapon select, bullet time
  aid, tips and subtitles (key names read from the real registry); nothing is offered until the game has saved its own values.
- Max Payne (12140): skips the startup dialog with the launch option `%command% -nodialog` and edits the resolution and the
  gameplay options in the Wine registry (`user.reg`). New: registry editing (`regutil.py`), argument-only launch options, and a
  guard that refuses to write while any process of the game's Proton prefix is alive.

## [0.1.0] - 2026-11-24
- First version: Batman: Arkham Asylum GOTY Edition. Skip the launcher window from the plugin and change its settings
  (resolution, fullscreen, V-Sync, anti-aliasing, detail, effects, ambient occlusion, motion blur, PhysX, subtitles).
