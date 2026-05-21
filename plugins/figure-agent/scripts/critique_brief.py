"""Emit the L4.5 vision-critique brief from briefing.md + TikZ + rendered PNG.

Produces the prompt-context block consumed by the `/fig_critique <name>` slash
command. The host Claude Code main loop reads the brief together with the
build PNG (via the Read tool) and writes the structured critique to
`examples/<name>/critique.md` (YAML front-matter + Markdown summary, schema
v1.6). No external API is called; the brief itself is API-free.

Successor to the v0.1 `review_brief.py` (HALT-then-paste workflow); see
`docs/architecture-v0.2-proposal.md` §4.5 for the rename + extend rationale.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import critique_brief_sections as brief_sections
from critique_zoom_crops import build_zoom_crop_pack
from inputs import parse_briefing, parse_spec
from PIL import Image
from quality_manifest import (
    CRITIQUE_RUBRIC_VERSION,
    compute_critique_input_hash,
    critique_generator_version,
)
from reference_contract import compute_reference_input_failures, declared_figure_reference_path
from subregion_active_set import active_subregion_ids, iteration_patch_ids, parse_active_target_rows

MISSING_INVARIANTS = (
    "(none provided — critic should infer plausible physics constraints from §1+§2)"
)
REPO_ROOT = Path(__file__).resolve().parent.parent
STYLE_LOCK_PATH = REPO_ROOT / "styles" / "polymer-paper-preamble.sty"
_PANEL_ID_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")
_HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$", re.MULTILINE)
_HIGH_ZOOM_MICRO_DEFECT_CHECKS = (
    "line_crosses_label",
    "wire_crosses_label",
    "arrow_tip_fused",
    "label_target_detached",
    "floating_semantic_cue",
    "drawing_order_suspect",
    "label_backdrop_overflows_outline",
    "label_glyph_overlaps_internal_drawing",
)
_MICRO_DEFECT_KIND_SCHEMA = (
    "line_crosses_label | wire_crosses_label | arrow_tip_fused | "
    "label_target_detached | floating_semantic_cue | drawing_order_suspect | "
    "print_scale_unreadable | label_backdrop_overflows_outline | "
    "label_glyph_overlaps_internal_drawing"
)


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
    return example_dir / reference.strip()


def _critique_source_paths(
    tex_path: Path, briefing_path: Path, example_dir: Path, spec: dict
) -> tuple[Path, ...]:
    paths: list[Path] = [tex_path, briefing_path]
    spec_path = example_dir / "spec.yaml"
    if spec_path.exists():
        paths.append(spec_path)
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

    subregion_context = _subregion_active_context(example_dir)
    if subregion_context:
        blocks.append(subregion_context)

    if not blocks:
        return ""
    return "\n\n## Reference-conditioned authoring context\n" + "\n\n".join(blocks)


def _subregion_active_context(example_dir: Path) -> str:
    log_path = example_dir / "subregion_iteration_log.md"
    if not log_path.is_file():
        return ""
    text = log_path.read_text(encoding="utf-8")
    rows = parse_active_target_rows(text)
    active_ids = active_subregion_ids(rows)
    patch_ids = iteration_patch_ids(text)
    active_display = ", ".join(active_ids) if active_ids else "(none)"
    patch_display = ", ".join(patch_ids) if patch_ids else "(none)"
    return "\n".join(
        [
            "### Sub-region Active Set",
            f"- Active targets: {active_display}",
            f"- Observed patch units: {patch_display}",
            "- Critique instruction: focus sub-region findings on active targets. "
            "Do not reopen named-but-stable regions without concrete visual or theory evidence.",
        ]
    )


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
) -> tuple[str, str, tuple[Path, ...]]:
    contexts: list[str] = []
    warnings: list[str] = []
    panel_crop_paths: list[Path] = []
    for index, panel in enumerate(spec.get("panels", [])):
        ref_path = _panel_reference_path(example_dir, panel)
        if ref_path is None:
            if panel.get("bbox_pdf_cm") is not None:
                panel_id = _panel_id(panel, index)
                warnings.append(
                    f"WARN: Panel `{panel_id}` declares bbox_pdf_cm but no reference_image; "
                    "skipping per-panel comparison."
                )
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
        panel_crop_paths.append(crop_path)

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
    return warning_section, context_section, tuple(panel_crop_paths)


def _zoom_audit_section(example_dir: Path, crops: list[dict]) -> str:
    crops = [crop for crop in crops if crop.get("kind") == "zoom_crop"]
    if not crops:
        return ""
    lines = [
        "## High-Zoom Visual Audit Crops",
        "Host LLM MUST inspect these crops before finalizing `critique.md`.",
        "These are original-pixel attention crops; the zoom effect comes from inspecting "
        "each crop separately instead of only the full render.",
        "For each crop, check these closed-set micro-defects: "
        + ", ".join(_HIGH_ZOOM_MICRO_DEFECT_CHECKS)
        + ".",
        "",
    ]
    for crop in crops:
        crop_path = example_dir / crop["path"]
        source_path = example_dir / crop["source_path"]
        lines.append(
            f"- `{_example_relative_path(example_dir, crop_path)}` "
            f"from `{_example_relative_path(example_dir, source_path)}` "
            f"bbox_px={crop['bbox_px']}"
        )
    return "\n" + "\n".join(lines) + "\n"


def _print_scale_audit_section(example_dir: Path, crops: list[dict]) -> str:
    print_items = [crop for crop in crops if crop.get("kind") == "print_scale"]
    if not print_items:
        return ""
    lines = [
        "## Print-Scale Audit Images",
        "Host LLM MUST inspect these reduced-scale images before setting "
        "`journal_polish` or `publication_readiness` to `pass`.",
        "Use them to check label readability, arrow-tip recognizability, line-weight "
        "survival, and dense-region legibility at manuscript scale.",
        "These are proxy evidence images: `scale_basis=fixed_width_proxy` means "
        "the image is a deterministic reduced-width readability check, not a "
        "DPI-derived physical print simulation.",
        "If reduction hides text, fuses arrow tips, or makes a dense region "
        "ambiguous, record it as `micro_defects.kind: print_scale_unreadable`.",
        "",
    ]
    for item in print_items:
        item_path = example_dir / item["path"]
        source_path = example_dir / item["source_path"]
        lines.append(
            f"- `{_example_relative_path(example_dir, item_path)}` "
            f"scale={item['scale_label']} size_px={item['size_px']} "
            f"basis={item['scale_basis']} target_width_px={item['target_width_px']} "
            f"from `{_example_relative_path(example_dir, source_path)}`"
        )
    return "\n" + "\n".join(lines) + "\n"


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
    reference_failures = compute_reference_input_failures(example_dir, spec)
    if reference_failures:
        failures = "; ".join(reference_failures)
        raise CritiqueBriefError(
            f"{failures}; fix declared reference inputs before /fig_critique"
        )

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
    ref_image = declared_figure_reference_path(example_dir, spec)
    ref_path = _example_relative_path(example_dir, ref_image) if ref_image else None
    generator_version = critique_generator_version(Path(__file__))
    critique_input_hash = compute_critique_input_hash(
        example_dir,
        name,
        spec,
        style_lock_path=STYLE_LOCK_PATH,
    )

    ref_section = ""
    if ref_path:
        ref_section = f"""

