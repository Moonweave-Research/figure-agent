"""Build a filled LLM authoring prompt for a figure-agent example."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))


from inputs import _HTML_COMMENT, parse_briefing, parse_spec
from lint_tex import parse_palette


def _format_structural_regions(sr: dict) -> str:
    """Format structural_regions as an actionable coordinate block for TikZ authoring."""
    lines: list[str] = []

    img = sr.get("image_px", [])
    cmp = sr.get("cm_per_px", 0)
    if img and cmp:
        w = round(img[0] * cmp, 1)
        h = round(img[1] * cmp, 1)
        lines += [f"Canvas: {w} × {h} cm  (y=0 at bottom; {cmp:.5f} cm/px)", ""]

    arcs = sr.get("panel_arcs", [])
    if arcs:
        lines.append("Panel arcs — draw as ellipses:")
        for a in arcs:
            bb = a["bbox_cm"]
            cx = round((bb[0] + bb[2]) / 2, 2)
            cy = round((bb[1] + bb[3]) / 2, 2)
            rx = round((bb[2] - bb[0]) / 2, 2)
            ry = round((bb[3] - bb[1]) / 2, 2)
            lines.append(
                f"  {a['color_family']:8s}: center=({cx},{cy})  rx={rx}  ry={ry}"
                f"  [x={bb[0]}-{bb[2]}, y={bb[1]}-{bb[3]}]"
            )
        lines.append("")

    bbs = sr.get("border_boxes", [])
    if bbs:
        lines.append("Border boxes:")
        for b in bbs:
            bb = b["bbox_cm"]
            lines.append(f"  {b['color_family']:8s}: x={bb[0]}-{bb[2]}  y={bb[1]}-{bb[3]}")
        lines.append("")

    pbs = sr.get("plot_boxes", [])
    if pbs:
        lines.append("Axis background boxes (inside each panel):")
        for p in pbs:
            bb = p["bbox_cm"]
            lines.append(f"  panel={p['panel_family']:8s}: x={bb[0]}-{bb[2]}  y={bb[1]}-{bb[3]}")
        lines.append("")

    pcs = sr.get("plot_curves", [])
    if pcs:
        lines.append("Plot curve bounding boxes:")
        for c in pcs:
            bb = c["bbox_cm"]
            lines.append(
                f"  {c['element']:26s}(panel={c['panel_family']}): x={bb[0]}-{bb[2]}  y={bb[1]}-{bb[3]}"
            )
        lines.append("")

    lobes = sr.get("ispd_lobes", [])
    if lobes:
        lines.append("ISPD g(Et) bell lobes (inside orange panel arc):")
        for lobe in lobes:
            bb = lobe["bbox_cm"]
            lines.append(
                f"  {lobe['level_role']:8s}({lobe['color_family']}): x={bb[0]}-{bb[2]}  y={bb[1]}-{bb[3]}"
            )
        lines.append("")

    rows = sr.get("chain_rows", [])
    if rows:
        lines.append("Chain rows (draw as plot[smooth] wavy chains):")
        for i, r in enumerate(rows):
            lines.append(
                f"  row {i}: y_center={r['y_center_cm']} cm  x={r['x_span_cm'][0]}-{r['x_span_cm'][1]}"
            )
        lines.append("")

    atoms = sr.get("s_atoms", [])
    if atoms and rows:
        lines.append("S-atom x-positions per chain row (place S labels + circles at these x):")
        for i in range(len(rows)):
            xs = sorted(a["x_cm"] for a in atoms if a["chain_row_index"] == i)
            if xs:
                lines.append(
                    f"  row {i} (y≈{rows[i]['y_center_cm']}): " + "  ".join(str(x) for x in xs)
                )
        lines.append("")

    traps = sr.get("trap_levels", [])
    if traps:
        lines.append(
            "Trap level dashes (inside band diagram, use cAmber=shallow, cBlue!45!cRed=deep):"
        )
        for t in traps:
            lines.append(f"  {t['level_role']:8s}: y={t['y_cm']} cm  x_center={t['x_cm']}")
        lines.append("")

    rgs = sr.get("right_gaussians", [])
    if rgs:
        lines.append("Right-zone g(Et) Gaussians (sideways, inside teal border):")
        for g in rgs:
            bb = g["bbox_cm"]
            lines.append(f"  {g['level_role']:8s}: x={bb[0]}-{bb[2]}  y={bb[1]}-{bb[3]}")
        lines.append("")

    return "\n".join(lines).rstrip() if lines else "(no structural regions extracted)"


TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "prompts" / "llm_author_tikz.md"

_RE_FLAGSHIP_NEWCOMMAND = re.compile(
    r"\\newcommand\{\\(IsoBlock|IsoCharge|GradSlab|IsoConeTip"
    r"|BellCurve|WavyChain|BandDiagram|LogLogPlot)\}\[(\d+)\]"
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


def _coerce_selection_notes(raw: object, example_name: str) -> str:
    # Three real-world failure modes the v0.1.7 mid-review surfaced:
    #   1. Non-string YAML scalar (int, list, dict, bare date like 2026-04-29).
    #      Without this guard, _HTML_COMMENT.sub raises TypeError with no
    #      mention of selection_notes — confusing for users editing spec.yaml.
    #   2. User wrote content but it was all <!-- ... -->. The strip silently
    #      yields empty and the fallback fires. Warn so the user notices.
    #   3. Fallback parity with selected_preview ("(none)") instead of prose
    #      that an LLM might mis-read as instruction.
    if raw is None:
        return "(none)"
    if not isinstance(raw, str):
        print(
            f"llm_author_prompt.py: WARN — selection_notes in {example_name}/spec.yaml "
            f"is {type(raw).__name__}, not str; coercing. Use a YAML block scalar "
            f"(`selection_notes: |`) for prose.",
            file=sys.stderr,
        )
        raw = str(raw)
    cleaned = _HTML_COMMENT.sub("", raw).strip()
    if not cleaned and raw.strip():
        print(
            f"llm_author_prompt.py: WARN — selection_notes in {example_name}/spec.yaml "
            f"reduced to empty after HTML-comment stripping; using fallback. Visible "
            f"directives must live outside <!-- ... --> blocks.",
            file=sys.stderr,
        )
    return cleaned or "(none)"


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

    # spec.get("selected_preview") returns None when the YAML literal is `null`,
    # not the default. Coerce both the missing-key and explicit-null cases to
    # the "(none)" sentinel so the str.replace substitution below does not raise.
    selected_preview = spec.get("selected_preview") or "(none)"

    selection_notes = _coerce_selection_notes(spec.get("selection_notes"), example_dir.name)

    # Collect style-reference .tex files from sibling examples (excluding current).
    # Criterion: fixture has a .tex file AND an exports/ directory with at least one
    # artifact (stage 6). accepted: true fixtures are listed first; stage-6 others
    # follow. Both teach the same house style; acceptance status is for QA gates only.
    accepted_tex: list[str] = []
    stage6_tex: list[str] = []
    examples_dir = example_dir.parent
    for fixture_dir in sorted(examples_dir.iterdir()):
        if not fixture_dir.is_dir() or fixture_dir.resolve() == example_dir.resolve():
            continue
        fixture_tex_path = fixture_dir / f"{fixture_dir.name}.tex"
        fixture_exports = fixture_dir / "exports"
        if not fixture_tex_path.exists():
            continue
        has_exports = fixture_exports.is_dir() and any(fixture_exports.iterdir())
        if not has_exports:
            continue
        fixture_spec_path = fixture_dir / "spec.yaml"
        is_accepted = False
        if fixture_spec_path.exists():
            try:
                fs = parse_spec(fixture_spec_path.read_text(encoding="utf-8"))
                is_accepted = bool(fs and fs.get("accepted") is True)
            except Exception:
                pass
        if is_accepted:
            accepted_tex.append(str(fixture_tex_path))
        else:
            stage6_tex.append(str(fixture_tex_path))
    all_refs = accepted_tex + stage6_tex
    if all_refs:
        reference_fixture_paths = "\n".join(f"- `{p}`" for p in all_refs)
    else:
        reference_fixture_paths = (
            "(no stage-6 fixtures in examples/ yet — author from briefing.md only)"
        )

    def _section_body(num: int) -> str:
        entry = sections.get(num)
        if entry is None:
            return "(empty)"
        return entry[1] if entry[1] else "(empty)"

    # structural_regions from coordinate_hints.yaml (Layer 2.5 extraction)
    hints_path = example_dir / "coordinate_hints.yaml"
    structural_regions = "(no coordinate_hints.yaml — run /fig_extract <name> to generate)"
    if hints_path.exists():
        try:
            hints = yaml.safe_load(hints_path.read_text(encoding="utf-8"))
            sr = hints.get("structural_regions", {})
            if sr.get("status") == "ok":
                structural_regions = _format_structural_regions(sr)
            else:
                structural_regions = (
                    f"(structural_regions status: {sr.get('status', 'missing')}"
                    " — run /fig_extract <name> --rebuild)"
                )
        except Exception:
            structural_regions = "(coordinate_hints.yaml could not be parsed)"

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
        "{{reference_fixture_paths}}": reference_fixture_paths,
        "{{structural_regions}}": structural_regions,
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
