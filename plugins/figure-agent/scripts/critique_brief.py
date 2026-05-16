"""Emit the L4.5 vision-critique brief from briefing.md + TikZ + rendered PNG.

Produces the prompt-context block consumed by the `/fig_critique <name>` slash
command. The host Claude Code main loop reads the brief together with the
build PNG (via the Read tool) and writes the structured critique to
`examples/<name>/critique.md` (YAML front-matter + Markdown summary, schema
v1). No external API is called; the brief itself is API-free.

Successor to the v0.1 `review_brief.py` (HALT-then-paste workflow); see
`docs/architecture-v0.2-proposal.md` §4.5 for the rename + extend rationale.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from inputs import parse_briefing, parse_spec
from PIL import Image

MISSING_INVARIANTS = (
    "(none provided — critic should infer plausible physics constraints from §1+§2)"
)
STYLE_LOCK_PATH = Path(__file__).resolve().parent.parent / "styles" / "polymer-paper-preamble.sty"
_PANEL_ID_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")
_HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$", re.MULTILINE)


class CritiqueBriefError(Exception):
    """Expected user-facing error while preparing the critique brief."""


def _require_file(path: Path, hint: str | None = None) -> None:
    if path.exists():
        return
    message = f"missing {path}"
    if hint:
        message = f"{message}; {hint}"
    raise FileNotFoundError(message)


def _author_intent(sections: dict[int, tuple[str, str]]) -> str:
    topic = sections.get(1, ("", ""))[1].strip()
    composition = sections.get(3, ("", ""))[1].strip()
    semantic_constraints = sections.get(7, ("", ""))[1].strip()
    parts = [part for part in [topic, composition, semantic_constraints] if part]
    return "\n\n".join(parts) if parts else "(briefing.md §1 and §3 are empty)"


def _example_relative_path(example_dir: Path, path: Path) -> str:
    return str(Path("examples") / example_dir.name / path.relative_to(example_dir))


def _require_fresh_png(png_path: Path, source_paths: tuple[Path, ...]) -> None:
    png_mtime = png_path.stat().st_mtime
    stale_sources = [path for path in source_paths if path.stat().st_mtime > png_mtime]
    if stale_sources:
        names = ", ".join(path.name for path in stale_sources)
        raise CritiqueBriefError(
            f"stale render {png_path}; newer source file(s): {names}; run /fig_compile first"
        )


def _reference_image_path(example_dir: Path, spec: dict) -> Path | None:
    """Locate reference image. spec.yaml reference_image takes precedence over directory scan."""
    ref_image_str = spec.get("reference_image")
    if ref_image_str:
        candidate = example_dir / ref_image_str
        if candidate.is_file():
            return candidate
    panel_ref_paths = {
        example_dir / reference
        for panel in spec.get("panels", [])
        if isinstance((reference := panel.get("reference_image")), str) and reference.strip()
    }
    # Fallback: scan reference/ directory
    ref_dir = example_dir / "reference"
    if not ref_dir.is_dir():
        return None
    for candidate in [ref_dir / "golden_target_001.png"] + sorted(ref_dir.glob("*.png")):
        if candidate in panel_ref_paths:
            continue
        if candidate.exists():
            return candidate
    return None


def _panel_id(panel: dict, index: int) -> str:
    panel_id = panel.get("id")
    if panel_id is None:
        return f"panel_{index + 1}"
    return str(panel_id)


def _safe_panel_filename(panel_id: str) -> str:
    return _PANEL_ID_SAFE.sub("_", panel_id).strip("._") or "panel"


def _panel_reference_path(example_dir: Path, panel: dict) -> Path | None:
    reference = panel.get("reference_image")
    if not isinstance(reference, str) or not reference.strip():
        return None
    return example_dir / reference


def _panel_reference_paths(example_dir: Path, spec: dict) -> tuple[Path, ...]:
    paths: list[Path] = []
    for panel in spec.get("panels", []):
        if panel.get("bbox_pdf_cm") is None:
            continue
        ref_path = _panel_reference_path(example_dir, panel)
        if ref_path is not None and ref_path.exists():
            paths.append(ref_path)
    return tuple(paths)


def _critique_source_paths(
    tex_path: Path, briefing_path: Path, example_dir: Path, spec: dict
) -> tuple[Path, ...]:
    paths: list[Path] = [tex_path, briefing_path]
    spec_path = example_dir / "spec.yaml"
    if spec_path.exists():
        paths.append(spec_path)
    ref_image = _reference_image_path(example_dir, spec)
    if ref_image is not None:
        paths.append(ref_image)
    paths.extend(_panel_reference_paths(example_dir, spec))
    hints_path = example_dir / "coordinate_hints.yaml"
    if hints_path.exists():
        paths.append(hints_path)
    if STYLE_LOCK_PATH.exists():
        paths.append(STYLE_LOCK_PATH)
    return tuple(paths)


def _line_numbered(text: str) -> str:
    if not text.endswith("\n"):
        text += "\n"
    return "".join(
        f"{line_number:4d}: {line}\n" for line_number, line in enumerate(text.splitlines(), start=1)
    )


def _markdown_sections(text: str) -> dict[str, str]:
    matches = list(_HEADING_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections[title.lower()] = body
    return sections


def _selected_markdown_sections(path: Path, titles: tuple[str, ...]) -> list[str]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    sections = _markdown_sections(text)
    selected: list[str] = []
    for title in titles:
        body = sections.get(title.lower())
        if body:
            selected.append(f"#### {title}\n{body}")
    return selected


def _optional_authoring_context(example_dir: Path) -> str:
    blocks: list[str] = []

    contract_sections = _selected_markdown_sections(
        example_dir / "authoring_contract.md",
        ("Theory Invariants", "Forbidden Transfers", "Source Limitations", "Acceptance Rubric"),
    )
    if contract_sections:
        blocks.append("### Authoring Contract\n" + "\n\n".join(contract_sections))

    reference_pack = example_dir / "reference" / "reference_pack.md"
    if reference_pack.is_file():
        blocks.append("### Reference Pack\n" + reference_pack.read_text(encoding="utf-8").strip())

    plan_sections = _selected_markdown_sections(
        example_dir / "authoring_plan.md",
        ("Patch Order", "Human Checkpoints"),
    )
    if plan_sections:
        blocks.append("### Authoring Plan\n" + "\n\n".join(plan_sections))

    theory_guard = example_dir / "theory_guard.md"
    if theory_guard.is_file():
        blocks.append("### Theory Guard\n" + theory_guard.read_text(encoding="utf-8").strip())

    if not blocks:
        return ""
    return "\n\n## Reference-conditioned authoring context\n" + "\n\n".join(blocks)


def _pdf_page_size_cm(pdf_path: Path) -> tuple[float, float]:
    if not pdf_path.is_file():
        raise CritiqueBriefError(f"missing {pdf_path}; run /fig_compile first")
    try:
        import pdfplumber
    except ImportError as exc:
        raise CritiqueBriefError("pdfplumber required for panel bbox cropping") from exc

    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise CritiqueBriefError(f"empty PDF {pdf_path}")
        page = pdf.pages[0]
        return (float(page.width) * 2.54 / 72.0, float(page.height) * 2.54 / 72.0)


def _crop_panel_png(
    png_path: Path,
    pdf_path: Path,
    bbox_pdf_cm: list[float],
    output_path: Path,
) -> Path:
    page_width_cm, page_height_cm = _pdf_page_size_cm(pdf_path)
    x0, y0, x1, y1 = bbox_pdf_cm
    if x1 <= x0 or y1 <= y0:
        raise CritiqueBriefError("bbox_pdf_cm must satisfy x1>x0 and y1>y0")
    if x0 < 0 or y0 < 0 or x1 > page_width_cm or y1 > page_height_cm:
        raise CritiqueBriefError(
            "bbox_pdf_cm outside PDF page bounds "
            f"[0, 0, {page_width_cm:.3f}, {page_height_cm:.3f}]"
        )

    with Image.open(png_path) as image:
        width_px, height_px = image.size
        crop_box = (
            round(x0 / page_width_cm * width_px),
            round(y0 / page_height_cm * height_px),
            round(x1 / page_width_cm * width_px),
            round(y1 / page_height_cm * height_px),
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.crop(crop_box).save(output_path)
    return output_path


def _format_bbox(values: list[float]) -> str:
    return "[" + ", ".join(f"{value:.3f}" for value in values) + "]"


def _panel_reference_sections(
    example_dir: Path, spec: dict, png_path: Path, pdf_path: Path
) -> tuple[str, str]:
    contexts: list[str] = []
    warnings: list[str] = []
    for index, panel in enumerate(spec.get("panels", [])):
        ref_path = _panel_reference_path(example_dir, panel)
        if ref_path is None:
            continue
        panel_id = _panel_id(panel, index)
        if not ref_path.is_file():
            reference = panel.get("reference_image")
            warnings.append(
                f"WARN: Panel `{panel_id}` declares reference_image `{reference}` "
                "but that file is missing; skipping per-panel comparison."
            )
            continue
        bbox = panel.get("bbox_pdf_cm")
        if bbox is None:
            warnings.append(
                f"WARN: Panel `{panel_id}` declares reference_image but no bbox_pdf_cm; "
                "skipping per-panel comparison."
            )
            continue

        crop_path = example_dir / "build" / "panel_crops" / f"{_safe_panel_filename(panel_id)}.png"
        try:
            _crop_panel_png(png_path, pdf_path, bbox, crop_path)
        except CritiqueBriefError as exc:
            raise CritiqueBriefError(f"panel `{panel_id}` crop failed: {exc}") from exc

        contexts.append(
            "\n".join(
                [
                    f"### Panel `{panel_id}`",
                    f"- Build crop: `{_example_relative_path(example_dir, crop_path)}`",
                    f"- Panel reference: `{_example_relative_path(example_dir, ref_path)}`",
                    f"- bbox_pdf_cm: {_format_bbox(bbox)}",
                    "- Critique instruction: Compare this panel's build crop to its reference. "
                    "Note structural/topological deviations; style lock is handled elsewhere.",
                ]
            )
        )

    warning_section = ""
    if warnings:
        warning_section = "\n\n## Per-panel reference warnings\n" + "\n".join(warnings)
    context_section = ""
    if contexts:
        context_section = "\n\n## Per-panel reference contexts\n" + "\n\n".join(contexts)
    return warning_section, context_section


def generate_for(example_dir: Path) -> str:
    """Compose the reviewer brief for one `examples/<name>` directory."""
    if not example_dir.is_dir():
        raise FileNotFoundError(f"not a directory: {example_dir}")

    spec_path = example_dir / "spec.yaml"
    briefing_path = example_dir / "briefing.md"
    _require_file(spec_path)
    _require_file(briefing_path)

    spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    sections = parse_briefing(briefing_path.read_text(encoding="utf-8"))
    name = str(spec.get("name") or example_dir.name)

    tex_path = example_dir / f"{name}.tex"
    png_path = example_dir / "build" / f"{name}.png"
    pdf_path = example_dir / "build" / f"{name}.pdf"
    _require_file(tex_path)
    _require_file(png_path, "run /fig_compile first")
    _require_fresh_png(png_path, _critique_source_paths(tex_path, briefing_path, example_dir, spec))

    tex = tex_path.read_text(encoding="utf-8")
    numbered_tex = _line_numbered(tex)
    invariants = sections.get(6, ("", ""))[1].strip() or MISSING_INVARIANTS
    render_path = _example_relative_path(example_dir, png_path)
    ref_image = _reference_image_path(example_dir, spec)
    ref_path = _example_relative_path(example_dir, ref_image) if ref_image else None

    ref_section = ""
    if ref_path:
        ref_section = f"""

