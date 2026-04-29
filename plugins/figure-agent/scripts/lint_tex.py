"""BLOCKER-tier Style Lock linter for TikZ .tex files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

TIKZ_BUILTIN_COLORS: frozenset[str] = frozenset({"black", "white", "gray", "none", "transparent"})

# xcolor's standard named colors. If any of these appears as a positional
# option or as the value of fill/draw/text/color, the lint rejects it —
# the palette is the only sanctioned source of color.
KNOWN_NON_PALETTE_COLORS: frozenset[str] = frozenset(
    {
        "red",
        "blue",
        "green",
        "yellow",
        "cyan",
        "magenta",
        "orange",
        "purple",
        "pink",
        "lime",
        "violet",
        "brown",
        "olive",
        "teal",
    }
)

_RE_DEFINECOLOR = re.compile(r"\\definecolor\b")
_RE_FONT_OVERRIDE = re.compile(r"\\(setmainfont|setsansfont|setmonofont)\b")
_RE_RAW_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")
_RE_OPTION_BLOCK = re.compile(r"\[([^\[\]]*)\]")
_RE_KEY_VALUE = re.compile(r"^\s*(fill|draw|text|color)\s*=\s*\{?([!\w]+)\}?\s*$")
_RE_BARE_TOKEN = re.compile(r"^\s*([A-Za-z][A-Za-z0-9]*)\s*$")
_RE_COLOR_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
_RE_PALETTE_TOKEN = re.compile(r"\\definecolor\{([A-Za-z][A-Za-z0-9]*)\}")


class Violation(NamedTuple):
    line: int
    category: str
    snippet: str
    message: str


def strip_tex_comment(line: str) -> str:
    """Remove TeX comments from a line, respecting backslash escapes.

    LaTeX semantics: any backslash followed by a character escapes that
    character (literal `\\` is a newline command; `\\%` is therefore newline +
    comment, NOT a literal `%`). Walk char-by-char and consume two chars on
    every escape so `\\%` correctly truncates the rest of the line.
    """
    result: list[str] = []
    idx = 0
    while idx < len(line):
        ch = line[idx]
        if ch == "\\" and idx + 1 < len(line):
            result.append(ch)
            result.append(line[idx + 1])
            idx += 2
            continue
        if ch == "%":
            break
        result.append(ch)
        idx += 1
    return "".join(result)


def parse_palette(sty_path: Path | None = None) -> set[str]:
    """Extract palette color names from the polymer preamble.

    Returns the empty set if the .sty file is missing or unreadable; main()
    treats an empty palette as a configuration error and exits with code 2.
    """
    if sty_path is None:
        sty_path = Path(__file__).resolve().parents[1] / "styles" / "polymer-paper-preamble.sty"
    if not sty_path.is_file():
        return set()
    names: set[str] = set()
    for raw_line in sty_path.read_text(encoding="utf-8").splitlines():
        for match in _RE_PALETTE_TOKEN.finditer(raw_line):
            names.add(match.group(1))
    return names


def _check_color_segments(
    value: str,
    line_num: int,
    snippet: str,
    allowed_colors: set[str] | frozenset[str],
) -> list[Violation]:
    out: list[Violation] = []
    for segment in value.split("!"):
        if _RE_COLOR_NAME.fullmatch(segment) and segment not in allowed_colors:
            out.append(
                Violation(
                    line=line_num,
                    category="non_palette_color",
                    snippet=snippet,
                    message=f"color '{segment}' is not in the palette; use a palette macro",
                )
            )
    return out


def lint(tex_path: Path, palette: set[str] | None = None) -> list[Violation]:
    if palette is None:
        palette = parse_palette()
    allowed_colors = palette | TIKZ_BUILTIN_COLORS
    violations: list[Violation] = []

    raw_lines = tex_path.read_text(encoding="utf-8").splitlines()
    for line_num, raw_line in enumerate(raw_lines, start=1):
        stripped = strip_tex_comment(raw_line)
        snippet = raw_line.rstrip()[:80]

        if _RE_DEFINECOLOR.search(stripped):
            violations.append(
                Violation(
                    line=line_num,
                    category="definecolor",
                    snippet=snippet,
                    message=(
                        "redefining colors is forbidden in user .tex; the preamble owns the palette"
                    ),
                )
            )

        if _RE_FONT_OVERRIDE.search(stripped):
            violations.append(
                Violation(
                    line=line_num,
                    category="font_override",
                    snippet=snippet,
                    message="overriding fonts is forbidden in user .tex; the preamble owns fonts",
                )
            )

        if _RE_RAW_HEX.search(stripped):
            violations.append(
                Violation(
                    line=line_num,
                    category="raw_hex",
                    snippet=snippet,
                    message="raw hex color is forbidden; use a palette macro",
                )
            )

        for option_match in _RE_OPTION_BLOCK.finditer(stripped):
            block_content = option_match.group(1)
            for token in block_content.split(","):
                kv = _RE_KEY_VALUE.match(token)
                if kv:
                    value = kv.group(2)
                    violations.extend(
                        _check_color_segments(value, line_num, snippet, allowed_colors)
                    )
                    continue
                bare = _RE_BARE_TOKEN.match(token)
                if bare and bare.group(1) in KNOWN_NON_PALETTE_COLORS:
                    violations.append(
                        Violation(
                            line=line_num,
                            category="non_palette_color",
                            snippet=snippet,
                            message=(
                                f"color '{bare.group(1)}' is not in the palette; "
                                "use a palette macro"
                            ),
                        )
                    )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="BLOCKER-tier Style Lock lint for .tex files")
    parser.add_argument("tex_path", type=Path)
    args = parser.parse_args()

    palette = parse_palette()
    if not palette:
        print(
            "lint_tex.py: palette source missing or empty; "
            "expected styles/polymer-paper-preamble.sty with \\definecolor entries",
            file=sys.stderr,
        )
        return 2

    violations = lint(args.tex_path, palette=palette)
    violations_sorted = sorted(violations, key=lambda v: (v.line, v.category))
    for violation in violations_sorted:
        print(f"{args.tex_path}:{violation.line}: {violation.category}: {violation.message}")

    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
