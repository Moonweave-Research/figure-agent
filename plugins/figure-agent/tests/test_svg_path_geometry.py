import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_path_geometry import canonical_polyline, frechet_distance, shape_signature  # noqa: E402


def test_frechet_zero_for_identical_and_grows_with_drift():
    a = canonical_polyline("M0,0 L10,0", samples=64)
    same = canonical_polyline("M0,0 L5,0 L10,0", samples=64)  # same line
    drift = canonical_polyline("M0,0 Q5,3 10,0", samples=64)  # bows up ~3 units
    assert frechet_distance(a, same) < 1e-6
    assert frechet_distance(a, drift) > 1.0


def test_canonical_polyline_is_resample_invariant():
    # Same straight line, two different d-representations (1 segment vs 3).
    coarse = canonical_polyline("M0,0 L9,0", samples=64)
    fine = canonical_polyline("M0,0 L3,0 L6,0 L9,0", samples=64)
    assert len(coarse) == 64 and len(fine) == 64
    # Arc-length sampling makes them point-wise near-identical.
    max_dev = max(abs(a - b) for a, b in zip(coarse, fine))
    assert max_dev < 1e-6


def test_signature_detects_cusp_removal():
    # A sharp V (cusp) vs a smoothed arc between the same endpoints.
    cusp = shape_signature("M0,0 L5,5 L10,0")  # one sharp corner
    smooth = shape_signature("M0,0 Q5,5 10,0")  # no corner
    assert cusp.corner_count == 1
    assert smooth.corner_count == 0
    assert cusp != smooth


def test_signature_is_resample_invariant():
    a = shape_signature("M0,0 L5,5 L10,0")
    b = shape_signature("M0,0 L2.5,2.5 L5,5 L7.5,2.5 L10,0")  # same shape, more pts
    assert a == b
