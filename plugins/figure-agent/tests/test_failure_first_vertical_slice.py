from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "quality"))

from failure_ablation import evaluate_ablation

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def test_vertical_slice_has_comparable_raw_verified_repaired_evidence() -> None:
    fixture = PLUGIN_ROOT / "examples" / "failure_first_label_repair_demo"
    report = evaluate_ablation(
        {
            name: fixture / "review" / "ablation" / f"{name}.yaml"
            for name in ("raw", "verified", "repaired")
        }
    )
    assert report["variants"]["raw"]["confirmed_defect_count"] == 1
    assert report["variants"]["verified"]["confirmed_defect_count"] == 1
    assert report["variants"]["repaired"]["confirmed_defect_count"] == 0
    assert report["deltas"]["repaired_vs_raw"]["confirmed_defect_count"] == -1
    assert report["publication_acceptance"] == "not_claimed"


def test_repaired_source_preserves_declared_relations() -> None:
    fixture = PLUGIN_ROOT / "examples" / "failure_first_label_repair_demo"
    source = (fixture / "failure_first_label_repair_demo.tex").read_text(
        encoding="utf-8"
    )
    assert "Coulomb repulsion" in source
    assert "electrode separation" in source
