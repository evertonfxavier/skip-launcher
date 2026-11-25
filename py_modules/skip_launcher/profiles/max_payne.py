"""Max Payne (appid 12140).

There is no separate launcher exe: the window that opens before the game is the game's own startup dialog
(`CMaxPayneStartupDialog` inside `maxpayne.exe`). The exe takes the command-line word `-nodialog`, which starts it
without the dialog and with the last saved settings (proven by hand on the Deck, 2026-11-25). Those settings are the
Wine registry of the prefix (`user.reg`), under `Software\\\\Remedy Entertainment\\\\Max Payne\\\\...` (backslashes doubled
in the file), written as `"Key"=dword:xxxxxxxx`. Facts and the manual test: docs/games/12140-max-payne.md.
"""
from .base import Option, Profile, Setting

VIDEO = r"Software\\Remedy Entertainment\\Max Payne\\Video Settings"
OTHER = r"Software\\Remedy Entertainment\\Max Payne\\Other Settings"

RESOLUTIONS = [(1024, 768), (1280, 720), (1280, 800), (1600, 900), (1920, 1080)]


def dword(n):
    return "dword:%08x" % n


def _res_option(w, h):
    return Option("%dx%d" % (w, h), "%d x %d" % (w, h),
                  [(VIDEO, "Display Width", dword(w)), (VIDEO, "Display Height", dword(h))])


def _toggle(setting_id, label, key):
    return Setting(setting_id, "toggle", label, [
        Option("on", "On", [(OTHER, key, dword(1))]),
        Option("off", "Off", [(OTHER, key, dword(0))]),
    ], group="game")


class MaxPayne(Profile):
    appid = "12140"
    name = "Max Payne"
    revision = 1
    support = "full"
    launcher_exe = "maxpayne.exe"                  # the startup dialog is part of the game exe itself
    game_exe = "maxpayne.exe"
    skip_args = "-nodialog"
    config_rel = "user.reg"
    config_format = "reg"
    required_section = VIDEO                       # exists once the dialog ran and was accepted

    settings = (
        Setting("resolution", "choice", "Resolution", [_res_option(w, h) for w, h in RESOLUTIONS]),
        _toggle("auto_aim", "Auto-aim", "AutoAim Toggle"),
        _toggle("auto_weapon", "Auto weapon select", "AutoWeaponSelect Toggle"),
        _toggle("bullet_time_aid", "Bullet time aid", "BulletTimeAid Toggle"),
        _toggle("crosshair", "Crosshair", "Crosshair Toggle"),
        _toggle("tips", "Tips", "EnableTips Toggle"),
    )


PROFILE = MaxPayne()
