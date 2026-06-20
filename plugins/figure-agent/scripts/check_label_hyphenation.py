#!/usr/bin/env python3
"""WARN-tier lint: flag mid-word line breaks (trailing-hyphen tokens) in labels.

TikZ ``\\node`` labels with a fixed ``text width`` hyphenate words across lines
("nar-row", "in-jects", "elec-trode"). pdftotext renders the broken fragment as a
token ending in an ASCII hyphen (U+002D). In this schematic domain a trailing
ASCII hyphen is always a line-break artifact — en dashes (U+2013) and minus signs
(U+2212) are different code points and are not matched — so flag it for review.
Report-only by default; ``--strict`` exits non-zero when artifacts are found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from check_visual_clash import extract_pdf_words_and_page

SCHEMA = "figure-agent.label-hyphenation.v1"


def detect_label_hyphenation(words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return word boxes whose text ends in an ASCII hyphen (a line-break artifact)."""
    issues: list[dict[str, Any]] = []
    for word in words:
        text = word["text"]
        if len(text) > 1 and text.endswith("-"):
            issues.append(
                {
                    "text": text,
                    "xmin": word["xmin"],
                    "ymin": word["ymin"],
                    "xmax": word["xmax"],
                    "ymax": word["ymax"],
                    "message": (
                        f"hyphenated line break {text!r}: a fixed-width node wrapped a "
                        "word; widen text width or reword the label"
                    ),
                }
            )
    return issues


def label_hyphenation_payload(pdf_path: Path, issues: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "render_pdf": f"build/{pdf_path.name}",
        "issues": issues,
        "total": len(issues),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Flag hyphenated label line breaks.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    pdf_path: Path = args.pdf
    if not pdf_path.is_file():
        print(f"ERROR: missing PDF: {pdf_path}", file=sys.stderr)
        return 2
    try:
        words, _ = extract_pdf_words_and_page(pdf_path)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    issues = detect_label_hyphenation(words)
    output = args.json_output or pdf_path.parent / "label_hyphenation.json"
    output.write_text(
        json.dumps(label_hyphenation_payload(pdf_path, issues), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for issue in issues:
        print(
            f"WARN label_hyphenation: {issue['text']!r} — {issue['message']}",
            file=sys.stderr,
        )
    if issues:
        print(f"{len(issues)} label hyphenation artifact(s)", file=sys.stderr)
        if args.strict:
            return 1
    else:
        print(f"OK: no label hyphenation found in {pdf_path.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
