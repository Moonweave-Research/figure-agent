#!/usr/bin/env python3
"""Safely shift scoped literal TikZ coordinates in a .tex file."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


class TexCoordinateShiftError(ValueError):
    """Controlled user-facing coordinate shift error."""


@dataclass(frozen=True)
class ShiftResult:
    text: str
    changed_count: int


_COORD_RE = re.compile(
    r"\(\s*(?P<x>[+-]?\d+(?:\.\d+)?)\s*,\s*(?P<y>[+-]?\d+(?:\.\d+)?)\s*\)"
)
_FOREACH_RE = re.compile(
    r"\\foreach\s+(?P<vars>(?:\\[A-Za-z@]+\s*/\s*)+\\[A-Za-z@]+)\s+in\s*\{(?P<body>[^{}]*)\}"
)
_SLASH_NUMBER_RE = re.compile(
    r"(?P<x>[+-]?\d+(?:\.\d+)?)/(?P<y>[+-]?\d+(?:\.\d+)?)(?P<tail>(?:/[+-]?\d+(?:\.\d+)?)*)"
)
_SAFE_FOREACH_VAR_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("x", "y"),
        ("dx", "dy"),
        ("px", "py"),
        ("qx", "qy"),
        ("tx", "ty"),
        ("cx", "cy"),
    }
)


def _decimal(raw: str, label: str) -> Decimal:
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise TexCoordinateShiftError(f"{label} must be numeric") from exc


def _fraction_digits(raw: str) -> int:
    if "." not in raw:
        return 0
    return len(raw.rsplit(".", 1)[1])


def _format_shifted(raw: str, delta: Decimal, delta_raw: str) -> str:
    value = _decimal(raw, "coordinate") + delta
    digits = max(_fraction_digits(raw), _fraction_digits(delta_raw))
    if digits == 0:
        return str(value.quantize(Decimal("1")))
    quantum = Decimal("1").scaleb(-digits)
    return f"{value.quantize(quantum):f}"


def _line_selected(line_number: int, line_ranges: list[tuple[int, int]] | None) -> bool:
    if line_ranges is None:
        return True
    return any(start <= line_number <= end for start, end in line_ranges)


def _split_tex_comment(line: str) -> tuple[str, str]:
    idx = 0
    while idx < len(line):
        if line[idx] == "\\":
            idx += 2
            continue
        if line[idx] == "%":
            return line[:idx], line[idx:]
        idx += 1
    return line, ""


def _strip_var(raw: str) -> str:
    return raw.strip().lstrip("\\")


def _safe_foreach_vars(raw_vars: str) -> bool:
    vars_ = [_strip_var(part) for part in raw_vars.split("/")]
    if len(vars_) < 2:
        return False
    return (vars_[0], vars_[1]) in _SAFE_FOREACH_VAR_PAIRS


def _shift_foreach_body(
    body: str,
    *,
    dx: Decimal,
    dy: Decimal,
    dx_raw: str,
    dy_raw: str,
) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return (
            f"{_format_shifted(match.group('x'), dx, dx_raw)}/"
            f"{_format_shifted(match.group('y'), dy, dy_raw)}"
            f"{match.group('tail')}"
        )

    return _SLASH_NUMBER_RE.sub(replace, body), count


def _shift_foreach_line(
    line: str,
    *,
    dx: Decimal,
    dy: Decimal,
    dx_raw: str,
    dy_raw: str,
) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        if not _safe_foreach_vars(match.group("vars")):
            return match.group(0)
        shifted_body, shifted_count = _shift_foreach_body(
            match.group("body"),
            dx=dx,
            dy=dy,
            dx_raw=dx_raw,
            dy_raw=dy_raw,
        )
        count += shifted_count
        return match.group(0).replace(match.group("body"), shifted_body, 1)

    return _FOREACH_RE.sub(replace, line), count


def _shift_literal_coordinates(
    line: str,
    *,
    dx: Decimal,
    dy: Decimal,
    dx_raw: str,
    dy_raw: str,
) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return (
            f"({_format_shifted(match.group('x'), dx, dx_raw)}, "
            f"{_format_shifted(match.group('y'), dy, dy_raw)})"
        )

    return _COORD_RE.sub(replace, line), count


def shift_tex_coordinates(
    tex: str,
    *,
    dx: str,
    dy: str,
    line_ranges: list[tuple[int, int]] | None,
) -> ShiftResult:
    dx_decimal = _decimal(dx, "dx")
    dy_decimal = _decimal(dy, "dy")
    if dx_decimal == 0 and dy_decimal == 0:
        raise TexCoordinateShiftError("dx and dy cannot both be zero")
    lines = tex.splitlines(keepends=True)
    changed_count = 0
    shifted_lines: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        if not _line_selected(line_number, line_ranges):
            shifted_lines.append(line)
            continue

        code, comment = _split_tex_comment(line)
        shifted, count = _shift_foreach_line(
            code,
            dx=dx_decimal,
            dy=dy_decimal,
            dx_raw=dx,
            dy_raw=dy,
        )
        changed_count += count
        shifted, count = _shift_literal_coordinates(
            shifted,
            dx=dx_decimal,
            dy=dy_decimal,
            dx_raw=dx,
            dy_raw=dy,
        )
        changed_count += count
        shifted_lines.append(shifted + comment)

    return ShiftResult("".join(shifted_lines), changed_count)


def _parse_line_range(raw: str) -> tuple[int, int]:
    start_raw, sep, end_raw = raw.partition(":")
    if not sep:
        raise TexCoordinateShiftError("--line must use START:END")
    try:
        start = int(start_raw)
        end = int(end_raw)
    except ValueError as exc:
        raise TexCoordinateShiftError("--line must contain integer line numbers") from exc
    if start < 1 or end < start:
        raise TexCoordinateShiftError("--line must satisfy 1 <= START <= END")
    return start, end


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tex_path", help="Path to the .tex file to shift")
    parser.add_argument("--dx", required=True, help="X shift in source TikZ units")
    parser.add_argument("--dy", required=True, help="Y shift in source TikZ units")
    parser.add_argument(
        "--line",
        action="append",
        default=[],
        help="1-based inclusive line range START:END; may be repeated",
    )
    parser.add_argument("--all", action="store_true", help="Shift the whole file intentionally")
    parser.add_argument("--write", action="store_true", help="Write shifted coordinates to file")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if bool(args.line) == bool(args.all):
        print("ERROR: provide --line or --all", file=sys.stderr)
        return 2

    try:
        line_ranges = None if args.all else [_parse_line_range(raw) for raw in args.line]
        tex_path = Path(args.tex_path)
        if tex_path.suffix != ".tex":
            raise TexCoordinateShiftError("tex_path must be a .tex file")
        if not tex_path.is_file():
            raise TexCoordinateShiftError(f"missing .tex file: {tex_path}")
        original = tex_path.read_text(encoding="utf-8")
        result = shift_tex_coordinates(
            original,
            dx=args.dx,
            dy=args.dy,
            line_ranges=line_ranges,
        )
    except TexCoordinateShiftError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if result.changed_count == 0:
        print("ERROR: no supported coordinates changed", file=sys.stderr)
        return 2

    if args.write:
        tex_path.write_text(result.text, encoding="utf-8")
        noun = "coordinate" if result.changed_count == 1 else "coordinates"
        print(f"wrote {result.changed_count} shifted {noun} to {tex_path}")
        return 0

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        result.text.splitlines(keepends=True),
        fromfile=str(tex_path),
        tofile=f"{tex_path} (shifted)",
    )
    print("".join(diff), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