**Reference image (for drift detection):** `{ref_path}`
(If the current render differs from reference, cite both in findings.
Use reference image as a tiebreaker in case of conflicting interpretations.)"""
    panel_warning_section, panel_context_section, panel_crop_paths = _panel_reference_sections(
        example_dir, spec, png_path, pdf_path
    )
    image_context_sections = f"{ref_section}{panel_warning_section}{panel_context_section}"
    zoom_crops = build_zoom_crop_pack(example_dir, png_path, panel_crop_paths=panel_crop_paths)
    zoom_audit_section = _zoom_audit_section(example_dir, zoom_crops)
    print_scale_audit_section = _print_scale_audit_section(example_dir, zoom_crops)
    authoring_context_section = _optional_authoring_context(example_dir)
    render_read_note = (
        "(The slash command loads this PNG into the host main loop via the Read tool.)"
    )

    return f"""# Critique brief — {name}

**Render to inspect:** `{render_path}`
{render_read_note}{image_context_sections}
{zoom_audit_section}
{print_scale_audit_section}

## Author intent (from briefing.md)
{_author_intent(sections)}

## Physics invariants the figure MUST honor
{invariants}
{authoring_context_section}

## Source under review (TikZ)
```tex
{numbered_tex}```

{brief_sections.mandatory_audit_checklists()}

