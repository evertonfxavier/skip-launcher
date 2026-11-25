"""Stable codes next to every English status message, so the UI can translate without parsing text.

Add a code here, in engine.py, and as `code.<code>` in every catalog (tests/test_status_codes.py ties them together).
"""
CODES = (
    "ok",                  # the file is readable and every setting could be read
    "not_installed",       # the game is not installed in any Steam library
    "not_ready",           # installing, updating or validating
    "running",             # the game is open: nothing is changed meanwhile
    "no_config",           # the launcher never ran, so the game's ini file does not exist yet
    "unreadable",          # the ini file cannot be read or decoded
    "write_failed",        # the ini file could not be written
    "unknown_setting",     # a setting or option id the profile does not have
    "unknown_game",        # an appid with no profile
)
