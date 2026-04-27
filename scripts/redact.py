"""Redact numerical + unit tokens from briefing/spec text.

v0.1 scope: pure-stdlib regex sweep over standard SI / composition / electrical units.
Returns redacted text + audit list so the caller can show a human what was stripped
before sending to an external image-gen tool.

Out of scope (v0.2+): domain ontology lookup (e.g. "85 wt% sulfur" → "sulfur-rich"),
context-aware ratio handling, multilingual unit detection.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Each entry: (regex source, category label).
# Order matters: longer/more-specific patterns first.
_UNIT_PATTERNS: list[tuple[str, str]] = [
    (r"\d+(?:\.\d+)?\s*wt\s*%", "composition"),
    (r"\d+(?:\.\d+)?\s*at\s*%", "composition"),
    (r"\d+(?:\.\d+)?\s*mol\s*%", "composition"),
    (r"\d+(?:\.\d+)?\s*vol\s*%", "composition"),
    (r"\d+(?:\.\d+)?\s*(?:[kMG]V|[mµu]V|V)\b", "voltage"),
    (r"\d+(?:\.\d+)?\s*(?:[mµu]?A)\b", "current"),
    (r"\d+(?:\.\d+)?\s*(?:[kMG]Hz|Hz)\b", "frequency"),
    (r"\d+(?:\.\d+)?\s*(?:[mµun]m|cm|m)\b", "length"),
    (r"\d+(?:\.\d+)?\s*(?:°C|K)\b", "temperature"),
    (r"\d+(?:\.\d+)?\s*(?:ms|µs|us|ns|min|hr?|s)\b", "time"),
    (r"\d+(?:\.\d+)?\s*(?:[kMG]?Pa)\b", "pressure"),
    (r"\d+(?:\.\d+)?\s*(?:[mkµu]?N)\b", "force"),
    (r"\d+(?:\.\d+)?\s*(?:[kMG]J|[kMG]W|J|W)\b", "energy_power"),
    (r"\d+(?:\.\d+)?\s*(?:µm|nm|Å)", "length"),
    (r"\d+(?:\.\d+)?\s*dpi\b", "resolution"),
]

_RATIO_PATTERN = re.compile(r"\b\d+\s*[:/]\s*\d+\b")


@dataclass
class RedactionEvent:
    original: str
    replacement: str
    category: str
    span: tuple[int, int]


def _build_combined_pattern() -> re.Pattern[str]:
    parts = [f"(?P<g{i}>{src})" for i, (src, _) in enumerate(_UNIT_PATTERNS)]
    return re.compile("|".join(parts), re.IGNORECASE)


_COMBINED = _build_combined_pattern()


def redact(text: str) -> tuple[str, list[RedactionEvent]]:
    """Replace numerical + unit tokens with [REDACTED:<category>].

    Returns (redacted_text, audit). Audit also contains ratio_warning entries
    where text like '70/30' or '3:1' is left untouched but flagged for review.
    """
    audit: list[RedactionEvent] = []
    out_chunks: list[str] = []
    last = 0
    for m in _COMBINED.finditer(text):
        out_chunks.append(text[last : m.start()])
        for i, (_, cat) in enumerate(_UNIT_PATTERNS):
            if m.group(f"g{i}"):
                rep = f"[REDACTED:{cat}]"
                out_chunks.append(rep)
                audit.append(RedactionEvent(m.group(0), rep, cat, m.span()))
                break
        last = m.end()
    out_chunks.append(text[last:])
    redacted = "".join(out_chunks)

    for m in _RATIO_PATTERN.finditer(redacted):
        audit.append(
            RedactionEvent(
                original=m.group(0),
                replacement=m.group(0),
                category="ratio_warning",
                span=m.span(),
            )
        )

    return redacted, audit


def format_audit(audit: list[RedactionEvent]) -> str:
    if not audit:
        return "(no redactions)"
    lines = []
    for ev in audit:
        if ev.category == "ratio_warning":
            lines.append(f"  ⚠️ ratio_warning: {ev.original!r} (kept — review manually)")
        else:
            lines.append(
                f"  REDACTED [{ev.category}]: {ev.original!r} → {ev.replacement}"
            )
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: redact.py <input.md|->", file=sys.stderr)
        return 2
    src = sys.argv[1]
    text = sys.stdin.read() if src == "-" else Path(src).read_text()
    redacted, audit = redact(text)
    sys.stdout.write(redacted)
    print("\n=== Redaction audit ===", file=sys.stderr)
    print(format_audit(audit), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
