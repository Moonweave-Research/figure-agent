"""briefing → L3 snippet candidate matcher.

First consumer of `styles/snippets/INDEX.yaml`. Ranks snippet candidates for a
given `briefing.md` by keyword + briefing_hooks substring hits against §7
(Author intent / Snippets), falling back to the whole document when §7 is
absent. Within §7, subsections whose header begins with "Must avoid" / "Must
not" / "Do not" / "Anti" are excluded from positive matching to prevent
avoidance terms from triggering matches. Output is meant to be eyeballed
against expected matches — schema gaps and bad hooks surface as surprises.

anti_patterns is read but not scored: full-sentence anti-pattern strings are
not designed for substring match. A future iteration may extract trigger
phrases; for now those entries are documentation-only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from inputs import parse_briefing

INDEX_PATH = Path(__file__).resolve().parent.parent / "styles" / "snippets" / "INDEX.yaml"
KEYWORD_WEIGHT = 1
HOOK_WEIGHT = 3

# §7 subsection headers that contain anti-text (terms to avoid). These must
# be excluded from positive matching — see fig1_overview "Bidirectional
# Actuation / Actuator / Electret" avoidance which previously gave a
# false-positive on electret_actuation.
_SUBSECTION_HEADER = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
_NEGATIVE_PREFIXES = ("must avoid", "must not", "do not", "anti")


def _load_index(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _strip_negative_subsections(section_body: str) -> str:
    parts = _SUBSECTION_HEADER.split(section_body)
    if len(parts) < 3:
        return section_body
    keep = [parts[0]]
    for i in range(1, len(parts), 2):
        title = parts[i].strip().lower()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        if not title.startswith(_NEGATIVE_PREFIXES):
            keep.append(f"### {parts[i]}\n{body}")
    return "\n".join(keep)


def _briefing_text(briefing_path: Path) -> str:
    sections = parse_briefing(briefing_path.read_text())
    if 7 in sections:
        return _strip_negative_subsections(sections[7][1])
    return briefing_path.read_text()


def _hits(needles: list[str], haystack: str) -> list[str]:
    h_lower = haystack.lower()
    return [n for n in needles if n.lower() in h_lower]


def score(entry: dict, briefing: str) -> dict:
    keywords = entry.get("discoverability", {}).get("keywords", []) or []
    hooks = entry.get("briefing_hooks", []) or []
    kw = _hits(keywords, briefing)
    hk = _hits(hooks, briefing)
    return {
        "score": len(kw) * KEYWORD_WEIGHT + len(hk) * HOOK_WEIGHT,
        "kw_matched": kw,
        "hook_matched": hk,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: match_snippet.py <briefing.md>", file=sys.stderr)
        return 2
    briefing_path = Path(argv[1])
    if not briefing_path.exists():
        print(f"missing: {briefing_path}", file=sys.stderr)
        return 1

    index = _load_index(INDEX_PATH)
    briefing = _briefing_text(briefing_path)

    scored = [(sid, score(entry, briefing)) for sid, entry in index["snippets"].items()]
    results = [(sid, r) for sid, r in scored if r["score"] > 0]
    results.sort(key=lambda x: x[1]["score"], reverse=True)

    if not results:
        print("(no snippet candidates)")
        return 0

    for sid, r in results:
        print(f"{sid}  score={r['score']}")
        if r["hook_matched"]:
            print(f"  hooks: {r['hook_matched']}")
        if r["kw_matched"]:
            print(f"  keywords: {r['kw_matched']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
