#!/usr/bin/env python3
r"""Deterministic tex-geometry assertion check (report-only WARN).

Directional physics facts — a force arrow points AWAY from the drive electrode, a
cantilever bends opposite under +V vs -V — live in DRAWN elements, not in text
labels, so the render-based detectors and the label-relational semantic_assertions
cannot catch a reversed one (a dogfood probe confirmed the natural label assertion
passes for BOTH a correct and a reversed figure). The robust source for these facts
is the figure's own TikZ source: this checker reads coordinates straight from the
`.tex` (no render, no pdftotext) and verifies the declared direction.

spec.yaml::

    tex_assertions:
      - id: force-repels-not-attracts
        anchor_style: forceArr     # tikz style naming the \draw to locate
        axis: x                    # x | y
        direction: decreasing      # increasing | decreasing

The physics MEANING (decreasing-x = away-from-the-right-electrode = repulsion) is the
author's interpretation, baked into the declared `direction`; the checker is purely
mechanical. Report-only by default; --strict exits non-zero on any violation.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

DEFAULT_TOLERANCE_CM = 0.05
AXES = ("x", "y")
DIRECTIONS = ("increasing", "decreasing")

_NUM = r"-?\d+(?:\.\d+)?"


def find_styled_draws(tex_text: str, style: str) -> list[tuple[float, float, float, float]]:
    """Coordinates of every `\\draw[…<style>…] (x1,y1) -- (x2,y2)` in the source.

    The style token is matched word-bounded inside the option brackets so
    `forceArr` does not match `forceArrow`."""
    pattern = re.compile(
        r"\\draw\s*\[[^\]]*\b" + re.escape(style) + r"\b[^\]]*\]\s*"
        rf"\(\s*({_NUM})\s*,\s*({_NUM})\s*\)\s*--\s*\(\s*({_NUM})\s*,\s*({_NUM})\s*\)"
    )
    return [
        (float(x1), float(y1), float(x2), float(y2)) for x1, y1, x2, y2 in pattern.findall(tex_text)
    ]


def check_direction(
    coords: tuple[float, float, float, float],
    *,
    axis: str,
    direction: str,
    tol: float = DEFAULT_TOLERANCE_CM,
) -> str:
    """'pass' | 'violated' | 'indeterminate' for a draw's endpoint direction."""
    x1, y1, x2, y2 = coords
    delta = (x2 - x1) if axis == "x" else (y2 - y1)
    if abs(delta) <= tol:
        return "indeterminate"
    holds = delta > 0 if direction == "increasing" else delta < 0
    return "pass" if holds else "violated"


NEAR_TOLERANCE_CM = 0.5


def select_draw(draws, near, *, tol: float = NEAR_TOLERANCE_CM):
    """Pick one draw from same-style matches. With no `near`, require exactly one
    (else ambiguous). With `near=[x,y]`, pick the one whose START coordinate is
    within `tol` of it. Returns ('ok', coords) | ('missing', None) | ('ambiguous', None)."""
    if not draws:
        return ("missing", None)
    if near is None:
        return ("ok", draws[0]) if len(draws) == 1 else ("ambiguous", None)
    near_x, near_y = near
    within = [d for d in draws if abs(d[0] - near_x) <= tol and abs(d[1] - near_y) <= tol]
    if not within:
        return ("missing", None)
    if len(within) > 1:
        return ("ambiguous", None)
    return ("ok", within[0])


SCHEMA = "figure-agent.tex-assertions.v1"


class TexAssertionError(ValueError):
    """Raised when declared tex_assertions are malformed."""