**Reference image (for drift detection):** `{ref_path}`
(If the current render differs from reference, cite both in findings.
Use reference image as a tiebreaker in case of conflicting interpretations.)"""
    panel_warning_section, panel_context_section = _panel_reference_sections(
        example_dir, spec, png_path, pdf_path
    )
    image_context_sections = f"{ref_section}{panel_warning_section}{panel_context_section}"
    authoring_context_section = _optional_authoring_context(example_dir)
    render_read_note = (
        "(The slash command loads this PNG into the host main loop via the Read tool.)"
    )

    return f"""# Critique brief — {name}

**Render to inspect:** `{render_path}`
{render_read_note}{image_context_sections}

## Author intent (from briefing.md)
{_author_intent(sections)}

## Physics invariants the figure MUST honor
{invariants}
{authoring_context_section}

## Source under review (TikZ)
```tex
{numbered_tex}```

## Critique rubric

### A. Physics correctness
- For each invariant in the section above, verify the rendered figure preserves it.
  Cite the .tex line numbers where a violation is seen.
- Check band ordering, arrow directions, label↔target binding, and any quantitative claim
  that contradicts the briefing.

### B. Aesthetic placement
- Label positioning: is each label clearly attached to its intended target? Is the offset
  consistent across labels of the same kind?
