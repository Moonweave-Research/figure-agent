"""BLOCKER-tier Style Lock linter for TikZ .tex files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

TIKZ_BUILTIN_COLORS: frozenset[str] = frozenset({"black", "white", "gray", "none", "transparent"})

_RE_DEFINECOLOR = re.compile(r"\\definecolor\b")
_RE_FONT_OVERRIDE = re.compile(r"\\(setmainfont|setsansfont|setmonofont)\b")
_RE_RAW_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")
_RE_COLOR_OPTION = re.compile(r"\b(fill|draw|text|color)\s*=\s*([!\w]+)")
_RE_COLOR_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
_RE_PALETTE_TOKEN = re.compile(r"\\definecolor\{([A-Za-z][A-Za-z0-9]*)\}")


class Violation(NamedTuple):
    line: int
    category: str
    snippet: str
    message: str


def strip_tex_comment(line: str) -> str:
    result: list[str] = []
    idx = 0
    while idx < len(line):
        ch = line[idx]
        if ch == "\\" and idx + 1 < len(line) and line[idx + 1] == "%":
            result.append("\\%")
            idx += 2
        elif ch == "%":
            break
        else:
            result.append(ch)
            idx += 1
    return "".join(result)


def parse_palette(sty_path: Path | None = None) -> set[str]:
    if sty_path is None:
        sty_path = Path(__file__).resolve().parents[1] / "styles" / "polymer-paper-preamble.sty"
    names: set[str] = set()
    for raw_line in sty_path.read_text(encoding="utf-8").splitlines():
        for match in _RE_PALETTE_TOKEN.finditer(raw_line):
            names.add(match.group(1))
    return names


def lint(tex_path: Path) -> list[Violation]:
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

        for match in _RE_COLOR_OPTION.finditer(stripped):
            value = match.group(2)
            segments = value.split("!")
            for segment in segments:
                if not _RE_COLOR_NAME.fullmatch(segment):
                    continue
                if segment not in allowed_colors:
                    violations.append(
                        Violation(
                            line=line_num,
                            category="non_palette_color",
                            snippet=snippet,
                            message=f"color '{segment}' is not in the palette; use a palette macro",
                        )
                    )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="BLOCKER-tier Style Lock lint for .tex files")
    parser.add_argument("tex_path", type=Path)
    args = parser.parse_args()

    violations = lint(args.tex_path)
    violations_sorted = sorted(violations, key=lambda v: (v.line, v.category))
    for violation in violations_sorted:
        print(f"{args.tex_path}:{violation.line}: {violation.category}: {violation.message}")

    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
