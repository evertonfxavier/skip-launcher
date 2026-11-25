"""Max Payne 2: The Fall of Max Payne (appid 12150).

Same engine family and the same startup dialog as Max Payne (docs/games/12140-max-payne.md): no separate launcher exe, the
command-line word `-nodialog` skips the dialog (proven by hand on the Deck, 2026-11-25). The settings are the Wine registry
of the prefix, `Software\\\\Remedy Entertainment\\\\Max Payne 2\\\\...`, written as `"Key"=dword:xxxxxxxx`. The key names below
were read from the real `user.reg` of the Deck after the game ran (2026-11-25): `Video Settings` (Display Width / Height,
640x480 at 32 bits on that run) and `Other Settings` (AutoAim, AutoWeaponSelect, BulletTimeAid, EnableTips, Subtitles as
0/1 toggles). `Crosshair Index` is not a toggle and its values are unknown, so it is not offered. Nothing is offered until the
game itself saved a `Display Width` (`required_key`).
"""
from .base import Option, Profile, Setting
from .max_payne import RESOLUTIONS, dword

VIDEO = r"Software\\Remedy Entertainment\\Max Payne 2\\Video Settings"
OTHER = r"Software\\Remedy Entertainment\\Max Payne 2\\Other Settings"

SIZES = [(640, 480), (800, 600)] + [r for r in RESOLUTIONS if r not in ((640, 480), (800, 600))]


def _res_option(w, h):
    return Option("%dx%d" % (w, h), "%d x %d" % (w, h),
                  [(VIDEO, "Display Width", dword(w)), (VIDEO, "Display Height", dword(h))])


def _toggle(setting_id, label, key):
    return Setting(setting_id, "toggle", label, [
        Option("on", "On", [(OTHER, key, dword(1))]),
        Option("off", "Off", [(OTHER, key, dword(0))]),
    ], group="game")


class MaxPayne2(Profile):
    appid = "12150"
    name = "Max Payne 2: The Fall of Max Payne"
    revision = 2
    support = "full"
    launcher_exe = "maxpayne2.exe"
    game_exe = "maxpayne2.exe"
    skip_args = "-nodialog"
    config_rel = "user.reg"
    config_format = "reg"
    required_section = VIDEO
    required_key = (VIDEO, "Display Width")

    settings = (
        Setting("resolution", "choice", "Resolution", [_res_option(w, h) for w, h in SIZES]),
        _toggle("auto_aim", "Auto-aim", "AutoAim Toggle"),
        _toggle("auto_weapon", "Auto weapon select", "AutoWeaponSelect Toggle"),
        _toggle("bullet_time_aid", "Bullet time aid", "BulletTimeAid Toggle"),
        _toggle("tips", "Tips", "EnableTips Toggle"),
        _toggle("subtitles", "Subtitles", "Subtitles Toggle"),
    )


PROFILE = MaxPayne2()
