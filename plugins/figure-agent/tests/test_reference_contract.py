from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from reference_contract import (  # noqa: E402
    compute_reference_input_failures,
    declared_figure_reference_path,
    participating_panel_reference_paths,
)


def test_declared_figure_reference_path_never_infers_from_reference_directory(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "fig"
    reference_dir = example_dir / "reference"
    reference_dir.mkdir(parents=True)
    (reference_dir / "golden_target_001.png").write_bytes(b"PNG")

    assert declared_figure_reference_path(example_dir, {"panels": []}) is None


def test_declared_figure_reference_path_returns_existing_spec_reference(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "fig"
    reference_dir = example_dir / "reference"
    reference_dir.mkdir(parents=True)
    ref_path = reference_dir / "target.png"
    ref_path.write_bytes(b"PNG")

    assert (
        declared_figure_reference_path(
            example_dir,
            {"reference_image": " reference/target.png ", "panels": []},
        )
        == ref_path
    )


def test_participating_panel_reference_paths_require_bbox_and_existing_file(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "fig"
    reference_dir = example_dir / "reference"
    reference_dir.mkdir(parents=True)
    panel_ref = reference_dir / "panel_a.png"
    panel_ref.write_bytes(b"PNG")

    spec = {
        "panels": [
            {"id": "A", "reference_image": " reference/panel_a.png ", "bbox_pdf_cm": [0, 0, 1, 1]},
            {"id": "B", "reference_image": "reference/panel_b.png", "bbox_pdf_cm": [0, 0, 1, 1]},
            {"id": "C", "reference_image": "reference/panel_c.png"},
        ]
    }

    assert participating_panel_reference_paths(example_dir, spec) == (panel_ref,)


def test_reference_input_failures_only_block_participating_declared_inputs(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "fig"
    example_dir.mkdir()
    spec = {
        "reference_image": "reference/missing_top.png",
        "panels": [
            {
                "id": "A",
                "reference_image": "reference/missing_panel.png",
                "bbox_pdf_cm": [0, 0, 1, 1],
            },
            {"id": "B", "reference_image": "reference/skipped_without_bbox.png"},
        ],
    }

    assert compute_reference_input_failures(example_dir, spec) == [
        "reference_image_missing: reference/missing_top.png",
        "panel_reference_image_missing: A: reference/missing_panel.png",
    ]
