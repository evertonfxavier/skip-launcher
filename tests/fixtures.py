"""Synthetic fixtures: a fake Steam library with a Batman install and a Proton prefix holding a UserEngine.ini."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "py_modules"))

from skip_launcher.profiles import PROFILES  # noqa: E402

APPID = "35140"

USER_ENGINE = (
    "[Configuration]\r\n"
    "BasedOn=..\\BmGame\\Config\\DefaultEngine.ini\r\n"
    "\r\n"
    "[SystemSettings]\r\n"
    "Fullscreen=True\r\n"
    "UseVsync=True\r\n"
    "AllowD3D10=False\r\n"
    "ResX=1920\r\n"
    "ResY=1080\r\n"
    "EffectsLevel=3\r\n"
    "MaxMultisamples=1\r\n"
    "DynamicLights=True\r\n"
    "DepthOfField=True\r\n"
    "LensFlares=True\r\n"
    "Bloom=True\r\n"
    "DynamicShadows=True\r\n"
    "MotionBlur=True\r\n"
    "Distortion=True\r\n"
    "FogVolumes=True\r\n"
    "DisableSphericalHarmonicLights=False\r\n"
    "AmbientOcclusion=True\r\n"
    "DetailMode=2\r\n"
    "MaxShadowResolution=512\r\n"
    "Stereo=False\r\n"
    "IniVersion=5.8\r\n"
    "\r\n"
    "[Engine.Engine]\r\n"
    "bOnScreenKismetWarnings=FALSE\r\n"
    "bSubtitlesEnabled=FALSE\r\n"
    "PhysXLevel=0\r\n"
    "bPhysXuseGRB=False\r\n"
    "bPhysXPatched=True\r\n"
    "Language=int\r\n"
    "\r\n"
    "[DevOptions.Shaders]\r\n"
    "bAllowMultiThreadedShaderCompile=True\r\n"
)


def utf16(text):
    return b"\xff\xfe" + text.encode("utf-16-le")


class Library(object):
    """A temp 'home' with a Steam library; `install()` adds the game, `write_ini()` the launcher's file."""

    def __init__(self, test, appid=APPID, installdir="Batman Arkham Asylum GOTY"):
        self.appid, self.installdir = appid, installdir
        self.tmp = tempfile.TemporaryDirectory()
        test.addCleanup(self.tmp.cleanup)
        self.home = os.path.join(self.tmp.name, "home")
        self.settings = os.path.join(self.tmp.name, "settings")
        self.proc = os.path.join(self.tmp.name, "proc")
        os.makedirs(self.proc)
        self.root = os.path.join(self.home, ".local", "share", "Steam")
        self.steamapps = os.path.join(self.root, "steamapps")
        os.makedirs(self.steamapps)
        self.profile = PROFILES[appid]

    def install(self, state_flags=4):
        with open(os.path.join(self.steamapps, "appmanifest_%s.acf" % self.appid), "w") as f:
            f.write('"AppState"\n{\n\t"appid"\t"%s"\n\t"name"\t"%s"\n\t"StateFlags"\t"%d"\n'
                    '\t"installdir"\t"%s"\n}\n' % (self.appid, self.profile.name, state_flags, self.installdir))
        os.makedirs(os.path.join(self.steamapps, "common", self.installdir, "Binaries"), exist_ok=True)

    @property
    def install_path(self):
        return os.path.join(self.steamapps, "common", self.installdir)

    @property
    def prefix(self):
        return os.path.join(self.steamapps, "compatdata", self.appid, "pfx")

    @property
    def ini_path(self):
        return os.path.join(self.prefix, self.profile.config_rel)

    def write_ini(self, raw=None):
        os.makedirs(os.path.dirname(self.ini_path), exist_ok=True)
        with open(self.ini_path, "wb") as f:
            f.write(utf16(USER_ENGINE) if raw is None else raw)

    def read_ini(self):
        with open(self.ini_path, "rb") as f:
            return f.read()

    def fake_process(self, cmdline, pid="4242"):
        d = os.path.join(self.proc, pid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "cmdline"), "wb") as f:
            f.write(cmdline.replace(" ", "\0").encode())

    def fake_environ(self, env, pid="4343"):
        """A process whose environment is `env` (a dict), as Proton starts every process of a prefix."""
        d = os.path.join(self.proc, pid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "environ"), "wb") as f:
            f.write(b"\0".join(("%s=%s" % kv).encode() for kv in env.items()) + b"\0")


MP_APPID = "12140"

USER_REG = (
    "WINE REGISTRY Version 2\n"
    ";; All keys relative to \\\\User\\\\S-1-5-21-0-0-0-1000\n"
    "\n"
    "#arch=win32\n"
    "\n"
    "[Control Panel\\\\Desktop] 1795560000\n"
    "#time=1dd7c60000000000\n"
    '"FontSmoothing"="2"\n'
    "\n"
    "[Software\\\\Remedy Entertainment\\\\Max Payne\\\\Audio Settings] 1795560333\n"
    "#time=1dd7c6583a4a292\n"
    '"Effects Volume"=dword:00002710\n'
    "\n"
    "[Software\\\\Remedy Entertainment\\\\Max Payne\\\\Input Settings] 1795560333\n"
    "#time=1dd7c6583a49fa4\n"
    '" 0 Button0 type"=dword:00000001\n'
    "\n"
    "[Software\\\\Remedy Entertainment\\\\Max Payne\\\\Other Settings] 1795560333\n"
    "#time=1dd7c6583a4b462\n"
    '"AutoAim Toggle"=dword:00000001\n'
    '"AutoWeaponSelect Toggle"=dword:00000001\n'
    '"BulletTimeAid Toggle"=dword:00000001\n'
    '"Crosshair Toggle"=dword:00000001\n'
    '"EnableTips Toggle"=dword:00000001\n'
    '"Other Settings Version"=dword:00000002\n'
    "\n"
    "[Software\\\\Remedy Entertainment\\\\Max Payne\\\\Video Settings] 1795560333\n"
    "#time=1dd7c6583a4a9ea\n"
    '"CPU Driver"=dword:00000001\n'
    '"Display Bits Per Pixel"=dword:00000010\n'
    '"Display Height"=dword:00000438\n'
    '"Display Width"=dword:00000780\n'
    '"Driver"="ATI Radeon HD 5600 Series"\n'
    '"Video Settings Version"=dword:00000001\n'
    "\n"
    "[Software\\\\Valve\\\\Steam] 1795560400\n"
    "#time=1dd7c6600000000\n"
    '"SteamPath"="C:\\\\Program Files (x86)\\\\Steam"\n'
)
