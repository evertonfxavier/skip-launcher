"""Steam launch options that make Steam start a game without its launcher window.

Two kinds: the exe-rewrite wrapper below (the launcher is a separate exe), and a plain command-line word (`-nodialog`
for games whose window is a dialog inside the game exe; see `enable_args`).

Steam builds the whole command (`... proton waitforexitandrun .../BmLauncher.exe`) and puts it where `%command%` is.
The wrapper below hands that command to `bash`, which rewrites the one argument that names the launcher and then
runs it. No game file is touched, so a Steam update or "verify files" cannot undo it, and turning it off is just
removing the text. Any other launch option the player already has is kept around it.
"""
import re

COMMAND = "%command%"


def wrapper(launcher_exe, game_exe):
    """The exact text; it is also what the first manual test on the Deck used."""
    return "bash -c 'exec \"${@/%s/%s}\"' _ %s" % (launcher_exe, game_exe, COMMAND)


def is_enabled(options, launcher_exe, game_exe):
    return wrapper(launcher_exe, game_exe) in (options or "")


def enable(options, launcher_exe, game_exe):
    """`options` with the wrapper in place of `%command%` (or in front, when there is no `%command%`)."""
    options = options or ""
    wrap = wrapper(launcher_exe, game_exe)
    if wrap in options:
        return options
    if COMMAND in options:
        return options.replace(COMMAND, wrap, 1)
    options = options.strip()
    return wrap + (" " + options if options else "")


def disable(options, launcher_exe, game_exe):
    """The inverse of `enable`: what the player had before is what they get back."""
    options = options or ""
    wrap = wrapper(launcher_exe, game_exe)
    if wrap not in options:
        return options
    out = options.replace(wrap, COMMAND, 1)
    if out.strip() == COMMAND:
        return ""
    if out.startswith(COMMAND + " ") and out.count(COMMAND) == 1:
        return out[len(COMMAND) + 1:]            # Steam appends the options after the command anyway
    return out


# -- games whose window is a dialog of the game exe itself: one command-line word ------------------------------------------
def _word(args):
    return re.compile(r"(?<!\S)%s(?!\S)" % re.escape(args))


def args_enabled(options, args):
    return bool(_word(args).search(options or ""))


def enable_args(options, args):
    """Add `args` right after `%command%` (or at the end, when there is no `%command%`: Steam appends it anyway)."""
    options = options or ""
    if args_enabled(options, args):
        return options
    if COMMAND in options:
        return options.replace(COMMAND, COMMAND + " " + args, 1)
    options = options.strip()
    return (options + " " + args) if options else COMMAND + " " + args


def disable_args(options, args):
    """The inverse of `enable_args`: only our word goes, one adjacent space with it."""
    options = options or ""
    m = _word(args).search(options)
    if m is None:
        return options
    before, after = options[:m.start()], options[m.end():]
    if before.endswith(" "):
        before = before[:-1]
    elif after.startswith(" "):
        after = after[1:]
    out = before + after
    return "" if out.strip() == COMMAND else out


# -- one entry point for a profile -----------------------------------------------------------------------------------
def profile_enabled(options, profile):
    if profile.skip_args:
        return args_enabled(options, profile.skip_args)
    return is_enabled(options, profile.launcher_exe, profile.game_exe)


def profile_enable(options, profile):
    if profile.skip_args:
        return enable_args(options, profile.skip_args)
    return enable(options, profile.launcher_exe, profile.game_exe)


def profile_disable(options, profile):
    if profile.skip_args:
        return disable_args(options, profile.skip_args)
    return disable(options, profile.launcher_exe, profile.game_exe)
