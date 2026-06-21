import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_path_geometry import canonical_polyline  # noqa: E402


def test_canonical_polyline_is_resample_invariant():
    # Same straight line, two different d-representations (1 segment vs 3).
    coarse = canonical_polyline("M0,0 L9,0", samples=64)
    fine = canonical_polyline("M0,0 L3,0 L6,0 L9,0", samples=64)
    assert len(coarse) == 64 and len(fine) == 64
    # Arc-length sampling makes them point-wise near-identical.
    max_dev = max(abs(a - b) for a, b in zip(coarse, fine))
    assert max_dev < 1e-6
