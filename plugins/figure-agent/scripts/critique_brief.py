"""Emit the L4.5 vision-critique brief from briefing.md + TikZ + rendered PNG.

Produces the prompt-context block consumed by the `/fig_critique <name>` slash
command. The host Claude Code main loop reads the brief together with the
build PNG (via the Read tool) and writes the structured critique to
`examples/<name>/critique.md` (YAML front-matter + Markdown summary, schema
v1.10). No external API is called; the brief itself is API-free.

Successor to the v0.1 `review_brief.py` (HALT-then-paste workflow); see
`docs/architecture-v0.2-proposal.md` §4.5 for the rename + extend rationale.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import critique_brief_sections as brief_sections
from aesthetic_intent import (
    AESTHETIC_INTENT_SCHEMA_V2,
    AestheticIntentError,
    load_optional_aesthetic_intent,
)
from critique_reference_pack import CritiqueReferencePackError, load_optional_reference_pack
from critique_zoom_crops import build_zoom_crop_pack
from external_vision_review import (
    ExternalVisionReviewError,
    load_optional_external_vision_review,
)
from inputs import parse_briefing, parse_spec
from journal_art_direction_playbook import (
    JournalArtDirectionPlaybookError,
    journal_playbook_anchors,
    load_optional_journal_art_direction_playbook,
)
from paper_aesthetic_context import (
    PaperAestheticContextError,
    load_optional_paper_aesthetic_context,
    matching_figure_role,
    paper_context_anchors,
)
from PIL import Image
from quality_manifest import (
    CRITIQUE_RUBRIC_VERSION,
    CRITIQUE_RUBRIC_VERSION_V1_14,
    CRITIQUE_RUBRIC_VERSION_V1_16,
    compute_critique_input_hash,
    critique_generator_version,
    file_sha256,
)
from reference_aesthetic_metrics import reference_aesthetic_metrics_summary
from reference_contract import compute_reference_input_failures, declared_figure_reference_path
from subregion_active_set import active_subregion_ids, iteration_patch_ids, parse_active_target_rows
from svg_polish_delta import (
    SVG_POLISH_DELTA_MANIFEST_RELATIVE_PATH,
    SvgPolishDeltaError,
    load_svg_polish_delta_manifest,
    svg_polish_delta_is_stale,
)

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
    "label_stacked_on_reference_line",
    "label_curve_near_label",
    "label_path_near_miss",
)
_MICRO_DEFECT_KIND_SCHEMA = (
    "line_crosses_label | wire_crosses_label | arrow_tip_fused | "
    "label_target_detached | floating_semantic_cue | drawing_order_suspect | "
    "print_scale_unreadable | label_backdrop_overflows_outline | "
    "label_glyph_overlaps_internal_drawing | label_crosses_panel_boundary | "
    "label_crosses_column_rule | label_overflows_row_box | "
    "label_stacked_on_reference_line | label_curve_near_label | "
    "label_path_near_miss"
)
_CRITIQUE_SCHEMA_VERSION = "figure-agent.critique.v1.10"
_CRITIQUE_SCHEMA_VERSION_V1_14 = "figure-agent.critique.v1.14"
_CRITIQUE_SCHEMA_VERSION_V1_16 = "figure-agent.critique.v1.16"


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
    crops = [
        crop
        for crop in crops
        if crop.get("kind") in {"zoom_crop", "visual_clash_crop", "label_path_crop"}
    ]
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
        crop_line = (
            f"- `{_example_relative_path(example_dir, crop_path)}` "
            f"from `{_example_relative_path(example_dir, source_path)}` "
            f"bbox_px={crop['bbox_px']}"
        )
        if crop.get("kind") == "visual_clash_crop":
            crop_line += f" visual_clash_ref=`{crop.get('visual_clash_ref', '')}`"
        if crop.get("kind") == "label_path_crop":
            crop_line += f" label_path_ref=`{crop.get('label_path_ref', '')}`"
        lines.append(crop_line)
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


def _reference_calibration_section(pack: dict | None) -> str:
    if pack is None:
        return ""
    lines = [
        "## Reference-Calibrated Top-Tier Comparison",
        "Host LLM MUST use this pack to calibrate journal-level critique. Evaluate every "
        "must-match trait, must-avoid trait, and calibration question below.",
        f"- Target journal: {pack['target_journal']}",
        f"- Reference class: {pack['reference_class']}",
        f"- Visual ambition: {pack['visual_ambition']}",
        "",
        "### Comparison References",
    ]
    for item in pack.get("comparison_references", []):
        lines.append(
            f"- {item['id']}: source={item['source']} role={item['role']} "
            f"citation/path={item['path_or_citation']}"
        )
    lines.append("")
    lines.append("### Must-Match Traits")
    for item in pack.get("must_match_traits", []):
        lines.append(f"- {item['id']} -> {item['reference_id']}: {item['trait']}")
    lines.append("")
    lines.append("### Must-Avoid Traits")
    for item in pack.get("must_avoid_traits", []):
        lines.append(f"- {item['id']} severity={item['severity']}: {item['trait']}")
    lines.append("")
    lines.append("### Calibration Questions")
    for item in pack.get("calibration_questions", []):
        lines.append(f"- {item['id']}: {item['question']}")
    return "\n" + "\n".join(lines) + "\n"


def _reference_learning_section(pack: dict | None) -> str:
    if pack is None:
        return ""
    learning = pack.get("reference_learning")
    if not isinstance(learning, dict):
        return ""
    lines = [
        "## Reference Learning Contract",
        "References are learning sources, not copy targets.",
        "`briefing.md`, theory guards, fixture semantics, and author intent outrank "
        "reference style. Learn only the allowed transfer items below; do not copy "
        "forbidden structure, hardware, layout, or physics.",
        "",
    ]
    for item in learning.get("references", []):
        roles = ", ".join(item.get("roles", []))
        allowed = "; ".join(item.get("allowed_transfer", []))
        forbidden = "; ".join(item.get("forbidden_transfer", []))
        lines.extend(
            [
                f"### `{item['path']}`",
                f"- roles={roles}",
                f"- Allowed transfer: {allowed}",
                f"- Forbidden transfer: {forbidden}",
                f"- Rationale: {item['rationale']}",
                "",
            ]
        )
    return "\n" + "\n".join(lines).rstrip() + "\n"


def _reference_aesthetic_metrics_section(example_dir: Path) -> str:
    summary = reference_aesthetic_metrics_summary(example_dir)
    if summary is None:
        return ""
    lines = [
        "## Reference Aesthetic Metrics",
        "Non-model aesthetic-class measurements are advisory anchors, not copy-target "
        "requirements. Use them to explain palette, density, silhouette, or line-density "
        "divergence from allowed reference-learning traits.",
        f"- Evaluation state: {summary['evaluation_state']}",
        f"- Evidence path: `{summary['evidence_path']}`",
        f"- Comparison count: {summary['comparison_count']}",
        f"- Severe metric count: {summary['severe_metric_count']}",
    ]
    blocking_items = summary.get("blocking_items") or []
    if blocking_items:
        lines.append("- Blocking items: " + ", ".join(f"`{item}`" for item in blocking_items))
    severe_metrics = summary.get("severe_metrics") or []
    if severe_metrics:
        lines.append("")
        lines.append("Severe metrics to explain or route:")
        for item in severe_metrics:
            lines.append(
                "- {reference_path} {metric}: value={value} threshold={threshold}".format(
                    **item
                )
            )
    warning_metrics = summary.get("warning_metrics") or []
    if warning_metrics:
        lines.append("")
        lines.append("Warning metrics to consider:")
        for item in warning_metrics:
            lines.append(
                "- {reference_path} {metric}: value={value} threshold={threshold}".format(
                    **item
                )
            )
    next_action = summary.get("next_action")
    if next_action:
        lines.append(f"- Next action: {next_action}")
    return "\n" + "\n".join(lines) + "\n"


def _external_vision_review_section(review: dict | None) -> str:
    if review is None:
        return ""
    artifact = review.get("reviewed_artifact")
    artifact_path = artifact.get("path") if isinstance(artifact, dict) else ""
    lines = [
        "## External Second-Opinion Vision Review",
        "",
        "Optional imported evidence from a human or outer-agent vision pass.",
        "This evidence can reveal blind spots, but it is not higher authority than",
        "the host critique. Conflicts must route to human review; do not auto-apply",
        "external suggestions or mutate source/accepted/golden/export state.",
        "",
        f"- Reviewer: {review['reviewer']}",
        f"- Reviewed at: {review['reviewed_at']}",
        f"- Confidence: {review['confidence']}",
        f"- Reviewed artifact: `{artifact_path}`",
        "",
        "Findings:",
    ]
    for item in review.get("findings", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            "- {id} [{severity}] {observation} "
            "(evidence={evidence_ref}; action={suggested_action})".format(
                id=item.get("id", ""),
                severity=item.get("severity", ""),
                observation=item.get("observation", ""),
                evidence_ref=item.get("evidence_ref", ""),
                suggested_action=item.get("suggested_action", ""),
            )
        )
    conflicts = [item for item in review.get("conflicts", []) if isinstance(item, dict)]
    if conflicts:
        lines.extend(["", "Conflicts:"])
        for item in conflicts:
            lines.append(
                "- external {external} vs host {host}: {summary}".format(
                    external=item.get("external_finding_id", ""),
                    host=item.get("host_finding_id", ""),
                    summary=item.get("summary", ""),
                )
            )
        lines.append("")
        lines.append("Conflicts must route to human review; do not pick a winner silently.")
    return "\n" + "\n".join(lines) + "\n"


def _paper_aesthetic_context_section(
    pack: dict | None,
    *,
    fixture: str,
) -> str:
    if pack is None:
        return ""
    role = matching_figure_role(pack, fixture)
    must_align_with = role.get("must_align_with", [])
    allowed_variations = role.get("allowed_variations", [])
    shared_items = {
        item["id"]: item
        for item in pack.get("shared_visual_language", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    lines = [
        "## Paper-Wide Aesthetic Context",
        "Host LLM MUST evaluate whether this figure remains coherent with the declared "
        "paper-wide visual language. The critique must cite exact paper context anchors "
        "in `top_tier_audit.cross_panel_semantic_grammar`, "
        "`top_tier_audit.aesthetic_coherence`, and "
        "`editorial_art_direction.visual_identity`.",
        "Each of those three critique slots must cite at least one exact paper-wide "
        "anchor from the target fields, matching role, shared-language ids, or "
        "must-avoid ids below; generic art-direction prose is invalid.",
        f"- Paper id: {pack['paper_id']}",
        f"- Target journal: {pack['target_journal']}",
        f"- Visual maturity: {pack['visual_maturity']}",
        f"- Density: {pack['density']}",
        f"- Figure role: {role['role']}",
        "",
        "### Required Shared Visual Language",
    ]
    for item_id in must_align_with:
        item = shared_items[item_id]
        lines.append(
            f"- {item['id']} priority={item['priority']} "
            f"dimension={item['dimension']}: {item['instruction']}"
        )
    if allowed_variations:
        lines.append("")
        lines.append("### Allowed Role Variations")
        for item in allowed_variations:
            lines.append(f"- {item}")
    lines.append("")
    lines.append("### Paper-Wide Must-Avoid Patterns")
    for item in pack.get("must_avoid", []):
        lines.append(f"- {item['id']} severity={item['severity']}: {item['pattern']}")
    anchors = sorted(paper_context_anchors(pack, fixture))
    role_anchor_text = ", ".join(must_align_with)
    lines.extend(
        [
            "",
            "### Exact Paper-Wide Anchors",
            f"- Required anchors from matching role: {role_anchor_text}",
            f"- Full accepted anchor set: {', '.join(anchors)}",
        ]
    )
    return "\n" + "\n".join(lines) + "\n"


def _journal_art_direction_playbook_section(pack: dict | None) -> str:
    if pack is None:
        return ""
    lines = [
        "## Journal Art-Direction Playbook",
        "Host LLM MUST use this playbook as the journal-level taste vocabulary "
        "for the current critique. Generic claims such as \"looks polished\" are "
        "invalid unless they cite exact playbook anchors and current-artifact evidence.",
        "The critique must cite exact playbook anchors in `top_tier_audit`, "
        "`editorial_art_direction`, `journal_grade_assessment.rationale`, and "
        "`journal_art_direction_playbook_audit`.",
        f"- Playbook id: {pack['playbook_id']}",
        f"- Target journal: {pack['target_journal']}",
        f"- Venue context: {pack['venue_context']}",
        f"- Visual maturity: {pack['visual_maturity']}",
        "",
        "### Design Center",
    ]
    for item in pack.get("design_center", []):
        lines.extend(
            [
                (
                    f"- {item['id']} priority={item['priority']} "
                    f"dimension={item['dimension']}: {item['instruction']}"
                ),
                f"  positive_signals: {'; '.join(item['positive_signals'])}",
                f"  anti_patterns: {'; '.join(item['anti_patterns'])}",
                f"  evidence_prompts: {'; '.join(item['evidence_prompts'])}",
            ]
        )
    lines.append("")
    lines.append("### Anti-Patterns")
    for item in pack.get("anti_patterns", []):
        lines.append(
            f"- {item['id']} severity={item['severity']} "
            f"route={item['preferred_route']}: {item['pattern']}"
        )
    lines.append("")
    lines.append("### Positive Signals")
    for item in pack.get("positive_signals", []):
        lines.append(f"- {item['id']} dimension={item['dimension']}: {item['signal']}")
        lines.append(f"  evidence_prompt: {item['evidence_prompt']}")
    lines.append("")
    lines.append("### Polish Route Rules")
    for item in pack.get("polish_route_rules", []):
        lines.append(f"- {item['id']} path={item['recommended_path']}: {item['condition']}")
        lines.append(f"  forbidden_actions: {'; '.join(item['forbidden_actions'])}")
    lines.append("")
    lines.append("### Human Review Triggers")
    for item in pack.get("human_review_triggers", []):
        lines.append(f"- {item['id']} severity={item['severity']}: {item['condition']}")
    anchors = sorted(journal_playbook_anchors(pack))
    required_ids = ", ".join(item["id"] for item in pack.get("design_center", []))
    lines.extend(
        [
            "",
            "### Exact Playbook Anchors",
            f"- Required design_center ids: {required_ids}",
            f"- Full accepted anchor set: {', '.join(anchors)}",
        ]
    )
    return "\n" + "\n".join(lines) + "\n"


def _svg_polish_delta_section(example_dir: Path) -> str:
    manifest_path = example_dir / SVG_POLISH_DELTA_MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        return ""
    try:
        manifest = load_svg_polish_delta_manifest(manifest_path, example_dir=example_dir)
        if svg_polish_delta_is_stale(manifest_path, example_dir=example_dir):
            raise CritiqueBriefError(
                "SVG polish aesthetic delta pack is stale; regenerate it before critique"
            )
    except SvgPolishDeltaError as exc:
        raise CritiqueBriefError(f"SVG polish aesthetic delta invalid: {exc}") from exc
    artifacts = manifest["artifacts"]
    operation_ids = ", ".join(manifest["operation_ids"])
    lines = [
        "## SVG Polish Aesthetic Delta",
        "Host LLM MUST compare the before/after polish images before treating SVG "
        "polish as an improvement.",
        f"- before: `{artifacts['before_png']}`",
        f"- after: `{artifacts['after_png']}`",
        f"- diff: `{artifacts['diff_png']}`",
        f"- recipe: `{manifest['recipe']}`",
        f"- operation_ids: {operation_ids}",
        f"- source_svg_hash: `{manifest['source_svg_hash']}`",
        f"- polished_svg_hash: `{manifest['polished_svg_hash']}`",
        f"- recipe_hash: `{manifest['recipe_hash']}`",
        "",
        "Questions the critique must answer:",
        "- Did journal polish improve?",
        "- Did any label/readability/spacing issue regress?",
        "- Did any scientific semantics change?",
        "- Should the route remain SVG polish, return to TikZ, or require human art direction?",
    ]
    return "\n" + "\n".join(lines) + "\n"


def _svg_polish_delta_audit_schema(include_delta_audit: bool) -> str:
    if not include_delta_audit:
        return ""
    return """svg_polish_delta_audit:
  evaluation_state: <improved | no_meaningful_change | regressed |
    needs_human_art_direction | invalid>
  read_all_delta_images: true
  delta_image_audit_log:
    - image_id: before
      path: polish/aesthetic_delta/before.png
      verdict: inspected
      observed_objects: ["<object names visible in before image>"]
      local_relationship: "<relative position or clearance observed in before image>"
      delta_focus: "<what changed or should remain unchanged in before>"
      observation: "<specific current-artifact evidence from before image>"
    - image_id: after
      path: polish/aesthetic_delta/after.png
      verdict: inspected
      observed_objects: ["<object names visible in after image>"]
      local_relationship: "<relative position or clearance observed in after image>"
      delta_focus: "<what changed or should remain unchanged in after>"
      observation: "<specific current-artifact evidence from after image>"
    - image_id: diff
      path: polish/aesthetic_delta/diff.png
      verdict: inspected
      observed_objects: ["<delta pixel/object names visible in diff image>"]
      local_relationship: "<where the diff pixels sit relative to labels/marks>"
      delta_focus: "<localized change visible in diff>"
      observation: "<specific current-artifact evidence from diff image>"
  compared_inputs: [before, after, diff]
  improvements:
    - "<specific improvement, or empty when not improved>"
  regressions:
    - category: <semantic_drift | label_readability | crop_regression |
        print_scale_regression | overdecorated | journal_mismatch>
      evidence: "<crop/diff/reference evidence>"
      severity: BLOCKER | MAJOR | MINOR | NIT
      linked_finding_id: "<finding id, or empty only for non-blocking route>"
  route_after_delta: <continue_svg_polish | accept_svg_polish |
    semantic_backport_required | needs_human_art_direction>
  rationale: "<why this route is chosen; accept_svg_polish is delta-local, not release approval>"
