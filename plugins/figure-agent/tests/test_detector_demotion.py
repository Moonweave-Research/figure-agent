from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from detector_demotion import (  # noqa: E402
    build_detector_demotion_recommendations,
    main,
)
from test_detector_feedback_ledger import _write_complete_fixture  # noqa: E402


def _append_detector_log(
    fig_dir: Path,
    *,
    name: str,
    fired: bool,
    finding_count: int,
) -> None:
    log_path = fig_dir / "build" / "detector_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "name": name,
                    "fired": fired,
                    "finding_count": finding_count,
                    "duration_ms": 1.0,
                    "ts": 1.0,
                },
                sort_keys=True,
            )
            + "\n"
        )


def _detector_row(payload: dict, detector: str) -> dict:
    rows = payload["detectors"]
    return next(row for row in rows if row["detector"] == detector)


def test_recommends_demote_from_false_positive_adjudication_and_log_counts(
    tmp_path: Path,
) -> None:
    examples_root = tmp_path / "examples"
    alpha = _write_complete_fixture(
        examples_root,
        "alpha",
        visual_candidates=("VC001",),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    kind: line_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC001 is a detector false positive.\n"
            '    linked_finding_id: ""\n'
            "    visual_clash_ref: VC001\n"
            '    text_boundary_ref: ""\n'
            '    undeclared_geometry_ref: ""\n'
            "    status: accept_simplification\n"
            "    accept_simplification_reason: false_positive\n"
            "    accept_simplification_rationale: VC001 marks texture, not a defect.\n"
        ),
    )
    beta = _write_complete_fixture(
        examples_root,
        "beta",
        visual_candidates=("VC010",),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M010\n"
            "    kind: line_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC010 is also a detector false positive.\n"
            '    linked_finding_id: ""\n'
            "    visual_clash_ref: VC010\n"
            '    text_boundary_ref: ""\n'
            '    undeclared_geometry_ref: ""\n'
            "    status: accept_simplification\n"
            "    accept_simplification_reason: false_positive\n"
            "    accept_simplification_rationale: VC010 marks texture, not a defect.\n"
        ),
    )
    _append_detector_log(alpha, name="visual_clash", fired=True, finding_count=1)
    _append_detector_log(beta, name="visual_clash", fired=True, finding_count=1)

    payload = build_detector_demotion_recommendations(
        examples_root,
        ["alpha", "beta"],
        false_positive_threshold=0.5,
        min_candidate_count=2,
    )

    assert payload["schema"] == "figure-agent.detector-demotion-recommendations.v1"
    assert payload["fixture_count"] == 2
    visual_clash = _detector_row(payload, "visual_clash")
    assert visual_clash["candidate_count"] == 2
    assert visual_clash["accepted_false_positive_count"] == 2
    assert visual_clash["false_positive_rate"] == 1.0
    assert visual_clash["log_run_count"] == 2
    assert visual_clash["fired_run_count"] == 2
    assert visual_clash["recommendation"] == "demote"


def test_keeps_detector_below_threshold(tmp_path: Path) -> None:
    examples_root = tmp_path / "examples"
    alpha = _write_complete_fixture(
        examples_root,
        "alpha",
        visual_candidates=("VC001", "VC002"),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    kind: line_crosses_label\n"
            "    severity: MINOR\n"
            "    observation: VC001 is a real defect.\n"
            "    linked_finding_id: C001\n"
            "    visual_clash_ref: VC001\n"
            '    text_boundary_ref: ""\n'
            '    undeclared_geometry_ref: ""\n'
            "    status: open\n"
        ),
    )
    _append_detector_log(alpha, name="visual_clash", fired=True, finding_count=2)

    payload = build_detector_demotion_recommendations(
        examples_root,
        ["alpha"],
        false_positive_threshold=0.5,
        min_candidate_count=1,
    )

    visual_clash = _detector_row(payload, "visual_clash")
    assert visual_clash["false_positive_rate"] == 0.0
    assert visual_clash["recommendation"] == "keep"


def test_rejects_detector_log_symlink(tmp_path: Path) -> None:
    examples_root = tmp_path / "examples"
    alpha = _write_complete_fixture(
        examples_root,
        "alpha",
        visual_candidates=(),
        micro_defects_yaml="micro_defects: []\n",
    )
    outside_log = tmp_path / "outside.jsonl"
    outside_log.write_text("", encoding="utf-8")
    log_path = alpha / "build" / "detector_log.jsonl"
    log_path.unlink(missing_ok=True)
    log_path.symlink_to(outside_log)

    with pytest.raises(ValueError, match="detector_log_symlink_forbidden"):
        build_detector_demotion_recommendations(examples_root, ["alpha"])


def test_cli_prints_recommendations_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    examples_root = tmp_path / "examples"
    alpha = _write_complete_fixture(
        examples_root,
        "alpha",
        visual_candidates=(),
        micro_defects_yaml="micro_defects: []\n",
    )
    _append_detector_log(alpha, name="visual_clash", fired=False, finding_count=0)

    exit_code = main(["--examples-root", str(examples_root), "--json", "alpha"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.detector-demotion-recommendations.v1"
    assert payload["fixtures"] == ["alpha"]