{brief_sections.journal_quality_axes()}

{brief_sections.top_tier_journal_audit()}

{brief_sections.editorial_art_direction_audit()}

{brief_sections.journal_grade_assessment()}

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
(YAML front-matter then human-readable Markdown body — schema v1.6):

```markdown
---
schema: figure-agent.critique.v1.6
fixture: {name}
generated_at: <ISO-8601 timestamp>
generator: critique_brief.py
generator_version: {generator_version}
rubric_version: {CRITIQUE_RUBRIC_VERSION}
critique_input_hash: {critique_input_hash}
verdict: ready | revise | block
audit_enumeration:
  structural_completeness:
    components:
      - component: <name>
        mount_support: yes|no|N/A
        rationale: "<one-line>"
        connections: "<endpoint audit>"
    missing_from_reference:
      - element: <name>
        status: intentional_omission | incomplete
        rationale: "<one-line>"
  label_target_matching:
    - label: "<text>"
      nearest_object: "<drawn-object-name>"
      intended_target: "<from-briefing-or-spec>"
      matches: true | false
      proposed_fix: "<concrete or empty if matches=true>"
  physical_plausibility:
    - check: {brief_sections.PHYSICAL_CHECK_VALUES}
      finding: "<what was observed>"
      verdict: convention_acceptable | structural_defect
  conceptual_completeness:
    - element: <name>
      reference: provided_reference | briefing | reference_pack | not_provided
      severity: BLOCKER | MAJOR | MINOR | NIT
      proposed_action: add | expand | accept_simplification
{brief_sections.quality_axes_schema()}
top_tier_audit:
  first_glance_message:
    verdict: pass | weak | fail | needs_human
    finding: "<what a reader understands in 3/10/30 seconds>"
    concrete_fix: "<specific figure edit or accept_simplification>"
    blocks_high_impact: true | false
  target_journal_fit:
    verdict: pass | weak | fail | needs_human
    finding: "<fit to target journal or generic high-impact schematic standard>"
    concrete_fix: "<specific edit or human art-direction question>"
    blocks_high_impact: true | false
  novelty_claim_support:
    verdict: pass | weak | fail | needs_human
    finding: "<whether the visual supports the manuscript's central claim>"
    concrete_fix: "<specific edit or claim-figure alignment question>"
    blocks_high_impact: true | false
  figure_caption_coupling:
    verdict: pass | weak | fail | needs_human
    finding: "<whether caption and figure share the right explanatory burden>"
    concrete_fix: "<specific figure or caption-side recommendation>"
    blocks_high_impact: true | false
  visual_economy:
    verdict: pass | weak | fail | needs_human
    finding: "<unnecessary ink, redundant marks, or missing explanatory marks>"
    concrete_fix: "<delete, simplify, or emphasize one concrete element>"
    blocks_high_impact: true | false
  cross_panel_semantic_grammar:
    verdict: pass | weak | fail | needs_human
    finding: "<color, arrow, shape, texture, and label grammar across panels>"
    concrete_fix: "<one grammar normalization edit>"
    blocks_high_impact: true | false
  reader_misinterpretation_risk:
    verdict: pass | weak | fail | needs_human
    finding: "<most likely wrong interpretation by a qualified reader>"
    concrete_fix: "<specific guardrail label, spacing, or visual cue>"
    blocks_high_impact: true | false
  reduction_print_readability:
    verdict: pass | weak | fail | needs_human
    finding: "<1-column, 2-column, thumbnail, grayscale, or print weakness>"
    concrete_fix: "<specific scale/contrast/typography edit>"
    blocks_high_impact: true | false
  accessibility_color_robustness:
    verdict: pass | weak | fail | needs_human
    finding: "<colorblind/grayscale/contrast/texture redundancy assessment>"
    concrete_fix: "<specific redundant encoding or contrast edit>"
    blocks_high_impact: true | false
  aesthetic_coherence:
    verdict: pass | weak | fail | needs_human
    finding: "<style authority across line weights, detail level, depth cues>"
    concrete_fix: "<specific style-normalization edit>"
    blocks_high_impact: true | false
{brief_sections.editorial_art_direction_schema()}
{brief_sections.journal_grade_assessment_schema(critique_input_hash)}
micro_defects:
  - id: M001
    crop: examples/{name}/build/audit_crops/<crop>.png
    kind: {_MICRO_DEFECT_KIND_SCHEMA}
    severity: BLOCKER | MAJOR | MINOR | NIT
    observation: "<visible micro-defect from a High-Zoom crop or Print-Scale image>"
    linked_finding_id: "<P001/C001 or empty when accept_simplification>"
    status: open | resolved | accept_simplification
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
    category: structural | physics | label_placement | whitespace | hierarchy | palette | style
    tex_lines: [<int>, ...]
    observation: "<what is wrong, citing what you see in the PNG>"
    suggested_fix: "<concrete edit to the .tex>"
    status: open
---

# Vision Critique — {name}

<one-paragraph overall verdict, then per-finding prose discussion>
```

