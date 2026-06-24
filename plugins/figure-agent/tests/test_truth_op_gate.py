import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_polish_recipe import reject_centerline_op_on_truth  # noqa: E402


def test_centerline_op_on_truth_path_rejected():
    with pytest.raises(ValueError, match="truth-bearing"):
        reject_centerline_op_on_truth(action_type="smooth", target_truth_bearing=True)


def test_centerline_op_on_decorative_path_ok():
    reject_centerline_op_on_truth(action_type="smooth", target_truth_bearing=False)


def test_stroke_op_on_truth_path_ok():
    reject_centerline_op_on_truth(action_type="taper_texture", target_truth_bearing=True)
