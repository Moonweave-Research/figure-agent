"""Deterministic input hashing helpers for quality-state manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from aesthetic_intent import AESTHETIC_INTENT_SCHEMA_V2
from external_vision_review import ExternalVisionReviewError, external_vision_review_opted_in
from journal_art_direction_playbook import (
    JournalArtDirectionPlaybookError,
    declared_journal_playbook_path,
    journal_playbook_id_from_spec,
)
from paper_aesthetic_context import PaperAestheticContextError, declared_paper_context_path
from reference_contract import (
    declared_figure_reference_path,
    participating_panel_reference_paths,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CRITIQUE_RUBRIC_VERSION = "figure-agent.critique-rubric.v1.10"
CRITIQUE_RUBRIC_VERSION_V1_11 = "figure-agent.critique-rubric.v1.11"
CRITIQUE_RUBRIC_VERSION_V1_12 = "figure-agent.critique-rubric.v1.12"
CRITIQUE_RUBRIC_VERSION_V1_13 = "figure-agent.critique-rubric.v1.13"
CRITIQUE_RUBRIC_VERSION_V1_14 = "figure-agent.critique-rubric.v1.14"
CRITIQUE_SCHEMA_VERSION_V1_11 = "figure-agent.critique.v1.11"
CRITIQUE_SCHEMA_VERSION_V1_12 = "figure-agent.critique.v1.12"
CRITIQUE_SCHEMA_VERSION_V1_13 = "figure-agent.critique.v1.13"
CRITIQUE_SCHEMA_VERSION_V1_14 = "figure-agent.critique.v1.14"
_CRITIQUE_METADATA_KEYS = ("generator_version", "rubric_version", "critique_input_hash")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _relative_manifest_path(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(path.resolve())


def input_manifest_hash(paths: tuple[Path, ...], *, base_dir: Path) -> str:
    entries = [
        {
            "path": _relative_manifest_path(path, base_dir),
            "sha256": file_sha256(path),
        }
        for path in sorted(dict.fromkeys(paths), key=lambda item: str(item.resolve()))
    ]
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _source_paths(example_dir: Path, name: str, style_lock_path: Path) -> tuple[Path, ...]:
    candidates = [
        example_dir / f"{name}.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
        style_lock_path,
    ]
    return tuple(path for path in candidates if path.exists())


def _authoring_context_paths(example_dir: Path) -> tuple[Path, ...]:
    candidates = (
        example_dir / "authoring_contract.md",
        example_dir / "reference" / "reference_pack.md",
        example_dir / "authoring_plan.md",
        example_dir / "theory_guard.md",
        example_dir / "subregion_iteration_log.md",
    )
    return tuple(path for path in candidates if path.is_file())


def _uses_polished_svg_final_artifact(spec: dict) -> bool:
    final_artifact = spec.get("final_artifact")
    return isinstance(final_artifact, dict) and final_artifact.get("kind") == "polished_svg"


def critique_manifest_paths(
    example_dir: Path,
    name: str,
    spec: dict,
    *,
    style_lock_path: Path,
) -> tuple[Path, ...]:
    paths = list(_source_paths(example_dir, name, style_lock_path))
    ref_path = declared_figure_reference_path(example_dir, spec)
    if ref_path is not None:
        paths.append(ref_path)
    hints_path = example_dir / "coordinate_hints.yaml"
    if hints_path.exists():
        paths.append(hints_path)
    visual_clash_path = example_dir / "build" / "visual_clash.json"
    if visual_clash_path.exists():
        paths.append(visual_clash_path)
    text_boundary_clash_path = example_dir / "build" / "text_boundary_clash.json"
    if text_boundary_clash_path.exists():
        paths.append(text_boundary_clash_path)
    label_path_proximity_path = example_dir / "build" / "label_path_proximity.json"
    if label_path_proximity_path.exists():
        paths.append(label_path_proximity_path)
    audit_crop_manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    if audit_crop_manifest_path.exists():
        paths.append(audit_crop_manifest_path)
    critique_reference_pack_path = example_dir / "critique_reference_pack.yaml"
    if critique_reference_pack_path.exists():
        paths.append(critique_reference_pack_path)
    reference_aesthetic_metrics_path = example_dir / "build" / "reference_aesthetic_metrics.json"
    if reference_aesthetic_metrics_path.exists():
        paths.append(reference_aesthetic_metrics_path)
    try:
        include_external_review = external_vision_review_opted_in(spec)
    except ExternalVisionReviewError:
        include_external_review = False
    external_vision_review_path = example_dir / "external_vision_review.yaml"
    if include_external_review and external_vision_review_path.exists():
        paths.append(external_vision_review_path)
    aesthetic_intent_path = example_dir / "aesthetic_intent.yaml"
    if aesthetic_intent_path.exists():
        paths.append(aesthetic_intent_path)
    try:
        paper_context_path = declared_paper_context_path(example_dir, spec)
    except PaperAestheticContextError:
        paper_context_path = None
    if paper_context_path is not None and paper_context_path.exists():
        paths.append(paper_context_path)
    try:
        journal_playbook_path = declared_journal_playbook_path(example_dir, spec)
    except JournalArtDirectionPlaybookError:
        journal_playbook_path = None
    if journal_playbook_path is not None and journal_playbook_path.exists():
        paths.append(journal_playbook_path)
    svg_polish_delta_candidates = (
        example_dir / "polish" / "aesthetic_delta" / "delta_manifest.json",
        example_dir / "polish" / "aesthetic_delta" / "before.png",
        example_dir / "polish" / "aesthetic_delta" / "after.png",
        example_dir / "polish" / "aesthetic_delta" / "diff.png",
        example_dir / "polish" / "svg_polish_recipe.yaml",
        example_dir / "polish" / f"{name}.polished.svg",
    )
    svg_polish_delta_paths = [path for path in svg_polish_delta_candidates if path.exists()]
    paths.extend(svg_polish_delta_paths)
    generated_export_svg_path = example_dir / "exports" / f"{name}.svg"
    if (
        (_uses_polished_svg_final_artifact(spec) or svg_polish_delta_paths)
        and generated_export_svg_path.exists()
    ):
        paths.append(generated_export_svg_path)
    paths.extend(participating_panel_reference_paths(example_dir, spec))
    paths.extend(_authoring_context_paths(example_dir))
    return tuple(dict.fromkeys(paths))


def compute_critique_input_hash(
    example_dir: Path,
    name: str,
    spec: dict,
    *,
    style_lock_path: Path,
    base_dir: Path = REPO_ROOT,
) -> str:
    return input_manifest_hash(
        critique_manifest_paths(example_dir, name, spec, style_lock_path=style_lock_path),
        base_dir=base_dir,
    )


def critique_generator_version(
    generator_path: Path = REPO_ROOT / "scripts" / "critique_brief.py",
) -> str:
    return file_sha256(generator_path)


def expected_critique_rubric_version(example_dir: Path) -> str:
    reference_pack_path = example_dir / "critique_reference_pack.yaml"
    if reference_pack_path.is_file():
        try:
            reference_pack = yaml.safe_load(reference_pack_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            reference_pack = {}
        if isinstance(reference_pack, dict) and isinstance(
            reference_pack.get("reference_learning"),
            dict,
        ):
            return CRITIQUE_RUBRIC_VERSION_V1_14
    spec_path = example_dir / "spec.yaml"
    if spec_path.is_file():
        try:
            spec_data = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            spec_data = {}
        if isinstance(spec_data, dict):
            try:
                if journal_playbook_id_from_spec(spec_data) is not None:
                    return CRITIQUE_RUBRIC_VERSION_V1_14
            except JournalArtDirectionPlaybookError:
                return CRITIQUE_RUBRIC_VERSION_V1_14
    intent_path = example_dir / "aesthetic_intent.yaml"
    if not intent_path.is_file():
        return CRITIQUE_RUBRIC_VERSION
    try:
        data = yaml.safe_load(intent_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return CRITIQUE_RUBRIC_VERSION
    if isinstance(data, dict) and data.get("schema") == AESTHETIC_INTENT_SCHEMA_V2:
        return CRITIQUE_RUBRIC_VERSION_V1_14
    return CRITIQUE_RUBRIC_VERSION


def _critique_schema_matches_expected_rubric(
    metadata: dict,
    expected_rubric_version: str,
) -> bool:
    schema = metadata.get("schema")
    if expected_rubric_version == CRITIQUE_RUBRIC_VERSION_V1_14:
        return schema == CRITIQUE_SCHEMA_VERSION_V1_14
    if expected_rubric_version == CRITIQUE_RUBRIC_VERSION_V1_13:
        return schema == CRITIQUE_SCHEMA_VERSION_V1_13
    if expected_rubric_version == CRITIQUE_RUBRIC_VERSION_V1_12:
        return schema == CRITIQUE_SCHEMA_VERSION_V1_12
    if expected_rubric_version == CRITIQUE_RUBRIC_VERSION_V1_11:
        return schema == CRITIQUE_SCHEMA_VERSION_V1_11
    return schema not in {
        CRITIQUE_SCHEMA_VERSION_V1_11,
        CRITIQUE_SCHEMA_VERSION_V1_12,
        CRITIQUE_SCHEMA_VERSION_V1_13,
        CRITIQUE_SCHEMA_VERSION_V1_14,
    }


def yaml_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if end_index is None:
        return {}
    try:
        data = yaml.safe_load("\n".join(lines[1:end_index])) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def critique_hash_freshness(
    critique_path: Path,
    example_dir: Path,
    name: str,
    spec: dict,
    *,
    style_lock_path: Path,
    base_dir: Path = REPO_ROOT,
    generator_path: Path = REPO_ROOT / "scripts" / "critique_brief.py",
    rubric_version: str | None = None,
) -> bool | None:
    metadata = yaml_frontmatter(critique_path)
    values = {key: metadata.get(key) for key in _CRITIQUE_METADATA_KEYS}
    if not all(isinstance(value, str) and value.strip() for value in values.values()):
        return None
    expected_hash = compute_critique_input_hash(
        example_dir,
        name,
        spec,
        style_lock_path=style_lock_path,
        base_dir=base_dir,
    )
    expected_rubric_version = rubric_version or expected_critique_rubric_version(example_dir)
    return (
        values["critique_input_hash"].strip() == expected_hash
        and values["rubric_version"].strip() == expected_rubric_version
        and values["generator_version"].strip() == critique_generator_version(generator_path)
        and _critique_schema_matches_expected_rubric(metadata, expected_rubric_version)
    )