"""


def _aesthetic_gate_audit_schema(include_gate: bool) -> str:
    if not include_gate:
        return ""
    return """aesthetic_gate_audit:
  - slot: maturity_restraint | visual_hierarchy | template_genericness |
      overdecorated_or_cartoonish | journal_fit | handcrafted_finish |
      semantic_preservation | print_scale_finish | paper_wide_coherence
    verdict: pass | weak | fail | needs_human
    route: pass | tikz_patch | svg_polish | semantic_backport |
      needs_human_art_direction | accept_simplification
    evidence: "<specific current-artifact evidence; generic 'looks polished' prose is invalid>"
    rationale: "<why this slot takes the selected route>"
    linked_evidence:
      - svg_polish_delta_audit.delta_image_audit_log |
        top_tier_audit.<slot> | editorial_art_direction.<slot> | finding id
"""


def _reference_score_calibration(
    example_dir: Path,
    pack: dict | None,
) -> dict[str, str] | None:
    if pack is None:
        return None
    return {
        "reference_pack_hash": file_sha256(example_dir / "critique_reference_pack.yaml"),
        "reference_class": pack["reference_class"],
        "visual_ambition": pack["visual_ambition"],
    }


def _aesthetic_intent_section(pack: dict | None) -> str:
    if pack is None:
        return ""
    if pack.get("schema") == AESTHETIC_INTENT_SCHEMA_V2:
        return _aesthetic_lever_grammar_section(pack)
    lines = [
        "## Aesthetic Intent Calibration",
        "Host LLM MUST apply this fixture-specific aesthetic target when filling "
        "`top_tier_audit.aesthetic_coherence`, "
        "`editorial_art_direction.visual_identity`, "
        "`editorial_art_direction.aesthetic_risk`, and "
        "`editorial_art_direction.tikz_vs_svg_polish_trigger`.",
        "Each of those four critique slots must cite at least one exact aesthetic intent "
        "anchor from the target fields or item ids below; generic style prose is invalid.",
        f"- Target journal: {pack['target_journal']}",
        f"- Visual maturity: {pack['visual_maturity']}",
        f"- Density: {pack['density']}",
        f"- Reference style: {pack['reference_style']}",
        "",
        "### Design Principles",
    ]
    for item in pack.get("design_principles", []):
        lines.append(f"- {item['id']}: {item['instruction']}")
    lines.append("")
    lines.append("### Must-Avoid Patterns")
    for item in pack.get("must_avoid", []):
        lines.append(f"- {item['id']} severity={item['severity']}: {item['pattern']}")
    lines.append("")
    lines.append("### Polish Triggers")
    for item in pack.get("polish_triggers", []):
        lines.append(f"- {item['id']} path={item['recommended_path']}: {item['condition']}")
    return "\n" + "\n".join(lines) + "\n"


def _aesthetic_lever_grammar_section(pack: dict) -> str:
    lines = [
        "## Aesthetic Lever Grammar (host LLM MUST enumerate)",
        "The fixture declares aesthetic intent schema v2. You MUST fill top-level YAML "
        "field `aesthetic_lever_audit` with exactly one entry for every declared lever id.",
        'Generic prose such as "improve polish" is invalid unless it is tied to a '
        "lever id, observed evidence, allowed adjustment, forbidden guard, and route.",
        "For non-passing levers, `observed_anti_patterns` must be non-empty and "
        "`route` must match the lever's declared default_route. Route overrides are "
        "not part of schema v1.14.",
        "`svg_polish` requires the editorial polish trigger to recommend "
        "`ready_for_svg_polish`; `semantic_backport` requires that same trigger to "
        "recommend `semantic_backport_required`; `human_art_direction` must cite "
        "`editorial_art_direction.human_art_direction_gate`.",
        "The v1 aesthetic anchor-citation rule still applies to "
        "`top_tier_audit.aesthetic_coherence`, "
        "`editorial_art_direction.visual_identity`, "
        "`editorial_art_direction.aesthetic_risk`, and "
        "`editorial_art_direction.tikz_vs_svg_polish_trigger`.",
        f"- Target journal: {pack['target_journal']}",
        f"- Visual maturity: {pack['visual_maturity']}",
        f"- Density: {pack['density']}",
        f"- Reference style: {pack['reference_style']}",
        "",
        "### Design Principles",
    ]
    for item in pack.get("design_principles", []):
        lines.append(f"- {item['id']}: {item['instruction']}")
    lines.append("")
    lines.append("### Must-Avoid Patterns")
    for item in pack.get("must_avoid", []):
        lines.append(f"- {item['id']} severity={item['severity']}: {item['pattern']}")
    lines.append("")
    lines.append("### Polish Triggers")
    for item in pack.get("polish_triggers", []):
        lines.append(f"- {item['id']} path={item['recommended_path']}: {item['condition']}")
    lines.append("")
    lines.append("### Declared Aesthetic Levers")
    for item in pack.get("aesthetic_levers", []):
        lines.extend(
            [
                (
                    f"- {item['id']}: dimension={item['dimension']} "
                    f"priority={item['priority']} route={item['default_route']}"
                ),
                f"  intent: {item['intent']}",
                f"  positive_signals: {'; '.join(item['positive_signals'])}",
                f"  anti_patterns: {'; '.join(item['anti_patterns'])}",
                f"  allowed_adjustments: {'; '.join(item['allowed_adjustments'])}",
                f"  forbidden_adjustments: {'; '.join(item['forbidden_adjustments'])}",
            ]
        )
    return "\n" + "\n".join(lines) + "\n"


def _uses_aesthetic_lever_schema(pack: dict | None) -> bool:
    return bool(pack and pack.get("schema") == AESTHETIC_INTENT_SCHEMA_V2)


def _aesthetic_lever_audit_schema(pack: dict | None) -> str:
    if not _uses_aesthetic_lever_schema(pack):
        return ""
    dimension_values = (
        "maturity | hero_hierarchy | whitespace_breathing | typography_authority | "
        "color_harmony | line_weight_rhythm | component_fidelity | hand_craft | "
        "cross_panel_grammar | polish_route"
    )
    evidence_values = (
        "top_tier_audit.* | editorial_art_direction.* | quality_axes.* | "
        "micro_defects.* | finding id"
    )
    return f"""aesthetic_lever_audit:
  - lever_id: <id from aesthetic_intent.yaml aesthetic_levers[]>
    dimension: {dimension_values}
    verdict: pass | weak | fail | needs_human | not_applicable
    confidence: low | medium | high
    observed_positive_signals:
      - "<current-artifact positive signal>"
    observed_anti_patterns:
      - "<current-artifact anti-pattern, or empty only for pass/not_applicable>"
    route: none | tikz_patch | svg_polish | semantic_backport | human_art_direction
    linked_evidence:
      - "<{evidence_values}>"
    allowed_next_adjustment: "<one bounded adjustment, or empty when route=none>"
    forbidden_adjustment_guard: "<semantic guard from the declared lever>"
    rationale: "<why this verdict and route follow from the declared lever>"
