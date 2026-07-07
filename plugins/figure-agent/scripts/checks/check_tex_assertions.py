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
from hashlib import sha256
from pathlib import Path

import yaml

DEFAULT_TOLERANCE_CM = 0.05
AXES = ("x", "y")
DIRECTIONS = ("increasing", "decreasing")

_NUM = r"-?\d+(?:\.\d+)?"

# Option body allowing ONE level of `[...]` nesting (e.g. an inline arrow tip spec
# `-{Stealth[length=6pt,width=4.5pt]}`, whose inner `]` breaks a flat `[^\]]*`).
_OPT_BODY = r"(?:[^\[\]]*\[[^\]]*\])*[^\[\]]*"
_STYLED_DRAW_RE = re.compile(
    r"\\draw\s*\[(" + _OPT_BODY + r")\]\s*"
    rf"\(\s*({_NUM})\s*,\s*({_NUM})\s*\)\s*--\s*\(\s*({_NUM})\s*,\s*({_NUM})\s*\)"
)
_ALL_DRAW_RE = re.compile(
    r"\\draw\s*(?:\[(" + _OPT_BODY + r")\])?\s*"
    rf"\(\s*({_NUM})\s*,\s*({_NUM})\s*\)\s*--\s*\(\s*({_NUM})\s*,\s*({_NUM})\s*\)"
)


def _styled_draws_raw(tex_text: str, style: str) -> list[tuple[float, float, float, float, str]]:
    """Every `\\draw[…<style>…] (x1,y1) -- (x2,y2)` as (x1, y1, x2, y2, option_body).

    The style token is matched word-bounded inside the option body so `forceArr`
    does not match `forceArrow`; the option body carries the arrow-tip spec.
    """
    style_re = re.compile(r"\b" + re.escape(style) + r"\b")
    out: list[tuple[float, float, float, float, str]] = []
    for match in _STYLED_DRAW_RE.finditer(tex_text):
        options = match.group(1)
        if not style_re.search(options):
            continue
        out.append(
            (
                float(match.group(2)),
                float(match.group(3)),
                float(match.group(4)),
                float(match.group(5)),
                options,
            )
        )
    return out


def _all_draws_raw(tex_text: str) -> list[tuple[float, float, float, float, str]]:
    """Every straight `\\draw … (x1,y1) -- (x2,y2)` as (x1, y1, x2, y2, option_body)."""
    return [
        (
            float(match.group(2)),
            float(match.group(3)),
            float(match.group(4)),
            float(match.group(5)),
            match.group(1) or "",
        )
        for match in _ALL_DRAW_RE.finditer(tex_text)
    ]


def find_styled_draws(tex_text: str, style: str) -> list[tuple[float, float, float, float]]:
    """Coordinates of every `\\draw[…<style>…] (x1,y1) -- (x2,y2)` in the source."""
    return [raw[:4] for raw in _styled_draws_raw(tex_text, style)]


def find_all_draws(tex_text: str) -> list[tuple[float, float, float, float]]:
    """Coordinates of every straight `\\draw … (x1,y1) -- (x2,y2)` regardless of
    style. Bezier `.. controls ..` segments are not matched."""
    return [raw[:4] for raw in _all_draws_raw(tex_text)]


def _tip_orientation(option_body: str) -> str:
    """'forward' (head at end) | 'reverse' (head at start) | 'both' | 'none'.

    Reads the arrow-spec option so a reversed arrowhead is not judged on coordinate
    order alone. `{...}` tip groups are masked to a single token first so an inner
    comma/bracket does not split the option list.
    """
    masked = re.sub(r"\{(?:[^{}]|\{[^{}]*\})*\}", "T", option_body)
    for option in masked.split(","):
        arrow = re.fullmatch(r"([<>|T]?)-([<>|T]?)", option.strip())
        if not arrow:
            continue
        start_tip, end_tip = bool(arrow.group(1)), bool(arrow.group(2))
        if start_tip and end_tip:
            return "both"
        if start_tip:
            return "reverse"
        if end_tip:
            return "forward"
        return "none"
    return "none"


