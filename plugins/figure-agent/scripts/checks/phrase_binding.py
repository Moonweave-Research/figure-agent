#!/usr/bin/env python3
"""Bind declared text to rendered PDF words: phrases in reading order, allowlists by word.

Both declared-geometry detectors resolve a phrase the same way, so the
grouping rule and the unmatched-declaration findings live here.  A declaration
that binds nothing measures nothing: it is broken, not clean.
"""

from __future__ import annotations

from typing import Any

PHRASE_UNMATCHED = "phrase_unmatched"
ALLOWLIST_UNMATCHED = "allowlist_unmatched"
NEAREST_WORD_LIMIT = 4


def _text(word: dict[str, Any]) -> str:
    return str(word.get("text", "")).strip()


def _bbox(word: dict[str, Any]) -> tuple[float, float, float, float]:
    return (
        round(float(word["xmin"]), 6),
        round(float(word["ymin"]), 6),
        round(float(word["xmax"]), 6),
        round(float(word["ymax"]), 6),
    )


def _reading_key(word: dict[str, Any]) -> tuple[float, float, float, float, str]:
    return (
        float(word["ymin"]),
        float(word["xmin"]),
        float(word["ymax"]),
        float(word["xmax"]),
        str(word.get("text", "")),
    )


def _center_y(word: dict[str, Any]) -> float:
    return (float(word["ymin"]) + float(word["ymax"])) / 2.0


def _overlaps(a_min: float, a_max: float, b_min: float, b_max: float) -> bool:
    return max(a_min, b_min) <= min(a_max, b_max)


def same_phrase_line(
    left: dict[str, Any],
    right: dict[str, Any],
    max_center_delta: float,
) -> bool:
    return (
        _overlaps(
            float(left["ymin"]),
            float(left["ymax"]),
            float(right["ymin"]),
            float(right["ymax"]),
        )
        or abs(_center_y(left) - _center_y(right)) <= max_center_delta
    )


def _continuation_cost(
    span: list[dict[str, Any]],
    candidate: dict[str, Any],
    *,
    max_gap: float,
    max_center_delta: float,
) -> tuple[int, float] | None:
    """Rank a word as the next word of a phrase, or reject it.

    Same-line continuation keeps the original left-to-right contract.  A word
    that opens the next line of a multi-line node continues the span below it:
    the vertical step may not exceed one word height, and the word must stay
    within the span's horizontal extent.  Neither rule depends on the global
    top-edge order, so a subscript or a second node line still binds.
    """
    previous = span[-1]
    if same_phrase_line(previous, candidate, max_center_delta):
        gap = float(candidate["xmin"]) - float(previous["xmax"])
        if 0.0 <= gap <= max_gap:
            return (0, round(gap, 6))
    step = float(candidate["ymin"]) - float(previous["ymax"])
    if step < 0.0:
        return None
    line_height = max(
        float(previous["ymax"]) - float(previous["ymin"]),
        float(candidate["ymax"]) - float(candidate["ymin"]),
    )
    if step > line_height:
        return None
    span_xmin = min(float(word["xmin"]) for word in span)
    span_xmax = max(float(word["xmax"]) for word in span)
    if not _overlaps(
        float(candidate["xmin"]),
        float(candidate["xmax"]),
        span_xmin - max_gap,
        span_xmax + max_gap,
    ):
        return None
    return (1, round(step, 6))


def _next_phrase_word(
    ordered: list[dict[str, Any]],
    used: set[int],
    span: list[dict[str, Any]],
    expected_text: str,
    *,
    max_gap: float,
    max_center_delta: float,
) -> tuple[int, dict[str, Any]] | None:
    best: tuple[tuple[Any, ...], int, dict[str, Any]] | None = None
    for index, candidate in enumerate(ordered):
        if index in used or _text(candidate) != expected_text:
            continue
        cost = _continuation_cost(
            span,
            candidate,
            max_gap=max_gap,
            max_center_delta=max_center_delta,
        )
        if cost is None:
            continue
        key = (cost[0], cost[1], _reading_key(candidate), index)
        if best is None or key < best[0]:
            best = (key, index, candidate)
    if best is None:
        return None
    return best[1], best[2]


def _longest_span(
    ordered: list[dict[str, Any]],
    phrase_words: list[str],
    start_index: int,
    *,
    max_gap: float,
    max_center_delta: float,
) -> list[dict[str, Any]]:
    span = [ordered[start_index]]
    used = {start_index}
    for expected_text in phrase_words[1:]:
        found = _next_phrase_word(
            ordered,
            used,
            span,
            expected_text,
            max_gap=max_gap,
            max_center_delta=max_center_delta,
        )
        if found is None:
            break
        index, word = found
        used.add(index)
        span.append(word)
    return span