"""


def _journal_art_direction_playbook_audit_schema(pack: dict | None) -> str:
    if pack is None:
        return ""
    design_center_ids = " | ".join(item["id"] for item in pack.get("design_center", []))
    positive_signal_ids = " | ".join(item["id"] for item in pack.get("positive_signals", []))
    anti_pattern_ids = " | ".join(item["id"] for item in pack.get("anti_patterns", []))
    route_rule_ids = " | ".join(item["id"] for item in pack.get("polish_route_rules", []))
    human_trigger_ids = " | ".join(item["id"] for item in pack.get("human_review_triggers", []))
    route_values = (
        "none | continue_tikz | ready_for_svg_polish | "
        "semantic_backport_required | needs_human_art_direction"
    )
    evidence_values = (
        "top_tier_audit.* | editorial_art_direction.* | "
        "journal_grade_assessment.rationale | finding id"
    )
    recommended_path_values = (
        "continue_tikz | ready_for_svg_polish | semantic_backport_required | "
        "needs_human_art_direction"
    )
    return f"""journal_art_direction_playbook_audit:
  schema: figure-agent.journal-art-direction-playbook-audit.v1
  playbook_id: {pack['playbook_id']}
  venue_context: {pack['venue_context']}
  design_center:
    - id: {design_center_ids}
      verdict: pass | weak | fail | needs_human | not_applicable
      evidence: "<current artifact evidence tied to exact playbook anchors>"
      positive_signal_refs:
        - "{positive_signal_ids}"
      anti_pattern_refs:
        - "{anti_pattern_ids}"
      route: {route_values}
      linked_evidence:
        - "{evidence_values}"
      rationale: "<why this verdict follows from the playbook>"
  route_rule_applied:
    id: {route_rule_ids}
    recommended_path: {recommended_path_values}
    rationale: "<why this route wins without bypassing loop/driver gates>"
  human_review_triggers:
    - id: {human_trigger_ids}
      active: true | false
      rationale: "<why active, or why not active>"
