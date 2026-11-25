"""Reads and changes the settings a game's launcher window used to hold.

Safety, in the same spirit as the Button Glyphs engine:
  * nothing is written while the game is running, installing or updating;
  * the ini file is edited in place (only the lines of the chosen option), through a temp file, fsync and an atomic
    replace, so a power cut leaves either the old or the new file, never half of one;
  * before the first change the whole file is copied aside, and the value every key had BEFORE our first change is
    recorded (persisted before the write). `restore` puts those values back key by key, so it is exact even when the
    game or the launcher rewrote the rest of the file meanwhile;
  * a file that is missing or cannot be decoded is never created or guessed: the status says what to do.
"""
import hashlib
import json
import os
import time

from . import steam
from .iniutil import IniError, IniText
from .regutil import RegError, RegText
from .profiles import PROFILES
from .profiles.base import SECTION_SEP

TMP_SUFFIX = ".skip-launcher.tmp"


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _fsync_dir(path):
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _write_atomic(path, data):
    tmp = path + TMP_SUFFIX
    try:
        mode = os.stat(path).st_mode & 0o7777
    except OSError:
        mode = 0o644
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    _fsync_dir(os.path.dirname(path))


class Engine(object):
    def __init__(self, home, settings_dir, logger=None, proc_root="/proc", clock=time.time):
        self.home = home
        self.settings_dir = settings_dir
        self.logger = logger
        self.proc_root = proc_root
        self.clock = clock
        self.config_path = os.path.join(settings_dir, "config.json")

    # -- bookkeeping -----------------------------------------------------------------------------------------------
    def _log(self, msg):
        if self.logger is not None:
            self.logger.info(msg)

    def _load(self):
        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return {"games": {}}
        if not isinstance(data, dict) or not isinstance(data.get("games"), dict):
            return {"games": {}}
        return data

    def _save(self, data):
        os.makedirs(self.settings_dir, exist_ok=True)
        _write_atomic(self.config_path, json.dumps(data, indent=2, sort_keys=True).encode("utf-8"))

    def _backup_path(self, appid):
        profile = PROFILES.get(str(appid))
        name = os.path.basename(profile.config_rel) if profile is not None else "settings"
        return os.path.join(self.settings_dir, "backups", str(appid), name + ".orig")

    # -- one game --------------------------------------------------------------------------------------------------
    def _context(self, appid):
        """(profile, app, status) where status is {state, code, message}; app is None when not installed."""
        profile = PROFILES.get(str(appid))
        if profile is None:
            return None, None, _status("error", "unknown_game", "no profile for appid %s" % appid)
        app = steam.find_app(self.home, profile.appid)
        if app is None:
            return profile, None, _status("error", "not_installed", "%s is not installed" % profile.name)
        if not steam.is_ready(app):
            return profile, app, _status("pending", "not_ready", "the game is installing or updating")
        if steam.is_running(app, steam.running_cmdlines(self.proc_root)):
            return profile, app, _status("running", "running", "the game is open: close it to change settings")
        if steam.prefix_in_use(app, self.proc_root):
            return profile, app, _status("running", "running", "the game's Wine session is still open: wait a moment")
        return profile, app, _status("ok", "ok", "ready")

    def _config_file(self, profile, app):
        return os.path.join(app["prefix"], profile.config_rel)

    def _read(self, profile, app):
        """(IniText, raw bytes) or (None, status) when the file cannot be used."""
        path = self._config_file(profile, app)
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except FileNotFoundError:
            return None, _no_config()
        except OSError as exc:
            return None, _status("error", "unreadable", "cannot read the settings file: %s" % exc)
        try:
            doc = RegText(raw) if profile.config_format == "reg" else IniText(raw)
        except (IniError, RegError) as exc:
            return None, _status("error", "unreadable", str(exc))
        if profile.required_section and not doc.has_section(profile.required_section):
            return None, _no_config()          # the game's window never ran here: its keys do not exist yet
        if profile.required_key and doc.get(*profile.required_key) is None:
            return None, _no_config()          # the section exists but the game never saved a value in it
        return doc, raw

    def list_games(self):
        out = []
        for profile in PROFILES.values():
            _, app, status = self._context(profile.appid)
            if app is not None and status["code"] in ("ok", "running"):
                ini, info = self._read(profile, app)
                if ini is None:
                    status = info
            out.append({
                "appid": profile.appid,
                "name": profile.name,
                "support": profile.support,
                "installed": app is not None,
                "launcher_exe": profile.launcher_exe,
                "game_exe": profile.game_exe,
                "status": status,
            })
        return out

    def get_game(self, appid):
        """Everything the UI shows for one game: status and, when readable, each setting's current option."""
        profile, app, status = self._context(appid)
        if profile is None:
            return {"appid": str(appid), "status": status, "settings": []}
        game = {
            "appid": profile.appid,
            "name": profile.name,
            "launcher_exe": profile.launcher_exe,
            "game_exe": profile.game_exe,
            "status": status,
            "settings": [],
            "changed": False,
        }
        if app is None:
            return game
        ini, info = self._read(profile, app)
        if ini is None:
            game["status"] = info if status["code"] in ("ok", "running") else status
            return game
        record = self._load()["games"].get(profile.appid, {})
        game["changed"] = bool(record.get("originals"))
        for setting in profile.settings:
            d = setting.to_dict()
            d["current"] = profile.current_option(setting, ini)
            game["settings"].append(d)
        return game

    def set_option(self, appid, setting_id, option_id):
        profile, app, status = self._context(appid)
        if profile is None:
            return _result(False, status)
        if status["code"] != "ok":
            return _result(False, status)
        setting = profile.setting(setting_id)
        option = setting.option(option_id) if setting is not None else None
        if option is None:
            return _result(False, _status("error", "unknown_setting", "unknown setting or option"))
        ini, info = self._read(profile, app)
        if ini is None:
            return _result(False, info)
        raw = info
        path = self._config_file(profile, app)

        data = self._load()
        record = data["games"].setdefault(profile.appid, {})
        originals = record.setdefault("originals", {})
        if not originals:                  # first change since install or since the last restore: the copy is replaced
            self._save_backup(profile.appid, raw)
            record["backup_sha256"] = _sha256(raw)
        for section, key, _ in option.entries:
            eid = "%s%s%s" % (section, SECTION_SEP, key)
            if eid not in originals:
                originals[eid] = ini.get(section, key)          # None = the key did not exist
        record["last_event"] = "set %s=%s" % (setting_id, option_id)
        record["last_change_at"] = int(self.clock())
        self._save(data)                                          # the way back is on disk before the first write

        changed = False
        try:
            for section, key, value in option.entries:
                current = ini.get(section, key)
                if current is None or current.strip() != value:
                    ini.set(section, key, value)
                    changed = True
        except (IniError, RegError) as exc:
            return _result(False, _status("error", "write_failed", "cannot edit the settings file: %s" % exc))
        if changed:
            try:
                _write_atomic(path, ini.dumps())
            except OSError as exc:
                return _result(False, _status("error", "write_failed", "cannot write the settings file: %s" % exc))
            self._log("skip-launcher: %s %s=%s" % (profile.appid, setting_id, option_id))
        return _result(True, _status("ok", "ok", "saved" if changed else "already set"), changed=changed)

    def _save_backup(self, appid, raw):
        path = self._backup_path(appid)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _write_atomic(path, raw)

    def restore(self, appid):
        """Put every key we changed back to what it was before our first change (a missing key is removed again)."""
        profile, app, status = self._context(appid)
        if profile is None or app is None or status["code"] != "ok":
            return _result(False, status)
        data = self._load()
        record = data["games"].get(profile.appid, {})
        originals = record.get("originals") or {}
        if not originals:
            return _result(True, _status("ok", "ok", "nothing was changed"), changed=False)
        ini, info = self._read(profile, app)
        if ini is None:
            return _result(False, info)
        for eid, value in originals.items():
            section, _, key = eid.partition(SECTION_SEP)
            if value is None:
                ini.remove(section, key)
            else:
                ini.set(section, key, value)
        try:
            _write_atomic(self._config_file(profile, app), ini.dumps())
        except OSError as exc:
            return _result(False, _status("error", "write_failed", "cannot write the settings file: %s" % exc))
        record["originals"] = {}
        record["last_event"] = "restored"
        record["last_change_at"] = int(self.clock())
        self._save(data)
        self._log("skip-launcher: %s restored" % profile.appid)
        return _result(True, _status("ok", "ok", "restored"), changed=True)


def _no_config():
    return _status(
        "pending", "no_config",
        "the game has not saved its settings yet: turn off Skip the launcher window once, press the game window's "
        "Play / Launch button, then come back",
    )


def _status(state, code, message):
    return {"state": state, "code": code, "message": message}


def _result(ok, status, changed=False):
    return {"ok": ok, "status": status, "changed": changed}