def phrase_span_word(
    span: list[dict[str, Any]],
    *,
    phrase_id: str,
    phrase_words: list[str],
) -> dict[str, Any]:
    return {
        "text": " ".join(phrase_words),
        "phrase_id": phrase_id,
        "words": phrase_words,
        "text_source": "text_phrases",
        "xmin": min(float(word["xmin"]) for word in span),
        "ymin": min(float(word["ymin"]) for word in span),
        "xmax": max(float(word["xmax"]) for word in span),
        "ymax": max(float(word["ymax"]) for word in span),
    }


def group_phrase_words(
    words: list[dict[str, Any]],
    phrase: dict[str, Any],
    *,
    max_gap: float,
    max_center_delta: float,
) -> list[dict[str, Any]]:
    """Return one synthetic word per rendered occurrence of the phrase."""
    ordered = sorted(words, key=_reading_key)
    phrase_words = list(phrase["words"])
    matches: list[dict[str, Any]] = []
    seen_spans: set[tuple[tuple[float, float, float, float], ...]] = set()
    for start_index, first_word in enumerate(ordered):
        if _text(first_word) != phrase_words[0]:
            continue
        span = _longest_span(
            ordered,
            phrase_words,
            start_index,
            max_gap=max_gap,
            max_center_delta=max_center_delta,
        )
        if len(span) != len(phrase_words):
            continue
        span_key = tuple(_bbox(word) for word in span)
        if span_key in seen_spans:
            continue
        seen_spans.add(span_key)
        matches.append(
            phrase_span_word(
                span,
                phrase_id=str(phrase["id"]),
                phrase_words=list(phrase_words),
            )
        )
    return matches


def nearest_phrase_words(
    words: list[dict[str, Any]],
    phrase: dict[str, Any],
    *,
    max_gap: float,
    max_center_delta: float,
    limit: int = NEAREST_WORD_LIMIT,
) -> list[str]:
    """Report the rendered words around the longest prefix the phrase reaches.

    An unmatched declaration is only actionable with the render's own words
    next to it: an empty list means the phrase's first word is not drawn at
    all, and a partial list names what the figure says instead.
    """
    ordered = sorted(words, key=_reading_key)
    phrase_words = list(phrase["words"])
    best_span: list[dict[str, Any]] = []
    for start_index, first_word in enumerate(ordered):
        if _text(first_word) != phrase_words[0]:
            continue
        span = _longest_span(
            ordered,
            phrase_words,
            start_index,
            max_gap=max_gap,
            max_center_delta=max_center_delta,
        )
        if len(span) > len(best_span):
            best_span = span
    if not best_span:
        return []
    continuations: list[tuple[tuple[int, float], tuple[Any, ...], str]] = []
    for candidate in ordered:
        if any(candidate is word for word in best_span):
            continue
        cost = _continuation_cost(
            best_span,
            candidate,
            max_gap=max_gap,
            max_center_delta=max_center_delta,
        )
        if cost is None:
            continue
        continuations.append((cost, _reading_key(candidate), _text(candidate)))
    continuations.sort()
    nearest = [_text(word) for word in best_span]
    nearest.extend(text for _, _, text in continuations[: max(0, limit - len(nearest))])
    return nearest


def phrase_unmatched_failure(
    check_id: str,
    phrase: dict[str, Any],
    nearest_words: list[str],
) -> dict[str, Any]:
    declared = " ".join(phrase["words"])
    rendered = ", ".join(nearest_words) if nearest_words else "none"
    return {
        "check_id": str(check_id),
        "kind": PHRASE_UNMATCHED,
        "phrase_id": str(phrase["id"]),
        "words": list(phrase["words"]),
        "nearest_words": list(nearest_words),
        "detail": f"{declared} (nearest rendered: {rendered})",
    }


def allowlist_matches(
    words: list[dict[str, Any]],
    allowlist: set[str],
) -> list[dict[str, Any]]:
    """Return every rendered word an allowlist names, in reading order."""
    return [word for word in sorted(words, key=_reading_key) if _text(word) in allowlist]


def allowlist_unmatched_failure(
    check_id: str,
    allowlist: set[str],
    nearest_words: list[str],
) -> dict[str, Any]:
    declared = ", ".join(sorted(allowlist))
    rendered = ", ".join(nearest_words) if nearest_words else "none"
    return {
        "check_id": str(check_id),
        "kind": ALLOWLIST_UNMATCHED,
        "words": sorted(allowlist),
        "nearest_words": list(nearest_words),
        "detail": f"{declared} (nearest rendered: {rendered})",
    }


def binding_state(checked: int, failures: list[dict[str, Any]]) -> str:
    if failures:
        return "failed"
    return "passed" if checked else "not_declared"