"""


def _format_metric(metric: object) -> str:
    if not isinstance(metric, dict) or not metric:
        return "(none)"
    parts: list[str] = []
    for key in sorted(metric):
        value = metric[key]
        if isinstance(value, int | float):
            parts.append(f"{key}={value:g}")
        else:
            parts.append(f"{key}={value}")
    return ", ".join(parts)


def _candidate_sort_key(candidate: dict) -> tuple[str, str, str, list[int]]:
    bbox = candidate.get("bbox_px")
    bbox_key = bbox if isinstance(bbox, list) else []
    return (
        str(candidate.get("id") or ""),
        str(candidate.get("kind") or ""),
        str(candidate.get("text") or ""),
        bbox_key,
    )


def _visual_clash_candidates_section(example_dir: Path) -> str:
    report_path = example_dir / "build" / "visual_clash.json"
    if not report_path.is_file():
        return ""
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (
            "\n## Visual Clash Candidates (from check_visual_clash.py)\n"
            f"WARN: `{_example_relative_path(example_dir, report_path)}` is malformed JSON: {exc}\n"
        )
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return (
            "\n## Visual Clash Candidates (from check_visual_clash.py)\n"
            f"WARN: `{_example_relative_path(example_dir, report_path)}` has no candidates list.\n"
        )
    total = report.get("total", len(candidates))
    crop_by_ref = _visual_clash_crop_paths_by_ref(example_dir)
    lines = [
        "## Visual Clash Candidates (from check_visual_clash.py)",
        "Host LLM MUST review each candidate. For each, either link to a new/existing "
        "`micro_defects` entry via `visual_clash_ref` or explicitly justify "
        "`status: accept_simplification`.",
        "Use `label_backdrop_overflows_outline` when a label fill/backdrop protrudes "
        "past its enclosing instrument-box outline.",
        "Use `label_glyph_overlaps_internal_drawing` when a label glyph or backdrop "
        "collides with an internal mark inside the same box.",
        f"- Source JSON: `{_example_relative_path(example_dir, report_path)}`",
        f"- Total candidates from JSON: {total}",
        "",
    ]
    for candidate in sorted(
        (item for item in candidates if isinstance(item, dict)),
        key=_candidate_sort_key,
    ):
        bbox = candidate.get("bbox_px")
        tex_lines = candidate.get("tex_lines")
        tex_display = tex_lines if isinstance(tex_lines, list) else "null"
        candidate_id = str(candidate.get("id", ""))
        crop_path = crop_by_ref.get(candidate_id)
        crop_display = f" crop=`{crop_path}`" if crop_path else ""
        lines.append(
            f"- id=`{candidate_id}` "
            f"kind=`{candidate.get('kind', '')}` text=`{candidate.get('text', '')}` "
            f"bbox_px={bbox} metric={_format_metric(candidate.get('metric'))} "
            f"tex_lines={tex_display}{crop_display}"
        )
    return "\n" + "\n".join(lines) + "\n"


def _text_boundary_candidate_sort_key(candidate: dict) -> tuple[str, str, str, str]:
    return (
        str(candidate.get("id") or ""),
        str(candidate.get("boundary_id") or ""),
        str(candidate.get("kind") or ""),
        str(candidate.get("text") or ""),
    )


def _text_boundary_clash_candidates_section(example_dir: Path) -> str:
    report_path = example_dir / "build" / "text_boundary_clash.json"
    if not report_path.is_file():
        return ""
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (
            "\n## Text Boundary Clash Candidates (from check_text_boundary_clash.py)\n"
            f"WARN: `{_example_relative_path(example_dir, report_path)}` is malformed JSON: {exc}\n"
        )
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return (
            "\n## Text Boundary Clash Candidates (from check_text_boundary_clash.py)\n"
            f"WARN: `{_example_relative_path(example_dir, report_path)}` has no candidates list.\n"
        )
    if not candidates:
        return ""
    total = report.get("total", len(candidates))
    lines = [
        "## Text Boundary Clash Candidates (from check_text_boundary_clash.py)",
        "Host LLM MUST review each text-boundary candidate. For each, either link "
        "to a new/existing `micro_defects` entry via `text_boundary_ref` or "
        "explicitly justify `status: accept_simplification`.",
        "Use `label_crosses_column_rule` for text crossing panel column rules.",
        "Use `label_crosses_panel_boundary` for text crossing panel or row boundary lines.",
        "Use `label_overflows_row_box` for text outside a containing row/panel box.",
        f"- Source JSON: `{_example_relative_path(example_dir, report_path)}`",
        f"- Total candidates from JSON: {total}",
        "",
    ]
    for candidate in sorted(
        (item for item in candidates if isinstance(item, dict)),
        key=_text_boundary_candidate_sort_key,
    ):
        lines.append(
            f"- id=`{candidate.get('id', '')}` "
            f"kind=`{candidate.get('kind', '')}` text=`{candidate.get('text', '')}` "
            f"boundary_id=`{candidate.get('boundary_id', '')}` "
            f"boundary_role=`{candidate.get('boundary_role', '')}` "
            f"bbox_pt={candidate.get('bbox_pt')} "
            f"boundary_pt={candidate.get('boundary_pt')} "
            f"clearance_pt={candidate.get('clearance_pt')}"
        )
    return "\n" + "\n".join(lines) + "\n"


def _label_path_candidate_sort_key(candidate: dict) -> tuple[str, str, str, str]:
    return (
        str(candidate.get("id") or ""),
        str(candidate.get("path_id") or ""),
        str(candidate.get("kind") or ""),
        str(candidate.get("text") or ""),
    )


def _label_path_proximity_candidates_section(example_dir: Path) -> str:
    report_path = example_dir / "build" / "label_path_proximity.json"
    if not report_path.is_file():
        return ""
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (
            "\n## Label-Path Proximity Candidates (from check_label_path_proximity.py)\n"
            f"WARN: `{_example_relative_path(example_dir, report_path)}` is malformed JSON: {exc}\n"
        )
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return (
            "\n## Label-Path Proximity Candidates (from check_label_path_proximity.py)\n"
            f"WARN: `{_example_relative_path(example_dir, report_path)}` has no candidates list.\n"
        )
    if not candidates:
        return ""
    total = report.get("total", len(candidates))
    crop_by_ref = _label_path_crop_paths_by_ref(example_dir)
    lines = [
        "## Label-Path Proximity Candidates (from check_label_path_proximity.py)",
        "Host LLM MUST review each label-path proximity candidate. For each, either "
        "link to a new/existing `micro_defects` entry via `label_path_ref` or "
        "explicitly justify `status: accept_simplification`.",
        "Use `label_stacked_on_reference_line` when a label visually stacks on a "
        "declared reference/baseline without an actual bbox overlap.",
        "Use `label_curve_near_label` when a semantic curve passes too close to a label.",
        "Use `label_path_near_miss` for other declared label/path clearance failures.",
        f"- Source JSON: `{_example_relative_path(example_dir, report_path)}`",
        f"- Total candidates from JSON: {total}",
        "",
    ]
    for candidate in sorted(
        (item for item in candidates if isinstance(item, dict)),
        key=_label_path_candidate_sort_key,
    ):
        candidate_id = str(candidate.get("id", ""))
        crop_path = crop_by_ref.get(candidate_id)
        crop_display = f" crop=`{crop_path}`" if crop_path else ""
        lines.append(
            f"- id=`{candidate_id}` "
            f"kind=`{candidate.get('kind', '')}` text=`{candidate.get('text', '')}` "
            f"path_id=`{candidate.get('path_id', '')}` "
            f"path_role=`{candidate.get('path_role', '')}` "
            f"bbox_pt={candidate.get('bbox_pt')} "
            f"path_pt={candidate.get('path_pt')} "
            f"clearance_pt={candidate.get('clearance_pt')} "
            f"distance_pt={candidate.get('distance_pt')}"
            f"{crop_display}"
        )
    return "\n" + "\n".join(lines) + "\n"


def _undeclared_geometry_candidate_sort_key(candidate: dict) -> tuple[str, str, str]:
    return (
        str(candidate.get("id") or ""),
        str(candidate.get("kind") or ""),
        str(candidate.get("nearest_text") or ""),
    )


def _undeclared_geometry_candidates_section(example_dir: Path) -> str:
    report_path = example_dir / "build" / "undeclared_geometry.json"
    if not report_path.is_file():
        return ""
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (
            "\n## Undeclared Geometry Candidates (from check_undeclared_geometry.py)\n"
            f"WARN: `{_example_relative_path(example_dir, report_path)}` is malformed JSON: {exc}\n"
        )
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return (
            "\n## Undeclared Geometry Candidates (from check_undeclared_geometry.py)\n"
            f"WARN: `{_example_relative_path(example_dir, report_path)}` has no candidates list.\n"
        )
    if not candidates:
        return ""
    total = report.get("total", len(candidates))
    lines = [
        "## Undeclared Geometry Candidates (from check_undeclared_geometry.py)",
        "Host LLM MUST review each undeclared geometry candidate. For each, either "
        "link to a new/existing `micro_defects` entry via `undeclared_geometry_ref` "
        "or explicitly justify `status: accept_simplification`.",
        "Use `label_crosses_column_rule`, `label_crosses_panel_boundary`, "
        "`label_overflows_row_box`, or `label_path_near_miss` as appropriate.",
        f"- Source JSON: `{_example_relative_path(example_dir, report_path)}`",
        f"- Total candidates from JSON: {total}",
        "",
    ]
    for candidate in sorted(
        (item for item in candidates if isinstance(item, dict)),
        key=_undeclared_geometry_candidate_sort_key,
    ):
        lines.append(
            f"- id=`{candidate.get('id', '')}` "
            f"kind=`{candidate.get('kind', '')}` "
            f"nearest_text=`{candidate.get('nearest_text', '')}` "
            f"bbox_pt={candidate.get('bbox_pt')} "
            f"distance_pt={candidate.get('distance_pt')} "
            f"source_line={candidate.get('source_line')} "
            f"recommended_action=`{candidate.get('recommended_action', '')}`"
        )
    return "\n" + "\n".join(lines) + "\n"


def _visual_clash_crop_paths_by_ref(example_dir: Path) -> dict[str, str]:
    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        return {}
    result: dict[str, str] = {}
    for crop in crops:
        if not isinstance(crop, dict) or crop.get("kind") != "visual_clash_crop":
            continue
        visual_clash_ref = crop.get("visual_clash_ref")
        path = crop.get("path")
        if isinstance(visual_clash_ref, str) and isinstance(path, str):
            result[visual_clash_ref] = path
    return result


def _label_path_crop_paths_by_ref(example_dir: Path) -> dict[str, str]:
    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        return {}
    result: dict[str, str] = {}
    for crop in crops:
        if not isinstance(crop, dict) or crop.get("kind") != "label_path_crop":
            continue
        label_path_ref = crop.get("label_path_ref")
        path = crop.get("path")
        if isinstance(label_path_ref, str) and isinstance(path, str):
            result[label_path_ref] = path
    return result


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
    try:
        reference_calibration_pack = load_optional_reference_pack(example_dir)
    except CritiqueReferencePackError as exc:
        raise CritiqueBriefError(f"critique_reference_pack.yaml invalid: {exc}") from exc
    try:
        external_vision_review = load_optional_external_vision_review(example_dir, spec)
    except ExternalVisionReviewError as exc:
        raise CritiqueBriefError(f"external_vision_review.yaml invalid: {exc}") from exc
    try:
        paper_aesthetic_context_pack = load_optional_paper_aesthetic_context(
            example_dir,
            spec,
        )
    except PaperAestheticContextError as exc:
        raise CritiqueBriefError(f"paper_aesthetic_context invalid: {exc}") from exc
    try:
        journal_playbook_pack = load_optional_journal_art_direction_playbook(
            example_dir,
            spec,
        )
    except JournalArtDirectionPlaybookError as exc:
        raise CritiqueBriefError(f"journal_art_direction_playbook invalid: {exc}") from exc
    try:
        aesthetic_intent_pack = load_optional_aesthetic_intent(example_dir)
    except AestheticIntentError as exc:
        raise CritiqueBriefError(f"aesthetic_intent.yaml invalid: {exc}") from exc
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
    label_path_report_path = example_dir / "build" / "label_path_proximity.json"
    pdf_page_size_cm = (
        _pdf_page_size_cm(pdf_path)
        if panel_crop_paths or (label_path_report_path.is_file() and pdf_path.is_file())
        else None
    )
    zoom_crops = build_zoom_crop_pack(
        example_dir,
        png_path,
        panel_crop_paths=panel_crop_paths,
        spec=spec,
        pdf_page_size_cm=pdf_page_size_cm,
    )
    generator_version = critique_generator_version(Path(__file__))
    critique_input_hash = compute_critique_input_hash(
        example_dir,
        name,
        spec,
        style_lock_path=STYLE_LOCK_PATH,
    )
    zoom_audit_section = _zoom_audit_section(example_dir, zoom_crops)
    print_scale_audit_section = _print_scale_audit_section(example_dir, zoom_crops)
    visual_clash_section = _visual_clash_candidates_section(example_dir)
    text_boundary_clash_section = _text_boundary_clash_candidates_section(example_dir)
    label_path_proximity_section = _label_path_proximity_candidates_section(example_dir)
    undeclared_geometry_section = _undeclared_geometry_candidates_section(example_dir)
    reference_calibration_section = _reference_calibration_section(
        reference_calibration_pack
    )
    reference_learning_section = _reference_learning_section(reference_calibration_pack)
    reference_aesthetic_metrics_section = _reference_aesthetic_metrics_section(example_dir)
    external_vision_review_section = _external_vision_review_section(
        external_vision_review
    )
    paper_aesthetic_context_section = _paper_aesthetic_context_section(
        paper_aesthetic_context_pack,
        fixture=example_dir.name,
    )
    journal_art_direction_playbook_section = _journal_art_direction_playbook_section(
        journal_playbook_pack
    )
    aesthetic_intent_section = _aesthetic_intent_section(aesthetic_intent_pack)
    svg_polish_delta_section = _svg_polish_delta_section(example_dir)
    uses_aesthetic_lever_schema = _uses_aesthetic_lever_schema(aesthetic_intent_pack)
    uses_reference_learning_schema = isinstance(
        (reference_calibration_pack or {}).get("reference_learning"),
        dict,
    )
    uses_v1_14_contract = (
        uses_reference_learning_schema
        or journal_playbook_pack is not None
        or uses_aesthetic_lever_schema
    )
    uses_svg_polish_delta_schema = bool(svg_polish_delta_section)
    uses_grounded_observation_schema = (
        uses_svg_polish_delta_schema
        or (example_dir / "build" / "audit_crops" / "manifest.json").is_file()
        or (example_dir / "build" / "undeclared_geometry.json").is_file()
    )
    uses_route_detail_contract = uses_v1_14_contract or uses_grounded_observation_schema
    if uses_grounded_observation_schema:
        critique_schema = _CRITIQUE_SCHEMA_VERSION_V1_16
        critique_rubric_version = CRITIQUE_RUBRIC_VERSION_V1_16
        crop_anomaly_schema = """    unintended_visible_anomaly: none | present | uncertain
    anomaly_rationale: "<whether any unintended visible artifact is present>"
    anomaly_link: "<finding id, micro_defect id, or accept_simplification:<reason> when present>"
