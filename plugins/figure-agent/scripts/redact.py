"""Normalize distracting literal tokens from briefing/spec text.

The public API intentionally remains ``redact()`` for v0.1 compatibility, but
the behavior is prompt normalization: preserve schematic intent while replacing
literal counts, sample labels, dimensions, and experimental values that make
image-gen tools overfit to the wrong detail. v0.2 will rename this module to
normalize.py.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

_DOMAIN_TERMS = ("CB", "VB", "HOMO", "LUMO", "E_t", "kT")
_DATA_PLOT_SIGNALS = re.compile(
    r"\b(?:plot|error\s*bars?|raw\s*\+\s*fit|peak\s*position|sweep|"
    r"vs\s+(?:composition|time|voltage|temperature))\b",
    re.IGNORECASE,
)


_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


def _quantity_from_phrase(phrase: str) -> int | None:
    numeric = re.search(r"\d+", phrase)
    if numeric:
        return int(numeric.group(0))
    word = phrase.split()[0].lower() if phrase.split() else ""
    return _NUMBER_WORDS.get(word)


def _count_replacement(phrase: str, noun: str) -> str:
    noun = noun.lower()
    quantity = _quantity_from_phrase(phrase)
    if noun.startswith("dot") or "점" in noun:
        if quantity is not None and quantity <= 2:
            return "a small cluster of dots"
        return "a few dots"
    if noun.startswith("layer"):
        if quantity == 1:
            return "single layer"
        return "stacked layers"
    if noun.startswith("panel"):
        if quantity == 1:
            return "single-panel layout"
        if quantity == 2:
            return "two-panel comparison layout"
        return "multi-panel layout"
    if noun.startswith("arrow"):
        if quantity == 1:
            return "one directional arrow"
        return "directional arrows"
    if noun.startswith("electron"):
        if quantity == 1:
            return "one representative electron"
        return "several electrons"
    return f"a few {noun}"


_NORMALIZATION_PATTERNS: list[tuple[re.Pattern[str], str, str | None]] = [
    (
        re.compile(
            r"\b(?:width|height|depth|diameter|radius|length|spacing|thickness|aspect\s+ratio)\s+"
            r"\d+(?:\.\d+)?\s*(?:by|x|×)\s*\d+(?:\.\d+)?\s*(?:pixels?|px)?\b",
            re.IGNORECASE,
        ),
        "geometry",
        "general geometry",
    ),
    (
        re.compile(r"\bS\d{2,3}(?:\s*[-–/]\s*S?\d{2,3})?\b"),
        "sample_label",
        "different material compositions",
    ),
    (
        re.compile(
            r"\b\d+\s*[:/]\s*\d+\s*(?:copolymer|blend|polymer|composition|ratio|mixture)?\b",
            re.IGNORECASE,
        ),
        "composition_ratio",
        "copolymer material",
    ),
    (
        re.compile(r"\b\d+(?:\.\d+)?\s*(?:wt|at|mol|vol)\s*%\b", re.IGNORECASE),
        "composition",
        "composition-rich material",
    ),
    (
        re.compile(r"\b\d+(?:\.\d+)?\s*(?:nm|µm|um|mm|cm|m)\s+film\b", re.IGNORECASE),
        "length",
        "thin film",
    ),
    (
        re.compile(r"\b\d+(?:\.\d+)?\s*(?:nm|µm|um|mm|cm|m|Å)\b", re.IGNORECASE),
        "length",
        "qualitative length scale",
    ),
    (
        re.compile(r"\b\d+(?:\.\d+)?\s*(?:[kMG]V|[mµu]V|V)\b"),
        "voltage",
        "a representative voltage",
    ),
    (
        re.compile(r"\b\d+(?:\.\d+)?\s*(?:ms|µs|us|ns|min|hr?|s)\b", re.IGNORECASE),
        "time",
        "a representative duration",
    ),
    (
        re.compile(r"\b\d+(?:\.\d+)?\s*dpi\b", re.IGNORECASE),
        "resolution",
        "high-resolution export",
    ),
    (
        re.compile(r"\bmobile\s+electron\s+\d+\s*개\b", re.IGNORECASE),
        "count",
        "one representative mobile electron",
    ),
    (
        re.compile(r"\b\d+\s+(dots?|layers?|panels?|arrows?|electrons?)\b", re.IGNORECASE),
        "count",
        None,
    ),
    (
        re.compile(
            r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen)\s+"
            r"(dots?|layers?|panels?|arrows?|electrons?)\b",
            re.IGNORECASE,
        ),
        "count_word",
        None,
    ),
    (
        re.compile(r"\b\d+\s*(개\s*점|점)"),
        "count",
        None,
    ),
]


@dataclass
class RedactionEvent:
    original: str
    replacement: str
    category: str
    span: tuple[int, int]


def redact(text: str) -> tuple[str, list[RedactionEvent]]:
    """Normalize literal-heavy prompt text and return (normalized_text, audit)."""
    audit: list[RedactionEvent] = []
    normalized = text

    for pattern, category, fixed_replacement in _NORMALIZATION_PATTERNS:
        next_chunks: list[str] = []
        last = 0
        for match in pattern.finditer(normalized):
            next_chunks.append(normalized[last : match.start()])
            replacement = fixed_replacement
            if replacement is None:
                noun = match.group(1)
                replacement = _count_replacement(match.group(0), noun)
            next_chunks.append(replacement)
            audit.append(RedactionEvent(match.group(0), replacement, category, match.span()))
            last = match.end()
        if last:
            next_chunks.append(normalized[last:])
            normalized = "".join(next_chunks)

    for token in _DOMAIN_TERMS:
        token_pattern = rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])"
        for match in re.finditer(token_pattern, normalized):
            audit.append(
                RedactionEvent(
                    match.group(0),
                    match.group(0),
                    "domain_term",
                    match.span(),
                )
            )

    for match in _DATA_PLOT_SIGNALS.finditer(normalized):
        audit.append(
            RedactionEvent(
                original=match.group(0),
                replacement=match.group(0),
                category="data_plot_signal",
                span=match.span(),
            )
        )

    return normalized, audit


def format_audit(audit: list[RedactionEvent]) -> str:
    if not audit:
        return "(no normalization events)"
    lines = []
    for ev in audit:
        if ev.category == "domain_term":
            lines.append(f"  KEPT [domain_term]: {ev.original!r}")
        elif ev.category == "physics_invariant":
            lines.append(f"  KEPT [physics_invariant]: {ev.original!r} (verbatim constraint)")
        elif ev.category.startswith("physics_invariant_literal_"):
            lines.append(
                f"  WARN [{ev.category}]: {ev.original!r} (kept verbatim inside physics invariant)"
            )
        elif ev.category == "data_plot_signal":
            lines.append(f"  WARN [data_plot_signal]: {ev.original!r} (review scope)")
        else:
            lines.append(f"  NORMALIZED [{ev.category}]: {ev.original!r} -> {ev.replacement}")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: redact.py <input.md|->", file=sys.stderr)
        return 2
    src = sys.argv[1]
    text = sys.stdin.read() if src == "-" else Path(src).read_text()
    normalized, audit = redact(text)
    sys.stdout.write(normalized)
    print("\n=== Normalization audit ===", file=sys.stderr)
    print(format_audit(audit), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
