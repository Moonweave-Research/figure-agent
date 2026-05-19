"""Emit the L4.5 vision-critique brief from briefing.md + TikZ + rendered PNG.

Produces the prompt-context block consumed by the `/fig_critique <name>` slash
command. The host Claude Code main loop reads the brief together with the
build PNG (via the Read tool) and writes the structured critique to
`examples/<name>/critique.md` (YAML front-matter + Markdown summary, schema
v1.2). No external API is called; the brief itself is API-free.

Successor to the v0.1 `review_brief.py` (HALT-then-paste workflow); see
`docs/architecture-v0.2-proposal.md` §4.5 for the rename + extend rationale.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

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
_PHYSICAL_CHECK_VALUES = (
    "cable_gravity | floating_components | spatial_proximity | "
    "direction_orientation | material_distinction"
)
_QUALITY_AXIS_NAMES = (
    "message_storyline",
    "panel_role_coherence",
    "subregion_integration",
    "component_fidelity",
    "scientific_plausibility",
    "composition_layout",
    "label_annotation_semantics",
    "journal_polish",
    "reference_fidelity",
    "publication_readiness",
)
_QUALITY_VERDICT_VALUES = "pass | needs_patch | needs_human | block | not_applicable"
_QUALITY_CONFIDENCE_VALUES = "low | medium | high"
_QUALITY_ACTION_VALUES = "none | patch | human_review | revise_briefing | block_release"
_PANEL_ROLE_VALUES = (
    "setup | mechanism | result | comparison | control | zoom | model | workflow | context"
)
_PANEL_ROLE_QUALITY_VALUES = "clear | weak | missing | redundant"


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


def _mandatory_audit_checklists() -> str:
    return """## Mandatory Audit Checklists (host LLM MUST enumerate)

The host LLM MUST fill every numbered audit family below in the resulting
`critique.md` under top-level YAML field `audit_enumeration`. Empty v1.1 audit
enumeration is invalid. Do not invent literature citations; use bounded
reference provenance values from the output schema.

### A. Structural Completeness Audit
For each instrument/component currently drawn in the figure, enumerate:
1. Component name -> mounting/support visible? (yes/no/N/A + 1-line rationale)
2. Connections (wires/cables) -- does each connection have BOTH endpoints
   visibly attached to a defined component?
3. Per the provided reference context, list 3 standard parts that exist in the
   real reference-system but are MISSING or weakly represented in the current
   rendering. For each, declare `intentional_omission` vs `incomplete`.

### B. Label-Target Matching Audit
For EVERY label/annotation in the figure (enumerate, do not summarize):
1. Label text -> visually-nearest drawn object.
2. Is that nearest object the INTENDED label target per briefing/spec/source?
3. If mismatch: propose ONE concrete fix (relocation coordinate, leader-line
   addition, OR rename).

### C. Physical Plausibility Audit
Enumerate at least 5 physical-plausibility checks specific to this figure:
1. Cables/wires -- do they follow gravity, or are they intentionally schematic?
2. Floating components -- list any drawn object with no visible support, mount,
   or frame attachment.
3. Spatial proximities -- list any two components whose drawn proximity
   contradicts real-system separation.
4. Direction/orientation -- list any arrow, modulation cue, or motion indicator
   whose direction conflicts with the labeled physics.
5. Material distinction -- verify each labeled material region is visually
   distinguishable from neighbors.

### D. Conceptual Completeness Audit
List 3 elements that SHOULD be present per provided reference/briefing context
but are weakly represented or missing entirely. For each, provide element name,
bounded reference provenance, severity, and proposed action.
"""


def _journal_quality_axes() -> str:
    return """## Journal-Grade Quality Axes (host LLM MUST evaluate)

After completing `audit_enumeration`, evaluate every quality axis below under
top-level YAML field `quality_axes`. Do not collapse these axes into one opaque
score. Every `pass`, `needs_patch`, `needs_human`, or `block` verdict needs
concrete visible, briefing, reference, theory-guard, or finding evidence.
Use `not_applicable` only when the figure lacks the relevant input or structure.

