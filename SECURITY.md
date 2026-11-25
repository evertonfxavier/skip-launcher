# Security policy

Skip Launcher changes a game's **launch option** in Steam and, for some games, writes the settings file or Wine registry file of that
game's Proton prefix. So "security" here covers two things: classic vulnerabilities, and **anything that could damage a user's games,
settings or saves**. We want to hear about both.

## What to report privately

- A way the plugin could write outside the files it is meant to change (path traversal, symlink tricks, a wrong prefix).
- A way it could damage a game's settings that the safety checks should have refused, or leave a settings file that
  **Put the original settings back** cannot restore exactly.
- A launch option the plugin builds that could run something other than the game (command injection through a game name,
  an existing launch option or a path).
- Code that runs untrusted input, or leaks anything about the user's machine.
- A problem in the release or CI pipeline (for example a way to publish a modified zip).

Ordinary bugs (a label that is wrong, a switch that does not update) are not security issues: please use a normal
[bug report](https://github.com/evertonfxavier/skip-launcher/issues/new?template=bug_report.yml).

## How to report

Use GitHub's private reporting: the repository's **Security** tab, then **Report a vulnerability**. Please do not open a public issue or
post details until we have had a chance to fix it.

Include: what you found, how to reproduce it (the game, the setting, the steps), the plugin version, and what you think the impact is.
You do not need a working exploit.

## What to expect

This is a volunteer project, so these are goals, not guarantees:

- an acknowledgement within **7 days**;
- an assessment and a plan within **14 days**;
- a fix released as soon as it is safe, with credit in the changelog if you want it.

## Supported versions

Only the **latest release** receives fixes.

## Good to know

- The plugin has **no network code** and needs no credentials; it only reads and writes files of games you chose, and the launch option of those games.
- It never modifies a game's own files (its executables and data), so a Steam update or *Verify integrity of game files* cannot be damaged by it.
- Releases are built by GitHub Actions from the `main` branch, and every zip has a `.sha256` file next to it so you can check your download.
- If you ever see a plugin zip that did not come from this repository's releases, do not install it.
