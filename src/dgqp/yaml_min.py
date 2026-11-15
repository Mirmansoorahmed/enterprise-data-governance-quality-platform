"""Minimal, dependency-free YAML reader for this repo's own files.

Why this exists
---------------
The CI sandbox has no network access, so PyYAML cannot be installed. The ODCS
contracts, RACI register and policy files in this repo are authored in a small,
predictable YAML subset. This module parses exactly that subset:

* block mappings (``key: value``) with two-space indentation
* block sequences (``- item``), including sequences of mappings
* scalars: plain, single-quoted and double-quoted strings, integers, floats,
  booleans (``true``/``false``), null (``null``/``~``/empty)
* inline flow scalars only inside quotes; ``#`` comments outside quotes
* ``|`` and ``>`` block scalars (folded/literal), and ``---`` document start

It is NOT a general YAML parser. It raises :class:`YamlError` on anything it
does not understand rather than guessing, so a malformed repo file fails loudly.
When PyYAML is available (local/hybrid), callers may prefer it; the structures
produced here are plain dict/list/str/int/float/bool/None and compare equal.
"""

from __future__ import annotations

from typing import Any


class YamlError(ValueError):
    """Raised when the input is outside the supported YAML subset."""


def load(text: str) -> Any:
    """Parse a YAML document from *text* and return a Python object."""
    lines = _logical_lines(text)
    if not lines:
        return None
    value, idx = _parse_block(lines, 0, lines[0][0])
    if idx != len(lines):
        raise YamlError(f"trailing content at line {lines[idx][2]}")
    return value


def load_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return load(handle.read())


# --- internal -------------------------------------------------------------

