import re
from typing import Any, Optional


class _ScanState:
    """Tracks quote, escape, and bracket-depth state while scanning text."""

    __slots__ = ("in_single", "in_double", "escaped", "depth")

    def __init__(self) -> None:
        self.in_single = False
        self.in_double = False
        self.escaped = False
        self.depth = 0

    @property
    def in_quotes(self) -> bool:
        return self.in_single or self.in_double

    def advance(self, ch: str) -> bool:
        """Update state for *ch*. Return True when the char is structural (outside quotes/escapes)."""
        if self.escaped:
            self.escaped = False
            return False
        if ch == "\\":
            self.escaped = True
            return False
        if ch == "'" and not self.in_double:
            self.in_single = not self.in_single
            return False
        if ch == '"' and not self.in_single:
            self.in_double = not self.in_double
            return False
        return not self.in_quotes

    def update_depth(self, ch: str) -> None:
        if ch in "[{(":
            self.depth += 1
        elif ch in "]})":
            self.depth = max(0, self.depth - 1)


# ---------------------------------------------------------------------------
# Escape handling
# ---------------------------------------------------------------------------

_ESCAPE_MAP = {
    "n": "\n",
    "t": "\t",
    "\\": "\\",
    '"': '"',
    "'": "'",
}


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) < 2 or value[0] != value[-1] or value[0] not in {"'", '"'}:
        return value

    inner = value[1:-1]
    result: list[str] = []
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch == "\\" and i + 1 < len(inner):
            next_ch = inner[i + 1]
            if next_ch in _ESCAPE_MAP:
                result.append(_ESCAPE_MAP[next_ch])
                i += 2
                continue
        result.append(ch)
        i += 1
    return "".join(result)


# ---------------------------------------------------------------------------
# Text scanning helpers
# ---------------------------------------------------------------------------


def strip_inline_comment(line: str) -> str:
    """Strip comments while preserving # characters inside quoted strings."""
    state = _ScanState()
    for idx, ch in enumerate(line):
        if state.advance(ch) and ch == "#":
            return line[:idx]
    return line


def split_top_level(value: str, sep: str = ",") -> list[str]:
    """Split by *sep* while respecting quotes and nested brackets/hashes."""
    state = _ScanState()
    parts: list[str] = []
    start = 0

    for idx, ch in enumerate(value):
        if not state.advance(ch):
            continue
        state.update_depth(ch)
        if ch == sep and state.depth == 0:
            part = value[start:idx].strip()
            if part:
                parts.append(part)
            start = idx + 1

    tail = value[start:].strip()
    if tail:
        parts.append(tail)

    return parts


def normalize_key(key: str) -> str:
    clean = key.strip()
    if clean.startswith(":"):
        clean = clean[1:]
    clean = unquote(clean)
    return clean.replace("-", "_")


def split_key_value(part: str) -> Optional[tuple[str, str]]:
    state = _ScanState()

    for idx, ch in enumerate(part):
        if not state.advance(ch):
            continue
        state.update_depth(ch)
        if ch == ":" and state.depth == 0:
            left = part[:idx].strip()
            right = part[idx + 1 :].strip()
            if left and right:
                return left, right
            return None

    return None


def parse_rubyish_value(value: str) -> Any:
    raw = value.strip()
    low = raw.lower()

    if low == "true":
        return True
    if low == "false":
        return False
    if low == "nil":
        return None
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if raw.startswith(":") and re.fullmatch(r":[A-Za-z_][A-Za-z0-9_]*", raw):
        return raw[1:]

    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return unquote(raw)

    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [parse_rubyish_value(part) for part in split_top_level(inner, ",")]

    if raw.startswith("{") and raw.endswith("}"):
        inner = raw[1:-1].strip()
        options, positional = parse_options_and_positional(inner)
        if positional:
            options["_positional"] = positional
        return options

    return unquote(raw)


def parse_options_and_positional(value: str) -> tuple[dict[str, Any], list[Any]]:
    options: dict[str, Any] = {}
    positional: list[Any] = []

    if not value:
        return options, positional

    for part in split_top_level(value, ","):
        kv = split_key_value(part)
        if kv is None:
            positional.append(parse_rubyish_value(part))
            continue

        key, val = kv
        options[normalize_key(key)] = parse_rubyish_value(val)

    return options, positional


def extract_first_argument(value: str) -> tuple[Optional[str], str]:
    remaining = value.lstrip()
    if not remaining:
        return None, ""

    if remaining[0] in {"'", '"'}:
        quote = remaining[0]
        escaped = False
        for idx in range(1, len(remaining)):
            ch = remaining[idx]
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == quote:
                return unquote(remaining[: idx + 1]), remaining[idx + 1 :]
        return None, ""

    parts = split_top_level(remaining, ",")
    if not parts:
        return None, ""

    first = parts[0].strip()
    rest_start = remaining.find(first) + len(first)
    rest = remaining[rest_start:]
    return unquote(first), rest


def sanitize_options(value: dict[str, Any], ignore_keys: Optional[list[str]] = None) -> dict[str, Any]:
    ignore_keys = ignore_keys or []
    return {k: v for k, v in value.items() if k not in ignore_keys and not k.startswith("_")}