- Whitespace: does the figure feel cluttered or balanced?
- Visual hierarchy: are the most important elements visually dominant?
- Palette: are colors used consistently with their semantic role
  (e.g., blue=conduction, red=valence, amber=trap)?
- Nature-schematic style: minimal, sans-serif, no unnecessary text?

## Output format

Write findings to `examples/{name}/critique.md` with this exact structure
(YAML front-matter then human-readable Markdown body — schema v1):

```markdown
---
schema: figure-agent.critique.v1
fixture: {name}
generated_at: <ISO-8601 timestamp>
verdict: ready | revise | block
panels:
  - id: <panel id>
    findings:
      - id: P001
        severity: BLOCKER | MAJOR | MINOR | NIT
        category: structural | physics | label_placement | whitespace | hierarchy | palette | style
        tex_lines: [<int>, ...]
        observation: "<panel-specific difference between build crop and panel reference>"
        suggested_fix: "<concrete edit to the .tex>"
        status: open
findings:
  - id: C001
    severity: BLOCKER | MAJOR | MINOR | NIT
    category: physics | label_placement | whitespace | hierarchy | palette | style
    tex_lines: [<int>, ...]
    observation: "<what is wrong, citing what you see in the PNG>"
    suggested_fix: "<concrete edit to the .tex>"
    status: open
---

# Vision Critique — {name}

<one-paragraph overall verdict, then per-finding prose discussion>
```

Use `panels: []` when no panel has both `reference_image` and `bbox_pdf_cm`.
Keep figure-level findings in top-level `findings:`; do not move them under panels.
`verdict: ready` if zero BLOCKER + zero MAJOR findings; `revise` for any
MAJOR/MINOR; `block` only if a BLOCKER physics violation makes the figure
unsuitable for manuscript use. Critique is **report-only** for v0.2 — do
NOT auto-edit `<name>.tex`. See `docs/architecture-v0.2-proposal.md` §7.

---
(Generated by figure-agent /fig_critique for {name}. API-free; the host
Claude Code main loop reads the PNG and produces the critique using only
subscription tokens.)
"""


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: critique_brief.py <example_dir>", file=sys.stderr)
        return 2

    try:
        brief = generate_for(Path(sys.argv[1]))
    except (FileNotFoundError, CritiqueBriefError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(brief, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