### 1. Message and Storyline
Evaluate the one-sentence figure message, first-read order, relation to the
manuscript claim, missing story bridges, main-conclusion prominence, and
decorative/non-explanatory content.

### 2. Panel Role Coherence
Classify every panel role as setup, mechanism, result, comparison, control,
zoom, model, workflow, or context. Flag missing, redundant, weak, or misordered
panel roles.

### 3. Sub-region Integration
If sub-region context exists, evaluate active sub-region ids, integration with
stable regions, global imbalance from local fixes, detail-level mismatch, and
callout/zoom link correctness.

### 4. Component Fidelity
Evaluate component identity, support/mount/frame/stage, material boundaries,
wire/cable/arrow endpoints, standard missing parts, and whether omissions are
acceptable schematic simplifications.

### 5. Scientific Plausibility
Evaluate arrows, fields, flows, forces, charge motion, current, energy ordering,
scale/proximity, material/interface meaning, theory-guard invariants, and
mechanism-level label/object conflicts.

### 6. Composition and Layout
Evaluate visual hierarchy, reading path, spacing, alignment, density, white
space, relative scale, thumbnail readability, and whether the figure reads as
one coherent system instead of assembled fragments.

### 7. Label and Annotation Semantics
Evaluate every label-target audit item, terminology consistency, leader-line
necessity, label density, cross-panel label grammar, and annotation usefulness
versus clutter.

### 8. Journal Polish
Evaluate typography hierarchy, line-weight economy, palette economy, semantic
color consistency, export-scale contrast, schematic restraint, and absence of
decorative noise.

### 9. Reference Fidelity
When references exist, evaluate role/topology transfer, per-panel reference
crop comparisons, preserved key relations, intentional omissions versus
incomplete drawing, hallucinated additions, and source limitations.

### 10. Publication Readiness
Conservatively summarize whether the figure passes, needs a patch, needs human
review, or blocks release. This summary cannot be less severe than any
applicable upstream quality axis.
"""


def _journal_grade_assessment() -> str:
    return """## Journal-Grade Fresh Re-Audit Assessment

After completing `quality_axes`, classify the current rendered/exported figure
under top-level YAML field `journal_grade_assessment`. This is not a progress
score. Re-audit the current artifact from scratch: earlier pass states can be
downgraded when a later patch introduces a new layout, story, label, or polish
regression.