"""
        crop_anomaly_instructions = """
For each crop, also answer the inverse question: "is anything visible here that
was not intended?" Use `unintended_visible_anomaly: present` for stray bond,
unintended line continuation, accidental component grouping, misleading reference transfer,
phantom boundary or texture, or any other visible artifact not supported by
briefing/author intent. `present` anomalies must link to a
finding, micro-defect, or explicit `accept_simplification:<reason>` decision;
`uncertain` anomalies require a concrete rationale and should route to more
zoom/reference review.
"""
    elif uses_v1_14_contract:
        critique_schema = _CRITIQUE_SCHEMA_VERSION_V1_14
        critique_rubric_version = CRITIQUE_RUBRIC_VERSION_V1_14
        crop_anomaly_schema = """    unintended_visible_anomaly: none | present | uncertain
    anomaly_rationale: "<whether any unintended visible artifact is present>"
    anomaly_link: "<finding id, micro_defect id, or accept_simplification:<reason> when present>"
"""
        crop_anomaly_instructions = """
For each crop, also answer the inverse question: "is anything visible here that
was not intended?" Use `unintended_visible_anomaly: present` for stray bond,
unintended line continuation, accidental component grouping, misleading reference transfer,
phantom boundary or texture, or any other visible artifact not supported by
briefing/author intent. `present` anomalies must link to a
finding, micro-defect, or explicit `accept_simplification:<reason>` decision;
`uncertain` anomalies require a concrete rationale and should route to more
zoom/reference review.
"""
    else:
        critique_schema = _CRITIQUE_SCHEMA_VERSION
        critique_rubric_version = CRITIQUE_RUBRIC_VERSION
        crop_anomaly_schema = ""
        crop_anomaly_instructions = ""
    authoring_context_section = _optional_authoring_context(example_dir)
    render_read_note = (
        "(The slash command loads this PNG into the host main loop via the Read tool.)"
    )

    return f"""# Critique brief — {name}

