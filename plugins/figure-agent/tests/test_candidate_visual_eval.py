from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_visual_eval  # noqa: E402


def _write_ppm(path: Path, width: int, height: int, pixels: list[tuple[int, int, int]]) -> None:
    values = " ".join(f"{r} {g} {b}" for r, g, b in pixels)
    path.write_text(f"P3\n{width} {height}\n255\n{values}\n", encoding="ascii")


def test_compare_image_pair_records_dimensions_hashes_and_pixel_delta(tmp_path: Path) -> None:
    before = tmp_path / "before.ppm"
    after = tmp_path / "after.ppm"
    _write_ppm(before, 2, 2, [(255, 255, 255)] * 4)
    _write_ppm(after, 2, 2, [(255, 255, 255), (255, 255, 255), (255, 255, 255), (0, 0, 0)])

    payload = candidate_visual_eval.compare_image_pair(before, after)

    assert payload["status"] == "rendered_needs_human_review"
    assert payload["before"]["dimensions"] == [2, 2]
    assert payload["after"]["dimensions"] == [2, 2]
    assert payload["before"]["sha256"].startswith("sha256:")
    assert payload["after"]["sha256"].startswith("sha256:")
    assert payload["visual_deltas"]["pixel_diff_max"] == 255
    assert payload["visual_deltas"]["changed_bbox"] == [1, 1, 1, 1]


def test_compare_image_pair_dimension_mismatch_needs_human_review(tmp_path: Path) -> None:
    before = tmp_path / "before.ppm"
    after = tmp_path / "after.ppm"
    _write_ppm(before, 2, 2, [(255, 255, 255)] * 4)
    _write_ppm(after, 3, 2, [(255, 255, 255)] * 6)

    payload = candidate_visual_eval.compare_image_pair(before, after)

    assert payload["status"] == "rendered_needs_human_review"
    assert payload["before"]["dimensions"] == [2, 2]
    assert payload["after"]["dimensions"] == [3, 2]
    assert payload["visual_deltas"] == {}
    assert payload["diagnostics"] == [
        {
            "stage": "evaluate",
            "category": "dimension_mismatch",
            "message": "before and after images have different dimensions",
        }
    ]