def parse_tex_assertions(spec: dict) -> list[dict]:
    raw = spec.get("tex_assertions")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise TexAssertionError("tex_assertions must be a list")
    parsed: list[dict] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise TexAssertionError(f"tex_assertions[{index}] must be a mapping")
        out: dict = {}
        for field in ("id", "anchor_style", "axis", "direction"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise TexAssertionError(f"tex_assertions[{index}].{field} is required")
            out[field] = value.strip()
        if out["axis"] not in AXES:
            raise TexAssertionError(f"tex_assertions[{index}].axis must be one of {AXES}")
        if out["direction"] not in DIRECTIONS:
            raise TexAssertionError(
                f"tex_assertions[{index}].direction must be one of {DIRECTIONS}"
            )
        if "tolerance_cm" in item:
            tol = item["tolerance_cm"]
            if isinstance(tol, bool) or not isinstance(tol, (int, float)) or tol <= 0:
                raise TexAssertionError(f"tex_assertions[{index}].tolerance_cm must be > 0")
            out["tolerance_cm"] = float(tol)
        if "near" in item:
            near = item["near"]
            if (
                not isinstance(near, list)
                or len(near) != 2
                or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in near)
            ):
                raise TexAssertionError(f"tex_assertions[{index}].near must be [x, y] numbers")
            out["near"] = [float(near[0]), float(near[1])]
        parsed.append(out)
    return parsed


def check_tex_assertions(tex_text: str, assertions: list[dict]) -> list[dict]:
    """One issue per assertion that is violated, indeterminate, or whose anchor is
    missing/ambiguous. A passing assertion produces no issue."""
    issues: list[dict] = []
    for assertion in assertions:
        draws = find_styled_draws(tex_text, assertion["anchor_style"])
        status, coords = select_draw(draws, assertion.get("near"))
        if status == "missing":
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "anchor_missing",
                    "message": (
                        f"assertion {assertion['id']!r}: no draw with style "
                        f"{assertion['anchor_style']!r}"
                        + (" near the declared point" if assertion.get("near") else "")
                    ),
                }
            )
            continue
        if status == "ambiguous":
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "anchor_ambiguous",
                    "message": (
                        f"assertion {assertion['id']!r}: style "
                        f"{assertion['anchor_style']!r} matches {len(draws)} draws "
                        "(add `near` to disambiguate)"
                    ),
                }
            )
            continue
        result = check_direction(
            coords,
            axis=assertion["axis"],
            direction=assertion["direction"],
            tol=assertion.get("tolerance_cm", DEFAULT_TOLERANCE_CM),
        )
        if result == "pass":
            continue
        issues.append(
            {
                "id": assertion["id"],
                "status": result,
                "message": (
                    f"assertion {assertion['id']!r} {result}: {assertion['anchor_style']!r} "
                    f"is not {assertion['direction']} on {assertion['axis']}"
                ),
            }
        )
    return issues


def tex_assertions_payload(tex_path, issues: list[dict], assertion_count: int) -> dict:
    return {
        "schema": SCHEMA,
        "source_tex": tex_path.name,
        "checked": assertion_count,
        "issues": issues,
        "total": len(issues),
    }


def write_tex_assertions_json(tex_path, issues, count, output_path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(tex_assertions_payload(tex_path, issues, count), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic tex-geometry assertion check")
    parser.add_argument("tex", type=Path, help="figure .tex source")
    parser.add_argument("--spec", type=Path, help="spec.yaml (default: tex's sibling spec.yaml)")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--strict", action="store_true", default=False)
    args = parser.parse_args()

    spec_path = args.spec or args.tex.parent / "spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) if spec_path.exists() else {}
    assertions = parse_tex_assertions(spec or {})
    tex_text = args.tex.read_text(encoding="utf-8")
    issues = check_tex_assertions(tex_text, assertions)

    if args.json_output:
        write_tex_assertions_json(args.tex, issues, len(assertions), args.json_output)
    print(f"tex assertions: {args.tex.name} ({len(assertions)} checked)")
    for issue in issues:
        print(f"WARN {issue['status']}: {issue['message']}")
    if not issues:
        print("OK: no tex-geometry assertion issues")
    violated = any(
        i["status"] in ("violated", "anchor_missing", "anchor_ambiguous") for i in issues
    )
    return 1 if (args.strict and violated) else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