Use `high_impact_candidate` only when all applicable upstream `quality_axes`
are passing, no human gate is required, and the current artifact reads above
ordinary manuscript quality. Use `needs_human_art_direction` when the remaining
decision is taste, story framing, target-journal fit, policy, or visual
direction that should not be decided by automation.
"""


def _quality_axis_schema(axis_name: str, *, evidence: str, rationale: str) -> str:
    return "\n".join(
        [
            f"  {axis_name}:",
            f"    verdict: {_QUALITY_VERDICT_VALUES}",
            f"    confidence: {_QUALITY_CONFIDENCE_VALUES}",
            f"    rationale: \"<{rationale}>\"",
            f"    evidence: \"<{evidence}>\"",
            "    blocking_items: []",
            f"    recommended_action: {_QUALITY_ACTION_VALUES}",
        ]
    )


def _quality_axes_schema() -> str:
    axis_schema = {
        "message_storyline": _quality_axis_schema(
            "message_storyline",
            rationale="message/story verdict rationale",
            evidence="visible evidence, briefing/spec reference, or finding id",
        ),
        "panel_role_coherence": "\n".join(
            [
                "  panel_role_coherence:",
                f"    verdict: {_QUALITY_VERDICT_VALUES}",
                f"    confidence: {_QUALITY_CONFIDENCE_VALUES}",
                "    rationale: \"<panel role coherence summary>\"",
                "    evidence: \"<panel ids and visual evidence>\"",
                "    panel_roles:",
                "      - panel_id: \"<id>\"",
                f"        role: {_PANEL_ROLE_VALUES}",
                f"        role_quality: {_PANEL_ROLE_QUALITY_VALUES}",
                "        rationale: \"<one-line>\"",
                "    blocking_items: []",
                f"    recommended_action: {_QUALITY_ACTION_VALUES}",
            ]
        ),
        "subregion_integration": _quality_axis_schema(
            "subregion_integration",
            rationale="sub-region/global integration summary",
            evidence="subregion id, log evidence, or visible evidence",
        ),
        "component_fidelity": _quality_axis_schema(
            "component_fidelity",
            rationale="component fidelity summary",
            evidence="component audit ids or visible evidence",
        ),
        "scientific_plausibility": _quality_axis_schema(
            "scientific_plausibility",
            rationale="scientific plausibility summary",
            evidence="theory guard, briefing invariant, or visible evidence",
        ),
        "composition_layout": _quality_axis_schema(
            "composition_layout",
            rationale="layout/composition summary",
            evidence="visible evidence, checker output, or finding id",
        ),
        "label_annotation_semantics": _quality_axis_schema(
            "label_annotation_semantics",
            rationale="label semantics summary",
            evidence="label-target audit ids or visible evidence",
        ),
        "journal_polish": _quality_axis_schema(
            "journal_polish",
            rationale="polish summary",
            evidence="visible evidence or export-scale issue",
        ),
        "reference_fidelity": _quality_axis_schema(
            "reference_fidelity",
            rationale="reference fidelity summary",
            evidence="reference path, panel id, or reference_pack note",
        ),
        "publication_readiness": _quality_axis_schema(
            "publication_readiness",
            rationale="conservative readiness summary",
            evidence="axis verdict summary",
        ),
    }
    return "quality_axes:\n" + "\n".join(
        axis_schema[axis_name] for axis_name in _QUALITY_AXIS_NAMES
    )


def _journal_grade_assessment_schema(critique_input_hash: str) -> str:
    return "\n".join(
        [
            "journal_grade_assessment:",
            "  schema: figure-agent.journal-grade-assessment.v1",
            "  scoring_mode: fresh_reaudit",
            f"  assessed_artifact_hash: {critique_input_hash}",
            (
                "  benchmark_level: draft | solid_manuscript | "
                "high_impact_candidate | needs_human_art_direction | blocked"
            ),
            f"  confidence: {_QUALITY_CONFIDENCE_VALUES}",
            "  blockers: []",
            "  regression_detected: true | false",
            "  regressions: []",
            "  score_is_gateable: true | false",
            (
                "  next_quality_bottleneck: storyline | composition | "
                "component_fidelity | scientific_plausibility | label_semantics | "
                "polish | reference_fidelity | export_scale_readability | human_policy"
            ),
            '  rationale: "<current artifact-only quality rationale>"',
        ]
    )


def _panel_reference_sections(
    example_dir: Path, spec: dict, png_path: Path, pdf_path: Path
) -> tuple[str, str]:
    contexts: list[str] = []
    warnings: list[str] = []
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

{_mandatory_audit_checklists()}

{_journal_quality_axes()}

{_journal_grade_assessment()}

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
(YAML front-matter then human-readable Markdown body — schema v1.2):

```markdown
---
schema: figure-agent.critique.v1.2
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
    - check: {_PHYSICAL_CHECK_VALUES}
      finding: "<what was observed>"
      verdict: convention_acceptable | structural_defect
  conceptual_completeness:
    - element: <name>
      reference: provided_reference | briefing | reference_pack | not_provided
      severity: BLOCKER | MAJOR | MINOR | NIT
      proposed_action: add | expand | accept_simplification
{_quality_axes_schema()}
{_journal_grade_assessment_schema(critique_input_hash)}
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

Every `needs_patch` and `block` quality axis must expose a concrete
`blocking_items` entry and either a normal panel/top-level finding or a
non-patch `recommended_action` such as `human_review`, `revise_briefing`, or
`block_release`. For `patch` or `block_release` actions, include the linked
finding id in the relevant `blocking_items` entry, e.g. `C001 - <reason>`.
`publication_readiness.verdict` must not be less severe than any applicable
upstream quality axis.

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