Any `structural_defect`, `incomplete`, `BLOCKER`, or `MAJOR` audit item must
either appear as a normal panel/top-level finding or be explicitly justified as
`accept_simplification`.

Any `fail`, `needs_human`, or `weak` plus `blocks_high_impact: true`
`top_tier_audit` item must either appear as a normal panel/top-level finding
that explicitly mentions `top_tier_audit.<slot_key>`, be represented in
`quality_axes.blocking_items` with that same `top_tier_audit.<slot_key>`
reference plus a human/revise/block action, or be justified in `concrete_fix`
as `accept_simplification`.

Any `needs_human` `editorial_art_direction` item must either appear as a normal
panel/top-level finding that explicitly mentions
`editorial_art_direction.<slot_key>` or be represented in
`quality_axes.blocking_items` with that same reference plus a human/revise/block
action. `needs_human` editorial slots cannot use `accept_simplification` to
bypass human visibility. Any `fail` or `weak` plus `blocks_high_impact: true`
editorial item follows the same link paths, or may use `accept_simplification`
only when the weakness is intentional.

Every `needs_patch` and `block` quality axis must expose a concrete
`blocking_items` entry and either a normal panel/top-level finding or a
non-patch `recommended_action` such as `human_review`, `revise_briefing`, or
`block_release`. For `patch` or `block_release` actions, include the linked
finding id in the relevant `blocking_items` entry, e.g. `C001 - <reason>`.
`publication_readiness.verdict` must not be less severe than any applicable
upstream quality axis.

Every High-Zoom Visual Audit Crop and Print-Scale Audit Image must be inspected
before finalizing `critique.md`. Record visible crop-scale and reduction-scale
defects in `micro_defects`. Every `BLOCKER` or `MAJOR` micro-defect must either
link to a normal panel/top-level finding via `linked_finding_id` or use
`status: accept_simplification` with a clear observation explaining why the
crop-scale or print-scale issue is acceptable.

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