**Render to inspect:** `{render_path}`
{render_read_note}{image_context_sections}
{zoom_audit_section}
{print_scale_audit_section}
{visual_clash_section}
{text_boundary_clash_section}
{label_path_proximity_section}
{undeclared_geometry_section}
{reference_calibration_section}
{reference_learning_section}
{reference_aesthetic_metrics_section}
{external_vision_review_section}
{paper_aesthetic_context_section}
{journal_art_direction_playbook_section}
{aesthetic_intent_section}
{svg_polish_delta_section}

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

{brief_sections.editorial_art_direction_audit(require_route_detail=uses_route_detail_contract)}

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
(YAML front-matter then human-readable Markdown body — use the schema printed
below):

```markdown
---
schema: {critique_schema}
fixture: {name}
generated_at: <ISO-8601 timestamp>
generator: critique_brief.py
generator_version: {generator_version}
rubric_version: {critique_rubric_version}
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
{brief_sections.editorial_art_direction_schema(require_route_detail=uses_route_detail_contract)}
{brief_sections.journal_grade_assessment_schema(
    critique_input_hash,
    _reference_score_calibration(example_dir, reference_calibration_pack),
)}
{_journal_art_direction_playbook_audit_schema(journal_playbook_pack)}
{_aesthetic_lever_audit_schema(aesthetic_intent_pack)}
{_svg_polish_delta_audit_schema(uses_svg_polish_delta_schema)}
{_aesthetic_gate_audit_schema(uses_svg_polish_delta_schema)}
micro_defects:
  - id: M001
    crop: examples/{name}/build/audit_crops/<crop>.png
    kind: {_MICRO_DEFECT_KIND_SCHEMA}
    severity: BLOCKER | MAJOR | MINOR | NIT
    observation: "<visible micro-defect from a crop, print-scale image, or audit candidate>"
    linked_finding_id: "<P001/C001 or empty when accept_simplification>"
    visual_clash_ref: "<VC001 or empty when not from visual_clash.json>"
    text_boundary_ref: "<TB001 or empty when not from text_boundary_clash.json>"
    label_path_ref: "<LP001 or empty when not from label_path_proximity.json>"
    undeclared_geometry_ref: "<UG001 or empty when not from undeclared_geometry.json>"
    status: open | resolved | accept_simplification
    accept_simplification_reason: "<required enum when status=accept_simplification>"
    accept_simplification_rationale: "<required when status=accept_simplification>"
crop_audit_log:
  - crop_id: <crop id from build/audit_crops/manifest.json>
    path: build/audit_crops/<crop>.png
    source: <manifest source, e.g. full_render or visual_clash:VC001>
    inspected: true
    verdict: defect | no_defect | uncertain
    linked_micro_defect_id: "<M001 when verdict=defect or empty>"
    rationale: "<local geometry reason from direct crop inspection>"
    observed_objects: ["<object names visible in this crop>"]
    local_relationship: "<one sentence naming relative position or clearance>"
    candidate_refs: ["<VC/TB/LP/UG ids related to this crop, or [] when none>"]
{crop_anomaly_schema.rstrip()}
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
Every crop id in `build/audit_crops/manifest.json.required_crop_ids` must appear
exactly once in `crop_audit_log`. Use `verdict: uncertain` when the crop remains
ambiguous; do not silently treat uncertainty as pass. Use `verdict: defect` only
when `linked_micro_defect_id` names the corresponding `micro_defects[].id`.
{crop_anomaly_instructions.rstrip()}
For every visual-clash-linked `accept_simplification`, the `observation` must
name the `VC###` id. For every `micro_defects` item with
`status: accept_simplification`, `accept_simplification_reason` must be one of
`false_positive`, `intentional_schematic`, `outside_target_region`,
`convention_acceptable`, or `decorative_background`, and
`accept_simplification_rationale` must explain the concrete geometry/context
reason it is not a defect; do not write vague phrases such as "acceptable after
review".

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