def _logical_lines(text: str) -> list[tuple[int, str, int]]:
    """Return (indent, content, lineno) for each significant line.

    Blank lines, comment-only lines and the ``---`` / ``...`` document markers
    are dropped. Block scalars are not pre-expanded here; they are handled where
    a ``|`` or ``>`` value is encountered.
    """
    out: list[tuple[int, str, int]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped in ("---", "..."):
            continue
        lead = raw[: len(raw) - len(raw.lstrip())]
        if "\t" in lead:
            raise YamlError(f"tab indentation at line {lineno}")
        indent = len(raw) - len(raw.lstrip(" "))
        out.append((indent, _strip_comment(raw[indent:]), lineno))
    return out


def _strip_comment(content: str) -> str:
    """Remove a trailing ``#`` comment that is outside any quotes."""
    in_single = in_double = False
    for i, ch in enumerate(content):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if i == 0 or content[i - 1] == " ":
                return content[:i].rstrip()
    return content.rstrip()


def _parse_block(lines, idx, indent):
    if idx >= len(lines):
        return None, idx
    cur_indent, content, _ = lines[idx]
    if cur_indent != indent:
        raise YamlError(f"unexpected indent at line {lines[idx][2]}")
    if content.startswith("- "):
        return _parse_sequence(lines, idx, indent)
    return _parse_mapping(lines, idx, indent)


def _parse_sequence(lines, idx, indent):
    items: list[Any] = []
    while idx < len(lines):
        cur_indent, content, lineno = lines[idx]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise YamlError(f"bad sequence indent at line {lineno}")
        if not (content == "-" or content.startswith("- ")):
            break
        rest = content[1:].lstrip()
        dash_offset = cur_indent + (len(content) - len(rest))
        if rest == "":
            # Nested block starts on the next line.
            value, idx = _parse_block(lines, idx + 1, lines[idx + 1][0])
            items.append(value)
        elif _is_key_line(rest):
            # Sequence item is a mapping whose first key follows the dash. The
            # item's own keys are aligned at the column after "- ". Rewrite this
            # line to start at that column, then parse a mapping there.
            item_lines = [(dash_offset, rest, lineno)]
            j = idx + 1
            while j < len(lines) and lines[j][0] >= dash_offset and not (
                lines[j][0] == indent
                and (lines[j][1] == "-" or lines[j][1].startswith("- "))
            ):
                item_lines.append(lines[j])
                j += 1
            value, consumed = _parse_mapping(item_lines, 0, dash_offset)
            if consumed != len(item_lines):
                raise YamlError(f"unparsed sequence item at line {lineno}")
            items.append(value)
            idx = j
        else:
            items.append(_scalar(rest))
            idx += 1
    return items, idx


def _is_key_line(text: str) -> bool:
    _, sep, _ = _split_key(text, 0)
    return sep


def _parse_mapping(lines, idx, indent):
    mapping: dict[str, Any] = {}
    while idx < len(lines):
        cur_indent, content, lineno = lines[idx]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise YamlError(f"bad mapping indent at line {lineno}")
        if content.startswith("- "):
            break
        key, sep, rest = _split_key(content, lineno)
        if not sep:
            raise YamlError(f"expected 'key: value' at line {lineno}")
        rest = rest.strip()
        if rest in ("|", ">", "|-", ">-", "|+", ">+"):
            value, idx = _parse_block_scalar(lines, idx + 1, indent, rest)
        elif rest == "":
            if idx + 1 < len(lines) and lines[idx + 1][0] > indent:
                value, idx = _parse_block(lines, idx + 1, lines[idx + 1][0])
            else:
                value, idx = None, idx + 1
        else:
            value, idx = _scalar(rest), idx + 1
        mapping[key] = value
    return mapping, idx


def _parse_block_scalar(lines, idx, parent_indent, style):
    # Minimal literal/folded block scalar: collect deeper-indented lines.
    collected: list[str] = []
    child_indent = None
    while idx < len(lines):
        cur_indent, content, _ = lines[idx]
        if cur_indent <= parent_indent:
            break
        if child_indent is None:
            child_indent = cur_indent
        collected.append(content)
        idx += 1
    joiner = "\n" if style.startswith("|") else " "
    text = joiner.join(collected)
    if not style.endswith("-"):
        text += "\n" if style.startswith("|") else ""
    return text, idx


def _split_key(content, lineno):
    in_single = in_double = False
    for i, ch in enumerate(content):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ":" and not in_single and not in_double:
            if i + 1 == len(content) or content[i + 1] == " ":
                return _dequote(content[:i].strip()), True, content[i + 1:]
    return content, False, ""


def _looks_scalar(text: str) -> bool:
    """True when ``text`` is a quoted string that merely contains a colon."""
    return (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    )


def _scalar(token: str) -> Any:
    token = token.strip()
    if token == "" or token in ("~", "null", "Null", "NULL"):
        return None
    if token in ("true", "True", "TRUE"):
        return True
    if token in ("false", "False", "FALSE"):
        return False
    if (token.startswith('"') and token.endswith('"')) or (
        token.startswith("'") and token.endswith("'")
    ):
        return _dequote(token)
    if token.startswith("[") and token.endswith("]"):
        return _flow_seq(token)
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        pass
    return token


def _flow_seq(token: str) -> list[Any]:
    inner = token[1:-1].strip()
    if not inner:
        return []
    return [_scalar(part.strip()) for part in _split_flow(inner)]


def _split_flow(inner: str) -> list[str]:
    parts: list[str] = []
    buf = ""
    in_single = in_double = False
    depth = 0
    for ch in inner:
        if ch == "'" and not in_double:
            in_single = not in_single
            buf += ch
        elif ch == '"' and not in_single:
            in_double = not in_double
            buf += ch
        elif ch in "([" and not in_single and not in_double:
            depth += 1
            buf += ch
        elif ch in ")]" and not in_single and not in_double:
            depth = max(depth - 1, 0)
            buf += ch
        elif ch == "," and not in_single and not in_double and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return parts


def _dequote(token: str) -> str:
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1].encode().decode("unicode_escape")
    if token.startswith("'") and token.endswith("'"):
        return token[1:-1].replace("''", "'")
    return token
