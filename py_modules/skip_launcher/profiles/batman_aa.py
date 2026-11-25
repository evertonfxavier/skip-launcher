"""Batman: Arkham Asylum GOTY Edition (appid 35140).

Steam starts `Binaries/BmLauncher.exe`, a mouse-only WinForms window. `BmGame/Config/Launcher.ini` says that the
launcher starts the real game as `Game="ShippingPC-BmGame.exe"` with `GameCommandLine=""`, so running that exe directly
is the very same launch. The window's choices live in `UserEngine.ini` (UTF-16) in the Proton prefix:
`[SystemSettings]` for video and detail, `[Engine.Engine]` for PhysX. The detail levels and the effects levels below
are the launcher's own presets (`Launcher.ini`, `[DetailSettings_*]` / `[SystemSettings_*]`). Facts and the manual test:
docs/games/35140-batman-arkham-asylum.md.
"""
from .base import Option, Profile, Setting

SYS = "SystemSettings"
ENG = "Engine.Engine"

# Common 16:9 / 16:10 sizes for the Deck's 1280x800 screen and a TV (the game's own output is scaled by gamescope).
RESOLUTIONS = [(1280, 720), (1280, 800), (1600, 900), (1920, 1080), (1920, 1200), (2560, 1440)]


def _res_option(w, h):
    return Option("%dx%d" % (w, h), "%d x %d" % (w, h), [(SYS, "ResX", str(w)), (SYS, "ResY", str(h))])


def _toggle(setting_id, label, section, key, group="video"):
    return Setting(
        setting_id, "toggle", label,
        [Option("on", "On", [(section, key, "True")]), Option("off", "Off", [(section, key, "False")])],
        group=group,
    )


def _detail(option_id, label, values):
    return Option(option_id, label, [(SYS, k, v) for k, v in values])


DETAIL_KEYS = [
    "DynamicLights", "DepthOfField", "LensFlares", "Bloom", "DynamicShadows", "MotionBlur", "Distortion",
    "FogVolumes", "DisableSphericalHarmonicLights", "AmbientOcclusion", "DetailMode", "MaxShadowResolution",
]


def _detail_values(*values):
    return list(zip(DETAIL_KEYS, values))


DETAIL_LEVELS = [
    _detail("very_high", "Very high", _detail_values("True", "True", "True", "True", "True", "True", "True",
                                                      "True", "False", "True", "2", "512")),
    _detail("high", "High", _detail_values("True", "True", "True", "True", "True", "True", "True",
                                            "True", "False", "False", "1", "512")),
    _detail("medium", "Medium", _detail_values("True", "True", "True", "True", "True", "False", "False",
                                                "False", "True", "False", "1", "512")),
    _detail("low", "Low", _detail_values("True", "True", "True", "False", "False", "False", "False",
                                          "False", "True", "False", "0", "256")),
]


class BatmanArkhamAsylum(Profile):
    appid = "35140"
    name = "Batman: Arkham Asylum GOTY Edition"
    revision = 1
    support = "full"
    launcher_exe = "BmLauncher.exe"
    game_exe = "ShippingPC-BmGame.exe"
    config_rel = (
        "drive_c/users/steamuser/Documents/Square Enix/Batman Arkham Asylum GOTY/BmGame/Config/UserEngine.ini"
    )

    settings = (
        Setting("resolution", "choice", "Resolution", [_res_option(w, h) for w, h in RESOLUTIONS]),
        _toggle("fullscreen", "Fullscreen", SYS, "Fullscreen"),
        _toggle("vsync", "V-Sync", SYS, "UseVsync"),
        Setting("antialiasing", "choice", "Anti-aliasing", [
            Option("off", "Off", [(SYS, "MaxMultisamples", "1")]),
            Option("2x", "2x", [(SYS, "MaxMultisamples", "2")]),
            Option("4x", "4x", [(SYS, "MaxMultisamples", "4")]),
            Option("8x", "8x", [(SYS, "MaxMultisamples", "8")]),
        ]),
        Setting("detail", "choice", "Detail level", DETAIL_LEVELS, group="detail"),
        Setting("effects", "choice", "Effects", [
            Option("high", "High", [(SYS, "EffectsLevel", "3")]),
            Option("medium", "Medium", [(SYS, "EffectsLevel", "2")]),
            Option("low", "Low", [(SYS, "EffectsLevel", "0")]),
        ], group="detail"),
        _toggle("ambient_occlusion", "Ambient occlusion", SYS, "AmbientOcclusion", group="detail"),
        _toggle("motion_blur", "Motion blur", SYS, "MotionBlur", group="detail"),
        Setting("physx", "choice", "PhysX", [
            Option("off", "Off", [(ENG, "PhysXLevel", "0")]),
            Option("normal", "Normal", [(ENG, "PhysXLevel", "1")]),
            Option("high", "High (NVIDIA only)", [(ENG, "PhysXLevel", "2")]),
        ], group="detail", note_key="note.physx"),
        _toggle("subtitles", "Subtitles", ENG, "bSubtitlesEnabled", group="game"),
    )


PROFILE = BatmanArkhamAsylum()
