"""Shared evidence set and hash snapshot helpers for fig_run journals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from journal_art_direction_playbook import (  # noqa: E402
    JournalArtDirectionPlaybookError,
    declared_journal_playbook_path,
)
from paper_aesthetic_context import (  # noqa: E402
    PaperAestheticContextError,
    declared_paper_context_path,
)
from quality_manifest import critique_manifest_paths, file_sha256  # noqa: E402

EVIDENCE_SNAPSHOT_VERSION = "figure-agent.fig-run-evidence-snapshot.v1"
MALFORMED_EVIDENCE_SNAPSHOT = "fig_run_journal:evidence_snapshot"


def repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except (OSError, ValueError):
        return str(path)


def fixture_evidence_paths(repo_root: Path, name: str) -> tuple[Path, ...]:
    example_dir = repo_root / "examples" / name
    paths = [
        example_dir / f"{name}.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
        example_dir / "authoring_plan.md",
        example_dir / "authoring_contract.md",
        example_dir / "subregion_iteration_log.md",
        example_dir / "theory_guard.md",
        example_dir / "coordinate_hints.yaml",
        example_dir / "critique_reference_pack.yaml",
        example_dir / "aesthetic_intent.yaml",
        example_dir / "critique.md",
        example_dir / "critique_adjudication.yaml",
        example_dir / "external_vision_review.yaml",
        example_dir / "inspection_trace.yaml",
        example_dir / "build" / "visual_clash.json",
        example_dir / "build" / "text_boundary_clash.json",
        example_dir / "build" / "label_path_proximity.json",
        example_dir / "build" / "audit_crops" / "manifest.json",
        example_dir / "build" / "reference_aesthetic_metrics.json",
        example_dir / "polish" / "svg_polish_recipe.yaml",
        example_dir / "polish" / "aesthetic_delta" / "before.png",
        example_dir / "polish" / "aesthetic_delta" / "after.png",
        example_dir / "polish" / "aesthetic_delta" / "diff.png",
        example_dir / "polish" / "aesthetic_delta" / "delta_manifest.json",
        example_dir / "polish" / "svg_semantic_diff.json",
        example_dir / "polish" / "svg_polish_audit.md",
        example_dir / "polish" / "svg_polish_manifest.yaml",
        example_dir / "polish" / f"{name}.polished.svg",
        example_dir / "build" / f"{name}.pdf",
        example_dir / "build" / f"{name}.png",
    ]
    paths.extend(_critique_manifest_paths(repo_root, example_dir, name))
    paths.extend(_declared_context_paths(example_dir))
    return tuple(dict.fromkeys(paths))


def evidence_snapshot(repo_root: Path, name: str) -> dict[str, Any]:
    items: list[dict[str, str]] = []
    for path in sorted(
        fixture_evidence_paths(repo_root, name),
        key=lambda item: repo_relative(repo_root, item),
    ):
        if not path.is_file():
            continue
        try:
            digest = file_sha256(path)
        except OSError:
            continue
        items.append({"path": repo_relative(repo_root, path), "sha256": digest})
    return {"schema": EVIDENCE_SNAPSHOT_VERSION, "items": items}


def snapshot_stale_paths(repo_root: Path, snapshot: object) -> list[str]:
    if snapshot is None:
        return []
    if not isinstance(snapshot, dict):
        return [MALFORMED_EVIDENCE_SNAPSHOT]
    if snapshot.get("schema") != EVIDENCE_SNAPSHOT_VERSION:
        return [MALFORMED_EVIDENCE_SNAPSHOT]
    items = snapshot.get("items")
    if not isinstance(items, list):
        return [MALFORMED_EVIDENCE_SNAPSHOT]

    stale_paths: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            stale_paths.append(MALFORMED_EVIDENCE_SNAPSHOT)
            continue
        raw_path = item.get("path")
        recorded_hash = item.get("sha256")
        if not isinstance(raw_path, str) or not raw_path:
            stale_paths.append(MALFORMED_EVIDENCE_SNAPSHOT)
            continue
        if not isinstance(recorded_hash, str) or not recorded_hash.startswith("sha256:"):
            stale_paths.append(raw_path)
            continue
        relative = Path(raw_path)
        if relative.is_absolute() or ".." in relative.parts:
            stale_paths.append(raw_path)
            continue
        current_path = repo_root / relative
        try:
            current_path.resolve().relative_to(repo_root.resolve())
        except (OSError, ValueError):
            stale_paths.append(raw_path)
            continue
        if not current_path.is_file():
            stale_paths.append(raw_path)
            continue
        try:
            current_hash = file_sha256(current_path)
        except OSError:
            stale_paths.append(raw_path)
            continue
        if current_hash != recorded_hash:
            stale_paths.append(raw_path)
    return sorted(dict.fromkeys(stale_paths))


def _critique_manifest_paths(repo_root: Path, example_dir: Path, name: str) -> tuple[Path, ...]:
    spec = _load_spec_mapping(example_dir)
    if spec is None:
        return ()
    try:
        return critique_manifest_paths(
            example_dir,
            name,
            spec,
            style_lock_path=repo_root / "styles" / "polymer-paper-preamble.sty",
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return ()


def _declared_context_paths(example_dir: Path) -> tuple[Path, ...]:
    spec = _load_spec_mapping(example_dir)
    if spec is None:
        return ()
    paths: list[Path] = []
    try:
        paper_context_path = declared_paper_context_path(example_dir, spec)
    except PaperAestheticContextError:
        paper_context_path = None
    if paper_context_path is not None:
        paths.append(paper_context_path)
    try:
        journal_playbook_path = declared_journal_playbook_path(example_dir, spec)
    except JournalArtDirectionPlaybookError:
        journal_playbook_path = None
    if journal_playbook_path is not None:
        paths.append(journal_playbook_path)
    return tuple(paths)


def _load_spec_mapping(example_dir: Path) -> dict[str, Any] | None:
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        return None
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None
    return spec if isinstance(spec, dict) else None
