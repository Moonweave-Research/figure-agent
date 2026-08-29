"""Bind rendered label text back to the TikZ node that produced it.

Detectors see labels only as rendered PDF words, so a finding about a label
cannot name the source line to edit. `critique_adjudication` already gates its
auto-apply route on a two-integer ``tex_lines`` field, and `check_visual_clash`
already carries that field — permanently ``None``, because nothing ever filled
it. Today the only thing that fills it is a reviewer typing line numbers into
critique.md by hand.

This binds the machine half. A node body is the last balanced brace group
before the terminating semicolon, not the first one after ``\\node``: an
options list or a calc coordinate can carry braces of its own, and reading
those as the label produces a confident wrong answer, which is worse than no
answer. Every uncertainty resolves to nothing rather than a guess — a phrase
matching no node, or more than one, yields ``None``.
"""

from __future__ import annotations

import re

_NODE_START_RE = re.compile(r"\\node\b")
_TEX_MARKUP_RE = re.compile(r"\\[A-Za-z@]+\s*|[$~^_]|\\\\")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalized(text: str) -> str:
    """Strip TeX markup so a source label compares against rendered words."""
    stripped = _TEX_MARKUP_RE.sub(" ", text).replace("{", " ").replace("}", " ")
    return _WHITESPACE_RE.sub(" ", stripped).strip()


def _brace_groups(text: str, start: int, stop: int) -> list[tuple[int, int]]:
    """Return (open, close) spans of top-level brace groups within a slice."""
    groups: list[tuple[int, int]] = []
    depth = 0
    opened = -1
    index = start
    while index < stop:
        char = text[index]
        if char == "\\":
            # A backslash escapes the next character, so \{ is not a group.
            index += 2
            continue
        if char == "{":
            if depth == 0:
                opened = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and opened >= 0:
                groups.append((opened, index))
                opened = -1
            elif depth < 0:
                return groups
        index += 1
    return groups


def _statement_end(text: str, start: int) -> int:
    """Index of the semicolon ending this node statement, or -1."""
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == ";" and depth == 0:
            return index
        index += 1
    return -1


def node_index(tex_text: str) -> list[dict[str, object]]:
    """Return every node whose body can be read literally, with its line."""
    nodes: list[dict[str, object]] = []
    for match in _NODE_START_RE.finditer(tex_text):
        end = _statement_end(tex_text, match.end())
        if end < 0:
            continue
        groups = _brace_groups(tex_text, match.end(), end)
        if not groups:
            continue
        open_index, close_index = groups[-1]
        body = tex_text[open_index + 1 : close_index]
        normalized = _normalized(body)
        if not normalized:
            continue
        nodes.append(
            {
                "text": normalized,
                "raw_text": body,
                "source_line": tex_text.count("\n", 0, match.start()) + 1,
            }
        )
    return nodes


def unique_source_line(tex_text: str, phrase: str) -> int | None:
    """Return the source line of the one node containing ``phrase``.

    ``None`` whenever the answer is not unique, which is the honest result for
    a repeated label, a macro-built label, or text this parser cannot read.
    """
    needle = _normalized(phrase)
    if not needle:
        return None
    matches = {
        int(node["source_line"]) for node in node_index(tex_text) if needle in str(node["text"])
    }
    if len(matches) != 1:
        return None
    return matches.pop()
