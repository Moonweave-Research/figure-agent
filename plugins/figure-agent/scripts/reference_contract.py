"""Shared reference-grounding contract for figure-level and panel references."""

from __future__ import annotations

from pathlib import Path

from inputs import parse_spec


def declared_figure_reference_path(example_dir: Path, spec: dict) -> Path | None:
    """Return the existing figure-level reference declared in spec.yaml."""
    reference_image = spec.get("reference_image")
    if not isinstance(reference_image, str) or not reference_image.strip():
        return None
    candidate = example_dir / reference_image.strip()
    return candidate if candidate.is_file() else None


def participating_panel_reference_paths(example_dir: Path, spec: dict) -> tuple[Path, ...]:
    """Return panel references that have both bbox metadata and an existing image."""
    paths: list[Path] = []
    for panel in spec.get("panels", []):
        if panel.get("bbox_pdf_cm") is None:
            continue
        reference = panel.get("reference_image")
        if not isinstance(reference, str) or not reference.strip():
            continue
        ref_path = example_dir / reference.strip()
        if ref_path.is_file():
            paths.append(ref_path)
    return tuple(paths)


def compute_reference_input_failures(example_dir: Path, spec: dict | None = None) -> list[str]:
    """Return declared reference inputs that should participate but are missing."""
    spec_path = example_dir / "spec.yaml"
    if spec is None:
        if not spec_path.exists():
            return []
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))

    failures: list[str] = []
    reference_image = spec.get("reference_image") if spec else None
    if isinstance(reference_image, str) and reference_image.strip():
        reference_image = reference_image.strip()
        if not (example_dir / reference_image).is_file():
            failures.append(f"reference_image_missing: {reference_image}")

    for index, panel in enumerate(spec.get("panels", [])):
        if panel.get("bbox_pdf_cm") is None:
            continue
        reference = panel.get("reference_image")
        if not isinstance(reference, str) or not reference.strip():
            continue
        reference = reference.strip()
        if not (example_dir / reference).is_file():
            panel_id = panel.get("id") or f"panel_{index + 1}"
            failures.append(f"panel_reference_image_missing: {panel_id}: {reference}")
    return failures
