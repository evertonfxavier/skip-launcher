"""What a game profile is: the launcher to skip, the real executable, where the launcher kept its choices, and the
choices themselves.

A setting is either a `toggle` (on / off) or a `choice` (a list of options). Both are lists of options; one option
sets one or more `(section, key, value)` entries of the game's ini file, so a resolution (ResX + ResY) or a whole
detail level (twelve keys) is still one control. The current option is the one whose entries all match the file;
when none does the setting reads as "custom" and the UI says so (it never guesses).
"""

SECTION_SEP = "|"


def entry_id(section, key):
    return "%s%s%s" % (section, SECTION_SEP, key)


class Option(object):
    def __init__(self, option_id, label, entries):
        self.id = option_id
        self.label = label                         # English fallback; the UI looks `label_key` up first
        self.entries = tuple(entries)              # ((section, key, value), ...)

    def to_dict(self, setting_id):
        return {"id": self.id, "label": self.label, "label_key": "option.%s.%s" % (setting_id, self.id)}


class Setting(object):
    def __init__(self, setting_id, kind, label, options, group="video", note_key=None):
        assert kind in ("toggle", "choice")
        self.id = setting_id
        self.kind = kind
        self.label = label
        self.options = list(options)
        self.group = group
        self.note_key = note_key

    def option(self, option_id):
        for opt in self.options:
            if opt.id == option_id:
                return opt
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "label_key": "setting.%s" % self.id,
            "group": self.group,
            "note_key": self.note_key,
            "options": [o.to_dict(self.id) for o in self.options],
        }


def same_value(a, b):
    """Ini values compare case-insensitively (True / TRUE / true) and numbers as numbers (512 / 512.0)."""
    a, b = str(a).strip(), str(b).strip()
    if a.lower() == b.lower():
        return True
    try:
        return float(a) == float(b)
    except ValueError:
        return False


class Profile(object):
    appid = ""
    name = ""
    revision = 1
    support = "full"
    launcher_exe = ""                              # the executable Steam starts (the window)
    game_exe = ""                                  # the real game
    config_rel = ""                                # the settings file, relative to the Proton prefix (`pfx/`)
    config_format = "ini"                          # "ini" (UTF-16 or UTF-8 text) or "reg" (Wine's user.reg)
    required_section = None                        # a section that exists once the game's window ran at least once
    required_key = None                            # (section, key) that must exist: the game itself saved its values once
    skip_args = ""                                 # when set, skipping = adding this command-line word (no exe swap)
    settings = ()

    def setting(self, setting_id):
        for s in self.settings:
            if s.id == setting_id:
                return s
        return None

    def current_option(self, setting, ini):
        """The id of the option the file matches, or None (custom / unknown)."""
        for opt in setting.options:
            if all(
                (lambda v: v is not None and same_value(v, value))(ini.get(section, key))
                for section, key, value in opt.entries
            ):
                return opt.id
        return None
