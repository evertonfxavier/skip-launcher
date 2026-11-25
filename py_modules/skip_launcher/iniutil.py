"""Edit one INI file in place, keeping everything else byte for byte.

Unreal Engine 3 user files (and the Windows launcher that wrote them) are UTF-16 LE with a BOM and CRLF line ends;
a plain text editor would turn them into something the game may read differently. `IniText` remembers the encoding
and the newline, changes only the lines it is asked to change, and `dumps()` of an untouched document is the very
bytes that were read.
"""
import re

BOM_U16LE = b"\xff\xfe"
BOM_U16BE = b"\xfe\xff"
BOM_U8 = b"\xef\xbb\xbf"

_SECTION = re.compile(r"^\s*\[([^\]]*)\]")


class IniError(Exception):
    pass


class IniText(object):
    def __init__(self, raw):
        if raw.startswith(BOM_U16LE):
            self.encoding, self.bom, body = "utf-16-le", BOM_U16LE, raw[2:]
        elif raw.startswith(BOM_U16BE):
            self.encoding, self.bom, body = "utf-16-be", BOM_U16BE, raw[2:]
        elif raw.startswith(BOM_U8):
            self.encoding, self.bom, body = "utf-8", BOM_U8, raw[3:]
        else:
            self.encoding, self.bom, body = "utf-8", b"", raw
        try:
            text = body.decode(self.encoding)
        except UnicodeDecodeError as exc:
            raise IniError("cannot decode the file as %s: %s" % (self.encoding, exc))
        self.newline = "\r\n" if "\r\n" in text else "\n"
        self.lines = text.splitlines(True)

    def dumps(self):
        return self.bom + "".join(self.lines).encode(self.encoding)

    # -- reading ---------------------------------------------------------------------------------------------------
    def _section_bounds(self, section):
        """(first line after the header, line after the last line of the first section with this name) or None."""
        want = section.strip().lower()
        start = None
        for i, line in enumerate(self.lines):
            m = _SECTION.match(line)
            if m is None:
                continue
            if start is not None:
                return start, i
            if m.group(1).strip().lower() == want:
                start = i + 1
        return (start, len(self.lines)) if start is not None else None

    def has_section(self, section):
        return self._section_bounds(section) is not None

    def _find_key(self, section, key):
        bounds = self._section_bounds(section)
        if bounds is None:
            return None, None
        want = key.strip().lower()
        found = None
        for i in range(bounds[0], bounds[1]):
            line = self.lines[i]
            stripped = line.lstrip()
            if stripped.startswith((";", "#", "!", ".")):
                continue
            name, eq, _ = stripped.partition("=")
            if eq and name.strip().lower() == want:
                found = i                       # the last assignment wins, as in Unreal
        return bounds, found

    def get(self, section, key, default=None):
        _, i = self._find_key(section, key)
        if i is None:
            return default
        return self.lines[i].partition("=")[2].strip()

    # -- writing ---------------------------------------------------------------------------------------------------
    def set(self, section, key, value):
        value = str(value)
        if "\n" in value or "\r" in value:
            raise IniError("a value cannot contain a line break")
        bounds, i = self._find_key(section, key)
        nl = self.newline
        if i is not None:
            line = self.lines[i]
            ending = line[len(line.rstrip("\r\n")):] or nl
            head = line.partition("=")[0]
            self.lines[i] = "%s=%s%s" % (head, value, ending)
            return
        new = "%s=%s%s" % (key, value, nl)
        if bounds is None:
            if self.lines and not self.lines[-1].endswith(("\n", "\r")):
                self.lines[-1] += nl
            if self.lines and self.lines[-1].strip():
                self.lines.append(nl)
            self.lines.extend(["[%s]%s" % (section, nl), new])
            return
        at = bounds[1]
        while at > bounds[0] and not self.lines[at - 1].strip():
            at -= 1                              # keep the blank lines that separate sections after the new key
        if at > bounds[0] and not self.lines[at - 1].endswith(("\n", "\r")):
            self.lines[at - 1] += nl
        self.lines.insert(at, new)

    def remove(self, section, key):
        _, i = self._find_key(section, key)
        if i is not None:
            del self.lines[i]
            return True
        return False
