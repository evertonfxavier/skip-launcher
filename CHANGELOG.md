# Changelog

All notable changes to this project are documented here, in the [Keep a Changelog](https://keepachangelog.com) style.

## [Unreleased]

## [0.2.1] - 2026-11-25
- First public release, as its own repository: README (English and Brazilian Portuguese), contributing guide, code of conduct, security
  policy, issue forms, a pull-request template, documentation (FAQ, architecture, safety rules, how to add a game), a scaffold tool for
  new games, the logo, and a release pipeline that tests, builds and publishes the zip on every push to `main`.
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

[Unreleased]: https://github.com/evertonfxavier/skip-launcher/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/evertonfxavier/skip-launcher/releases/tag/v0.2.1
