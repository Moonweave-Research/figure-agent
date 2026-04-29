"""Build a filled LLM authoring prompt for a figure-agent example."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inputs import _HTML_COMMENT, parse_briefing, parse_spec
from lint_tex import parse_palette

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "prompts" / "llm_author_tikz.md"

_RE_FLAGSHIP_NEWCOMMAND = re.compile(
    r"\\newcommand\{\\(IsoBlock|IsoCharge|GradSlab|IsoConeTip)\}\[(\d+)\]"
)
# Preamble signature comments are the single source of truth for the args
# the LLM should fill in. Two shapes appear in the .sty:
#   % \IsoCharge{x,y,sign}: half-buried hemisphere charge dot
#   % \IsoBlock{w}{d}{h}{color}{hook}: isometric block at origin
# Hardcoding signatures here previously drifted from the actual preamble API.
_RE_FLAGSHIP_COMMENT = re.compile(
    r"^%\s*(\\\w+(?:\{[^}]*\})+)\s*:\s*(.+?)\s*$",
    re.MULTILINE,
)


def _build_flagship_bullets(sty_text: str) -> list[str]:
    sigs: dict[str, tuple[str, str]] = {}
    for match in _RE_FLAGSHIP_COMMENT.finditer(sty_text):
        full_sig = match.group(1)
        descr = match.group(2)
        name_match = re.match(r"\\(\w+)", full_sig)
        if name_match:
            sigs[name_match.group(1)] = (full_sig, descr)

    bullets: list[str] = []
    for nc_match in _RE_FLAGSHIP_NEWCOMMAND.finditer(sty_text):
        name = nc_match.group(1)
        if name in sigs:
            full_sig, descr = sigs[name]
            bullets.append(f"- `{full_sig}` — {descr}")
        else:
            bullets.append(
                f"- `\\{name}` — signature missing from preamble; "
                f"add `% \\{name}{{args}}: description` above its \\newcommand"
            )
    return bullets


def build_prompt(example_dir: Path) -> str:
    spec_path = example_dir / "spec.yaml"
    briefing_path = example_dir / "briefing.md"

    if not spec_path.exists() or not briefing_path.exists():
        print(
            f"llm_author_prompt.py: spec.yaml or briefing.md missing in {example_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    sty_path = Path(__file__).resolve().parents[1] / "styles" / "polymer-paper-preamble.sty"
    if not TEMPLATE_PATH.exists():
        print(
            f"llm_author_prompt.py: template not found: {TEMPLATE_PATH}",
            file=sys.stderr,
        )
        sys.exit(2)
    if not sty_path.exists():
        print(
            f"llm_author_prompt.py: preamble .sty not found: {sty_path}",
            file=sys.stderr,
        )
        sys.exit(2)

    spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    sections = parse_briefing(briefing_path.read_text(encoding="utf-8"))

    palette = parse_palette(sty_path)
    palette_names = ", ".join(sorted(palette))

    sty_text = sty_path.read_text(encoding="utf-8")
    flagship_bullets = _build_flagship_bullets(sty_text)
    flagship_macros_signature = "\n".join(flagship_bullets) if flagship_bullets else "(none found)"

    panels = spec.get("panels", [])
    panel_bullets = "\n".join(f"- ({p.get('id', '?')}) {p.get('caption', '')}" for p in panels)
    spec_panels = panel_bullets if panel_bullets else "(no panels)"

    selected_preview = spec.get("selected_preview", "(none)")

    selection_notes_raw = spec.get("selection_notes", "") or ""
    selection_notes = _HTML_COMMENT.sub("", selection_notes_raw).strip() or (
        "(none — only preview filename selected)"
    )

    def _section_body(num: int) -> str:
        entry = sections.get(num)
        if entry is None:
            return "(empty)"
        return entry[1] if entry[1] else "(empty)"

    substitutions = {
        "{{example_name}}": example_dir.name,
        "{{briefing_section_1}}": _section_body(1),
        "{{briefing_section_3}}": _section_body(3),
        "{{briefing_section_5}}": _section_body(5),
        "{{briefing_section_6}}": _section_body(6),
        "{{spec_panels}}": spec_panels,
        "{{selected_preview}}": selected_preview,
        "{{selection_notes}}": selection_notes,
        "{{flagship_macros_signature}}": flagship_macros_signature,
        "{{palette_names}}": palette_names,
    }

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    # Use str.replace — never re.sub — because §6 content contains backslashes.
    for key, value in substitutions.items():
        template = template.replace(key, value)

    return template


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate LLM TikZ authoring prompt for an example."
    )
    parser.add_argument("example_dir", type=Path)
    args = parser.parse_args()

    prompt = build_prompt(args.example_dir)
    print(prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
