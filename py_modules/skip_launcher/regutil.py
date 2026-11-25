"""Edit one Wine registry file (`user.reg`) in place, keeping everything else byte for byte.

Some launcher windows (the Max Payne games) keep their choices in the Windows registry. Under Proton that registry is a
plain text file in the prefix: sections like `[Software\\\\Remedy Entertainment\\\\Max Payne\\\\Video Settings] 1795560333`
(backslashes doubled, a time stamp after the name) followed by `"Display Width"=dword:00000780` lines. `RegText` has the
same small interface as `IniText` (get / set / remove / dumps), so the engine treats both alike.

Rules that keep it safe:
  * section names are written exactly as they appear in the file (doubled backslashes), compared without case;
  * only the lines asked for are changed; time stamps, other sections and the line endings stay as they were;
  * a section that does not exist is never created (Wine's own writer owns the time stamps): `set` raises `RegError`;
  * Wine only writes this file when its server exits, so the engine must not edit it while a process of the prefix lives.
"""
import re

_SECTION = re.compile(r"^\[(.*)\](?:\s+\d+)?\s*$")
_KEY = re.compile(r'^("(?:[^"\\]|\\.)*"|@)=(.*?)(\r?\n)?$', re.S)


class RegError(Exception):
    pass


def _key_name(token):
    return token if token == "@" else token[1:-1]


class RegText(object):
    def __init__(self, raw):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RegError("cannot decode the registry file as UTF-8: %s" % exc)
        self.newline = "\r\n" if "\r\n" in text else "\n"
        self.lines = text.splitlines(True)

    def dumps(self):
        return "".join(self.lines).encode("utf-8")

    def _bounds(self, section):
        want = section.strip().lower()
        start = None
        for i, line in enumerate(self.lines):
            m = _SECTION.match(line.rstrip("\r\n"))
            if m is None:
                continue
            if start is not None:
                return start, i
            if m.group(1).strip().lower() == want:
                start = i + 1
        return (start, len(self.lines)) if start is not None else None

    def has_section(self, section):
        return self._bounds(section) is not None

    def _find_key(self, section, key):
        bounds = self._bounds(section)
        if bounds is None:
            return None, None
        want = key.strip().lower()
        for i in range(bounds[0], bounds[1]):
            m = _KEY.match(self.lines[i])
            if m and _key_name(m.group(1)).lower() == want:
                return bounds, i
        return bounds, None

    def get(self, section, key, default=None):
        _, i = self._find_key(section, key)
        if i is None:
            return default
        return _KEY.match(self.lines[i]).group(2).strip()

    def set(self, section, key, value):
        value = str(value)
        if "\n" in value or "\r" in value:
            raise RegError("a value cannot contain a line break")
        bounds, i = self._find_key(section, key)
        if bounds is None:
            raise RegError("the registry section %r does not exist" % section)
        if i is not None:
            m = _KEY.match(self.lines[i])
            self.lines[i] = "%s=%s%s" % (m.group(1), value, m.group(3) or self.newline)
            return
        at = bounds[1]
        while at > bounds[0] and not self.lines[at - 1].strip():
            at -= 1                              # the blank line that ends the section stays after the new key
        if at > bounds[0] and not self.lines[at - 1].endswith("\n"):
            self.lines[at - 1] += self.newline
        self.lines.insert(at, '"%s"=%s%s' % (key, value, self.newline))

    def remove(self, section, key):
        _, i = self._find_key(section, key)
        if i is not None:
            del self.lines[i]
            return True
        return False
