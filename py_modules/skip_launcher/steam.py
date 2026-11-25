"""Steam library discovery: libraries, installed apps, Proton prefixes, running games."""
import os
import re

STATE_FULLY_INSTALLED = 4


def parse_vdf(text):
    """Minimal parser for Valve's text KeyValues (enough for libraryfolders/appmanifest)."""
    tokens = re.findall(r'"((?:[^"\\]|\\.)*)"|([{}])', text)
    root = {}
    stack = [root]
    key = None
    for quoted, brace in tokens:
        if brace == "{":
            child = {}
            stack[-1][key] = child
            stack.append(child)
            key = None
        elif brace == "}":
            if len(stack) > 1:
                stack.pop()
            key = None
        elif key is None:
            key = quoted
        else:
            stack[-1][key] = quoted.replace("\\\\", "\\")
            key = None
    return root


def steam_roots(home):
    seen, roots = set(), []
    for cand in (".local/share/Steam", ".steam/steam", ".steam/root"):
        path = os.path.join(home, cand)
        if os.path.isdir(os.path.join(path, "steamapps")):
            real = os.path.realpath(path)
            if real not in seen:
                seen.add(real)
                roots.append(path)
    return roots


def library_paths(home):
    """All Steam library folders (internal, SD card, extra drives)."""
    paths, seen = [], set()
    for root in steam_roots(home):
        candidates = [root]
        vdf = os.path.join(root, "steamapps", "libraryfolders.vdf")
        try:
            with open(vdf, encoding="utf-8", errors="replace") as f:
                data = parse_vdf(f.read()).get("libraryfolders", {})
            for entry in data.values():
                if isinstance(entry, dict) and entry.get("path"):
                    candidates.append(entry["path"])
        except OSError:
            pass
        for path in candidates:
            real = os.path.realpath(path)
            if real not in seen and os.path.isdir(os.path.join(path, "steamapps")):
                seen.add(real)
                paths.append(path)
    return paths


def find_app(home, appid):
    """The installed app with this appid (None when it is not installed), with its library and Proton prefix."""
    for lib in library_paths(home):
        steamapps = os.path.join(lib, "steamapps")
        manifest = os.path.join(steamapps, "appmanifest_%s.acf" % appid)
        try:
            with open(manifest, encoding="utf-8", errors="replace") as f:
                state = parse_vdf(f.read()).get("AppState", {})
        except OSError:
            continue
        installdir = state.get("installdir", "")
        return {
            "appid": str(appid),
            "name": state.get("name", ""),
            "library": lib,
            "install_path": os.path.join(steamapps, "common", installdir),
            "prefix": os.path.join(steamapps, "compatdata", str(appid), "pfx"),
            "state_flags": int(state.get("StateFlags", "0") or 0),
        }
    return None


def is_ready(app):
    """Fully installed and not being updated or validated right now."""
    return app["state_flags"] == STATE_FULLY_INSTALLED and os.path.isdir(app["install_path"])


def running_cmdlines(proc_root="/proc"):
    """Command lines of running processes (used to tell whether a game is open)."""
    cmdlines = []
    try:
        pids = [p for p in os.listdir(proc_root) if p.isdigit()]
    except OSError:
        return cmdlines
    for pid in pids:
        try:
            with open(os.path.join(proc_root, pid, "cmdline"), "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode("utf-8", "replace")
        except OSError:
            continue
        if cmd:
            cmdlines.append(cmd)
    return cmdlines


def install_forms(install_path):
    """Names the install folder may run under (as reported, and its realpath), each with a trailing '/'."""
    path = install_path.rstrip("/")
    names = [path]
    try:
        real = os.path.realpath(path)
        if real != path:
            names.append(real)
    except (OSError, ValueError):
        pass
    return [n + "/" for n in names]


def is_running(app, cmdlines):
    """True when a process runs from the game's folder (any name, or the Z:\\ form Proton uses) or is its launcher.

    The Steam launcher's command line carries `AppId=<appid>` as a token of its own (never part of a longer number).
    """
    forms = install_forms(app["install_path"])
    wins = ["Z:" + f.replace("/", "\\") for f in forms]
    appid = str(app.get("appid", ""))
    token = re.compile(r"(?<!\S)AppId=%s(?!\S)" % re.escape(appid)) if appid.isdigit() else None
    for c in cmdlines:
        if any(f in c for f in forms) or any(w in c for w in wins) or (token and token.search(c)):
            return True
    return False


def prefix_in_use(app, proc_root="/proc"):
    """True when any process still belongs to the game's Proton prefix (its `wineserver` outlives the game for a moment).

    Wine keeps the registry in memory and writes `user.reg` when its server exits, so a registry edit made while the
    prefix is alive would be overwritten. Proton gives every process WINEPREFIX and STEAM_COMPAT_DATA_PATH.
    """
    wanted = set()
    for path in (app["prefix"], os.path.dirname(app["prefix"])):
        wanted.add(path.rstrip("/"))
        try:
            wanted.add(os.path.realpath(path).rstrip("/"))
        except (OSError, ValueError):
            pass
    try:
        pids = [p for p in os.listdir(proc_root) if p.isdigit()]
    except OSError:
        return False
    for pid in pids:
        try:
            with open(os.path.join(proc_root, pid, "environ"), "rb") as f:
                env = f.read()
        except OSError:
            continue
        for item in env.split(b"\0"):
            name, _, value = item.partition(b"=")
            if name in (b"WINEPREFIX", b"STEAM_COMPAT_DATA_PATH"):
                value = value.decode("utf-8", "replace").rstrip("/")
                if value in wanted or os.path.realpath(value) in wanted:
                    return True
    return False