def check_direction(
    coords: tuple[float, float, float, float],
    *,
    axis: str,
    direction: str,
    tip: str = "forward",
    tol: float = DEFAULT_TOLERANCE_CM,
) -> str:
    """'pass' | 'violated' | 'indeterminate' for a draw's PHYSICAL direction.

    Physical direction is the way the arrowHEAD points, not coordinate order: a
    `{Stealth}-` (head at start) arrow points opposite its (x1,y1)->(x2,y2) order,
    so `tip='reverse'` flips the delta. 'both'/'none' fall back to coordinate order.
    """
    x1, y1, x2, y2 = coords
    delta = (x2 - x1) if axis == "x" else (y2 - y1)
    if tip == "reverse":
        delta = -delta
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
        for field in ("id", "axis", "direction"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise TexAssertionError(f"tex_assertions[{index}].{field} is required")
            out[field] = value.strip()
        anchor_style = item.get("anchor_style")
        if anchor_style is not None:
            if not isinstance(anchor_style, str) or not anchor_style.strip():
                raise TexAssertionError(f"tex_assertions[{index}].anchor_style must be a string")
            out["anchor_style"] = anchor_style.strip()
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
        if "anchor_style" not in out and "near" not in out:
            raise TexAssertionError(
                f"tex_assertions[{index}] requires anchor_style or near to locate the draw"
            )
        parsed.append(out)
    return parsed


def check_tex_assertions(tex_text: str, assertions: list[dict]) -> list[dict]:
    """One issue per assertion that is violated, indeterminate, or whose anchor is
    missing/ambiguous. A passing assertion produces no issue."""
    issues: list[dict] = []
    for assertion in assertions:
        style = assertion.get("anchor_style")
        draws = _styled_draws_raw(tex_text, style) if style else _all_draws_raw(tex_text)
        anchor = repr(style) if style else "any draw near the declared point"
        status, selected = select_draw(draws, assertion.get("near"))
        if status == "missing":
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "anchor_missing",
                    "message": f"assertion {assertion['id']!r}: no draw matched ({anchor})",
                }
            )
            continue
        if status == "ambiguous":
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "anchor_ambiguous",
                    "message": (
                        f"assertion {assertion['id']!r}: {anchor} matches {len(draws)} draws "
                        "(add or tighten `near` to disambiguate)"
                    ),
                }
            )
            continue
        result = check_direction(
            selected[:4],
            axis=assertion["axis"],
            direction=assertion["direction"],
            tip=_tip_orientation(selected[4]),
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


# Statuses that should BLOCK export: a violated assertion is wrong physics; a
# missing/ambiguous anchor means an authored assertion is unverified. 'indeterminate'
# (within tolerance) is advisory, not blocking.
BLOCKING_STATUSES = ("violated", "anchor_missing", "anchor_ambiguous")


def _gate_failure_issue(status: str, json_path, *, detail: str | None = None) -> dict:
    message = f"tex_assertions evidence {status} at {json_path}"
    if detail:
        message += f": {detail}"
    return {"id": "tex-assertions-evidence", "status": status, "message": message}


def read_blocking_issues(json_path) -> list[dict]:
    """Blocking issues from a build/tex_assertions.json.

    Missing, unreadable, or schema-invalid evidence cannot be treated as "no
    issues" — a gate that trusts an absent/corrupt artifact fails open on the
    exact reversed-arrow physics this checker exists to catch. Callers must
    treat any non-empty result as blocking.
    """
    try:
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [_gate_failure_issue("artifact_missing", json_path)]
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [_gate_failure_issue("artifact_unreadable", json_path, detail=str(exc))]
    issues = data.get("issues")
    if not isinstance(issues, list):
        return [_gate_failure_issue("artifact_schema_invalid", json_path)]
    return [
        issue
        for issue in issues
        if isinstance(issue, dict) and issue.get("status") in BLOCKING_STATUSES
    ]


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def tex_assertions_payload(tex_path, issues: list[dict], assertion_count: int) -> dict:
    tex_path = Path(tex_path)
    return {
        "schema": SCHEMA,
        "source_tex": tex_path.name,
        "source_hashes": {
            f"examples/{tex_path.stem}/{tex_path.name}": _file_sha256(tex_path),
        },
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
