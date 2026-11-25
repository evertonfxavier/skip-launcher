import asyncio
import json
import os
import sys
from typing import Any, Dict

import decky

PLUGIN_DIR = getattr(decky, "DECKY_PLUGIN_DIR", os.path.dirname(os.path.abspath(__file__)))
PY_MODULES = os.path.join(PLUGIN_DIR, "py_modules")
if PY_MODULES not in sys.path:
    sys.path.insert(0, PY_MODULES)

from skip_launcher import launch  # noqa: E402
from skip_launcher.engine import Engine  # noqa: E402
from skip_launcher.profiles import PROFILES  # noqa: E402


def make_engine() -> Engine:
    return Engine(
        home=decky.DECKY_USER_HOME,
        settings_dir=decky.DECKY_PLUGIN_SETTINGS_DIR,
        logger=decky.logger,
    )


class Plugin:
    _engine = None

    def _get_engine(self) -> Engine:
        if self._engine is None:
            self._engine = make_engine()
        return self._engine

    async def ping(self) -> Dict[str, str]:
        return {"status": "ok", "version": getattr(decky, "DECKY_PLUGIN_VERSION", "unknown")}

    # JSON strings travel reliably through the Decky bridge.
    async def list_games(self) -> str:
        try:
            games = await asyncio.to_thread(self._get_engine().list_games)
            return json.dumps({"ok": True, "error": "", "games": games})
        except Exception as exc:
            decky.logger.exception("list_games failed")
            return json.dumps({"ok": False, "error": str(exc), "games": []})

    async def get_game(self, appid: str) -> str:
        try:
            game = await asyncio.to_thread(self._get_engine().get_game, str(appid))
            return json.dumps({"ok": True, "error": "", "game": game})
        except Exception as exc:
            decky.logger.exception("get_game failed")
            return json.dumps({"ok": False, "error": str(exc), "game": None})

    async def set_option(self, appid: str, setting_id: str, option_id: str) -> Dict[str, Any]:
        try:
            return await asyncio.to_thread(self._get_engine().set_option, str(appid), setting_id, option_id)
        except Exception as exc:
            decky.logger.exception("set_option failed")
            return {"ok": False, "changed": False, "status": {"state": "error", "code": "write_failed", "message": str(exc)}}

    async def restore_game(self, appid: str) -> Dict[str, Any]:
        try:
            return await asyncio.to_thread(self._get_engine().restore, str(appid))
        except Exception as exc:
            decky.logger.exception("restore failed")
            return {"ok": False, "changed": False, "status": {"state": "error", "code": "write_failed", "message": str(exc)}}

    async def plan_launch_option(self, appid: str, current: str, enable: bool) -> Dict[str, Any]:
        """The launch-options text the UI should store (the UI reads and writes Steam's own value)."""
        profile = PROFILES.get(str(appid))
        if profile is None:
            return {"ok": False, "options": current, "enabled": False}
        fn = launch.profile_enable if enable else launch.profile_disable
        options = fn(current or "", profile)
        return {"ok": True, "options": options, "enabled": launch.profile_enabled(options, profile)}

    async def launch_state(self, appid: str, current: str) -> Dict[str, Any]:
        profile = PROFILES.get(str(appid))
        if profile is None:
            return {"ok": False, "enabled": False}
        return {"ok": True, "enabled": launch.profile_enabled(current or "", profile)}

    async def _main(self):
        decky.logger.info("skip-launcher backend loaded")

    async def _unload(self):
        decky.logger.info("skip-launcher backend unloaded")

    async def _uninstall(self):
        decky.logger.info("skip-launcher backend uninstalled")
