"""briefing → L3 snippet candidate matcher.

First consumer of `styles/snippets/INDEX.yaml`. Ranks snippet candidates for a
given `briefing.md` by keyword + briefing_hooks substring hits against §7
(Author intent / Snippets), falling back to the whole document when §7 is
absent. Output is meant to be eyeballed against expected matches — schema
gaps and bad hooks surface as ranking surprises.

anti_patterns is read but not scored: full-sentence anti-pattern strings are
not designed for substring match. A future iteration may extract trigger
phrases; for now those entries are documentation-only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from inputs import parse_briefing

INDEX_PATH = Path(__file__).resolve().parent.parent / "styles" / "snippets" / "INDEX.yaml"
KEYWORD_WEIGHT = 1
HOOK_WEIGHT = 3


def _load_index(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _briefing_text(briefing_path: Path) -> str:
    sections = parse_briefing(briefing_path.read_text())
    if 7 in sections:
        return sections[7][1]
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
