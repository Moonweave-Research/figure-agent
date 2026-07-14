#!/usr/bin/env python3
r"""Deterministic TeX geometry assertion check (report-only WARN).

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
_STYLED_TO_RE = re.compile(
    r"\\draw\s*\[(" + _OPT_BODY + r")\]\s*"
    rf"\(\s*({_NUM})\s*,\s*({_NUM})\s*\)\s*to(?:\s*\[("
    + _OPT_BODY
    + rf")\])?\s*\(\s*({_NUM})\s*,\s*({_NUM})\s*\)"
)
_ALL_TO_RE = re.compile(
    r"\\draw\s*(?:\[(" + _OPT_BODY + r")\])?\s*"
    rf"\(\s*({_NUM})\s*,\s*({_NUM})\s*\)\s*to(?:\s*\[("
    + _OPT_BODY
    + rf")\])?\s*\(\s*({_NUM})\s*,\s*({_NUM})\s*\)"
)
_NAMED_COORD = r"[A-Za-z][A-Za-z0-9_-]*"
_STYLED_NAMED_TO_RE = re.compile(
    r"\\draw\s*\[(" + _OPT_BODY + r")\]\s*"
    rf"\(\s*({_NAMED_COORD})\s*\)\s*to(?:\s*\["
    + _OPT_BODY
    + rf"\])?\s*\(\s*({_NAMED_COORD})\s*\)"
)
_NAMED_COORD_DECL_RE = re.compile(
    r"\\(?:coordinate|node)(?:\s*\[[^\]]*\])?\s*"
    rf"\(\s*({_NAMED_COORD})\s*\)\s*at\s*\(\s*({_NUM})\s*,\s*({_NUM})\s*\)"
)

_RAW_DRAW_PATTERN = tuple[re.Pattern[str], tuple[int, int, int, int], int | None]


def _option_tokens(option_body: str) -> list[str]:
    """Split TikZ options only at top-level commas."""
    tokens: list[str] = []
    start = brace_depth = bracket_depth = 0
    for index, char in enumerate(option_body):
        if char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth -= 1
        elif char == "," and brace_depth == bracket_depth == 0:
            tokens.append(option_body[start:index].strip())
            start = index + 1
    tokens.append(option_body[start:].strip())
    return [token for token in tokens if token]


def _has_style_token(option_body: str, style: str) -> bool:
    """Require an exact bare style token, never a word-boundary substring."""
    return style in _option_tokens(option_body)


def _strip_tex_comments(tex_text: str) -> str:
    """Remove unescaped TeX comments while preserving line boundaries.

    A commented-out ``\\draw`` is not rendered and must not satisfy a source
    contract. An escaped ``\\%`` remains ordinary TeX content; an even number of
    preceding backslashes leaves ``%`` unescaped and starts a comment.
    """
    stripped_lines: list[str] = []
    for line in tex_text.splitlines(keepends=True):
        for index, char in enumerate(line):
            if char != "%":
                continue
            preceding_slashes = 0
            for before in reversed(line[:index]):
                if before != "\\":
                    break
                preceding_slashes += 1
            if preceding_slashes % 2:
                continue
            line_ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
            stripped_lines.append(line[:index] + line_ending)
            break
        else:
            stripped_lines.append(line)
    return "".join(stripped_lines)


def _match_raw_draws(
    tex_text: str,
    patterns: tuple[_RAW_DRAW_PATTERN, ...],
    *,
    style: str | None = None,
) -> list[tuple[float, float, float, float, str]]:
    tex_text = _strip_tex_comments(tex_text)
    matches: list[tuple[int, tuple[float, float, float, float, str]]] = []
    for pattern, coordinate_groups, to_options_group in patterns:
        for match in pattern.finditer(tex_text):
            draw_options = match.group(1) or ""
            if style is not None and not _has_style_token(draw_options, style):
                continue
            to_options = match.group(to_options_group) if to_options_group else None
            options = ",".join(option for option in (draw_options, to_options) if option)
            matches.append(
                (
                    match.start(),
                    (
                        *(float(match.group(group)) for group in coordinate_groups),
                        options,
                    ),
                )
            )
    return [raw for _, raw in sorted(matches, key=lambda item: item[0])]


def _styled_draws_raw(tex_text: str, style: str) -> list[tuple[float, float, float, float, str]]:
    """Every styled straight or `to[...]` draw as (x1, y1, x2, y2, option_body).

    The style token is exact inside the comma-delimited option body, so
    `xfer-helper` cannot satisfy an `xfer` assertion.
    """
    literal_paths = _match_raw_draws(
        tex_text,
        ((_STYLED_DRAW_RE, (2, 3, 4, 5), None), (_STYLED_TO_RE, (2, 3, 5, 6), 4)),
        style=style,
    )
    stripped = _strip_tex_comments(tex_text)
    coordinates = {
        match.group(1): (float(match.group(2)), float(match.group(3)))
        for match in _NAMED_COORD_DECL_RE.finditer(stripped)
    }
    named_paths: list[tuple[float, float, float, float, str]] = []
    for match in _STYLED_NAMED_TO_RE.finditer(stripped):
        if not _has_style_token(match.group(1), style):
            continue
        start = coordinates.get(match.group(2))
        end = coordinates.get(match.group(3))
        if start is not None and end is not None:
            named_paths.append((*start, *end, match.group(1)))
    return literal_paths + named_paths


def _all_draws_raw(tex_text: str) -> list[tuple[float, float, float, float, str]]:
    """Every straight or `to[...]` draw as (x1, y1, x2, y2, option_body)."""
    return _match_raw_draws(
        tex_text,
        ((_ALL_DRAW_RE, (2, 3, 4, 5), None), (_ALL_TO_RE, (2, 3, 5, 6), 4)),
    )


def find_styled_draws(tex_text: str, style: str) -> list[tuple[float, float, float, float]]:
    """Coordinates of every styled straight or `to[...]` draw in the source."""
    return [raw[:4] for raw in _styled_draws_raw(tex_text, style)]


def find_all_draws(tex_text: str) -> list[tuple[float, float, float, float]]:
    """Coordinates of every straight or `to[...]` draw, excluding Bezier controls."""
    return [raw[:4] for raw in _all_draws_raw(tex_text)]


def find_styled_named_to_paths(tex_text: str, style: str) -> list[tuple[str, str]]:
    """Named TikZ endpoints for ``style``-tagged curved paths.

    A source relation is robust only when the path ends at the named visual state
    it claims to enter or leave. Literal coordinates cannot provide that binding:
    moving a trap tick and forgetting an adjacent arrow would otherwise remain a
    silent semantic defect.
    """
    paths: list[tuple[str, str]] = []
    for match in _STYLED_NAMED_TO_RE.finditer(_strip_tex_comments(tex_text)):
        if _has_style_token(match.group(1), style):
            paths.append((match.group(2), match.group(3)))
    return paths


def _tip_orientation(option_body: str) -> str:
    """'forward' (head at end) | 'reverse' (head at start) | 'both' | 'none'.

    Reads the arrow-spec option so a reversed arrowhead is not judged on coordinate
    order alone. `{...}` tip groups are masked to a single token first so an inner
    comma/bracket does not split the option list.
    """
    masked = re.sub(r"\{(?:[^{}]|\{[^{}]*\})*\}", "T", option_body)
    for option in _option_tokens(masked):
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


def _style_tip(tex_text: str, style: str) -> str:
    """Resolve an arrowhead declared by a named TikZ style when unambiguous."""
    pattern = re.compile(
        rf"{re.escape(style)}/\.style\s*=\s*\{{((?:[^{{}}]|\{{[^{{}}]*\}})*)\}}"
    )
    matches = pattern.findall(_strip_tex_comments(tex_text))
    tips = {_tip_orientation(body) for body in matches}
    return tips.pop() if len(tips) == 1 else "none"


def _resolved_tip(tex_text: str, option_body: str) -> str:
    direct = _tip_orientation(option_body)
    if direct != "none":
        return direct
    style_tips = {_style_tip(tex_text, token) for token in _option_tokens(option_body)}
    style_tips.discard("none")
    return style_tips.pop() if len(style_tips) == 1 else "none"


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


def parse_tex_assertions(
    spec: dict,
    *,
    source_name: str | None = None,
) -> list[dict]:
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
        assertion_source_name = item.get("source_name")
        if assertion_source_name is not None:
            if not isinstance(assertion_source_name, str) or not assertion_source_name.strip():
                raise TexAssertionError(f"tex_assertions[{index}].source_name must be a string")
            out["source_name"] = assertion_source_name.strip()
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
        if "minimum_matches" in item:
            minimum_matches = item["minimum_matches"]
            if (
                isinstance(minimum_matches, bool)
                or not isinstance(minimum_matches, int)
                or minimum_matches < 1
            ):
                raise TexAssertionError(
                    f"tex_assertions[{index}].minimum_matches must be a positive integer"
                )
            if "near" in out:
                raise TexAssertionError(
                    f"tex_assertions[{index}].minimum_matches cannot be combined with near"
                )
            out["minimum_matches"] = minimum_matches
        require_arrow = item.get("require_unidirectional_arrow", False)
        if not isinstance(require_arrow, bool):
            raise TexAssertionError(
                f"tex_assertions[{index}].require_unidirectional_arrow must be boolean"
            )
        if require_arrow:
            out["require_unidirectional_arrow"] = True
        if "anchor_style" not in out and "near" not in out:
            raise TexAssertionError(
                f"tex_assertions[{index}] requires anchor_style or near to locate the draw"
            )
        if source_name is not None and out.get("source_name") not in (None, source_name):
            continue
        parsed.append(out)
    return parsed


def parse_named_endpoint_assertions(
    spec: dict,
    *,
    source_name: str | None = None,
) -> list[dict]:
    """Parse source-level bindings between semantic paths and named TikZ states."""
    raw = spec.get("named_endpoint_assertions")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise TexAssertionError("named_endpoint_assertions must be a list")
    parsed: list[dict] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise TexAssertionError(
                f"named_endpoint_assertions[{index}] must be a mapping"
            )
        out: dict = {}
        for field in ("id", "anchor_style"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise TexAssertionError(
                    f"named_endpoint_assertions[{index}].{field} is required"
                )
            out[field] = value.strip()
        for field in ("required_anchors", "allowed_anchors"):
            anchors = item.get(field)
            if (
                not isinstance(anchors, list)
                or not anchors
                or any(not isinstance(anchor, str) or not anchor.strip() for anchor in anchors)
            ):
                raise TexAssertionError(
                    f"named_endpoint_assertions[{index}].{field} must be a non-empty string list"
                )
            out[field] = [anchor.strip() for anchor in anchors]
        if not set(out["required_anchors"]).issubset(out["allowed_anchors"]):
            raise TexAssertionError(
                f"named_endpoint_assertions[{index}].required_anchors must be allowed"
            )
        minimum_paths = item.get("minimum_paths")
        if (
            isinstance(minimum_paths, bool)
            or not isinstance(minimum_paths, int)
            or minimum_paths < 1
        ):
            raise TexAssertionError(
                f"named_endpoint_assertions[{index}].minimum_paths must be a positive integer"
            )
        out["minimum_paths"] = minimum_paths
        assertion_source_name = item.get("source_name")
        if assertion_source_name is not None:
            if not isinstance(assertion_source_name, str) or not assertion_source_name.strip():
                raise TexAssertionError(
                    f"named_endpoint_assertions[{index}].source_name must be a string"
                )
            out["source_name"] = assertion_source_name.strip()
        if source_name is not None and out.get("source_name") not in (None, source_name):
            continue
        parsed.append(out)
    return parsed


def check_named_endpoint_assertions(tex_text: str, assertions: list[dict]) -> list[dict]:
    """Return blocking issues when semantic paths detach from declared named states."""
    issues: list[dict] = []
    for assertion in assertions:
        paths = find_styled_named_to_paths(tex_text, assertion["anchor_style"])
        if len(paths) < assertion["minimum_paths"]:
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "insufficient_named_paths",
                    "message": (
                        f"assertion {assertion['id']!r}: {assertion['anchor_style']!r} has "
                        f"{len(paths)} named paths; requires at least {assertion['minimum_paths']}"
                    ),
                }
            )
            continue
        allowed = set(assertion["allowed_anchors"])
        unexpected = sorted(
            {anchor for path in paths for anchor in path if anchor not in allowed}
        )
        if unexpected:
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "named_endpoint_unbound",
                    "message": (
                        f"assertion {assertion['id']!r}: unexpected named endpoints "
                        f"{', '.join(unexpected)}"
                    ),
                }
            )
            continue
        observed = {anchor for path in paths for anchor in path}
        missing = sorted(set(assertion["required_anchors"]) - observed)
        if missing:
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "named_endpoint_missing",
                    "message": (
                        f"assertion {assertion['id']!r}: required named endpoints absent "
                        f"{', '.join(missing)}"
                    ),
                }
            )
    return issues


def check_tex_assertions(tex_text: str, assertions: list[dict]) -> list[dict]:
    """One issue per assertion that is violated, indeterminate, or whose anchor is
    missing/ambiguous. A passing assertion produces no issue."""
    issues: list[dict] = []
    for assertion in assertions:
        style = assertion.get("anchor_style")
        draws = _styled_draws_raw(tex_text, style) if style else _all_draws_raw(tex_text)
        anchor = repr(style) if style else "any draw near the declared point"
        minimum_matches = assertion.get("minimum_matches")
        require_arrow = assertion.get("require_unidirectional_arrow", False)
        def direction_holds(draw: tuple[float, float, float, float, str]) -> bool:
            tip = _resolved_tip(tex_text, draw[4])
            return tip in {"forward", "reverse"} and check_direction(
                draw[:4], axis=assertion["axis"], direction=assertion["direction"], tip=tip,
                tol=assertion.get("tolerance_cm", DEFAULT_TOLERANCE_CM),
            ) == "pass" if require_arrow else check_direction(
                draw[:4], axis=assertion["axis"], direction=assertion["direction"], tip=tip,
                tol=assertion.get("tolerance_cm", DEFAULT_TOLERANCE_CM),
            ) == "pass"
        if minimum_matches is not None:
            if len(draws) < minimum_matches:
                issues.append(
                    {
                        "id": assertion["id"],
                        "status": "insufficient_matches",
                        "message": (
                            f"assertion {assertion['id']!r}: {anchor} matches {len(draws)} draws; "
                            f"requires at least {minimum_matches}"
                        ),
                    }
                )
                continue
            matching_count = sum(
                1
                for draw in draws
                if direction_holds(draw)
            )
            if matching_count >= minimum_matches:
                continue
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "insufficient_matches",
                    "message": (
                        f"assertion {assertion['id']!r}: {anchor} has {matching_count} "
                        f"{assertion['direction']} matches on {assertion['axis']}; requires "
                        f"at least {minimum_matches}"
                    ),
                }
            )
            continue
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
        tip = _resolved_tip(tex_text, selected[4])
        if require_arrow and tip not in {"forward", "reverse"}:
            issues.append({"id": assertion["id"], "status": "arrowhead_invalid", "message": (
                f"assertion {assertion['id']!r}: {anchor} has {tip} arrowhead"
            )})
            continue
        result = check_direction(
            selected[:4],
            axis=assertion["axis"],
            direction=assertion["direction"],
            tip=tip,
            tol=assertion.get("tolerance_cm", DEFAULT_TOLERANCE_CM),
        )
        if result == "pass":
            continue
        issues.append(
            {
                "id": assertion["id"],
                "status": result,
                "message": (
                    f"assertion {assertion['id']!r} {result}: {anchor} "
                    f"is not {assertion['direction']} on {assertion['axis']}"
                ),
            }
        )
    return issues


# Statuses that should BLOCK export: a violated assertion is wrong physics; a
# missing/ambiguous anchor means an authored assertion is unverified. 'indeterminate'
# (within tolerance) is advisory, not blocking.
BLOCKING_STATUSES = (
    "violated", "anchor_missing", "anchor_ambiguous", "insufficient_matches", "arrowhead_invalid",
    "insufficient_named_paths", "named_endpoint_unbound", "named_endpoint_missing",
)


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
    assertions = parse_tex_assertions(spec or {}, source_name=args.tex.name)
    named_endpoint_assertions = parse_named_endpoint_assertions(
        spec or {}, source_name=args.tex.name
    )
    tex_text = args.tex.read_text(encoding="utf-8")
    issues = check_tex_assertions(tex_text, assertions) + check_named_endpoint_assertions(
        tex_text, named_endpoint_assertions
    )
    assertion_count = len(assertions) + len(named_endpoint_assertions)

    if args.json_output:
        write_tex_assertions_json(args.tex, issues, assertion_count, args.json_output)
    print(f"tex assertions: {args.tex.name} ({assertion_count} checked)")
    for issue in issues:
        print(f"WARN {issue['status']}: {issue['message']}")
    if not issues:
        print("OK: no tex-geometry assertion issues")
    violated = any(i["status"] in BLOCKING_STATUSES for i in issues)
    return 1 if (args.strict and violated) else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
