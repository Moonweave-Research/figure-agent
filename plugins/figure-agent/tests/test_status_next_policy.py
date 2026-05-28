"""Focused regression tests for /fig_status next-hint policy."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from export_freshness import EXPORT_FRESH, EXPORT_STALE, EXPORT_TRACKED_GOLDEN  # noqa: E402
from status_next_policy import select_next_hint  # noqa: E402


def _hint(
    *,
    stage: int,
    notes: list[str] | None = None,
    critique_state: str = "FRESH",
    exports_substate: str = EXPORT_FRESH,
    source_stale: bool = False,
    export_content_stale: bool = False,
    render_state: str = "FRESH",
    partial: bool = False,
    final_artifact_state: str = "NONE",
    accepted: bool | None = None,
) -> str:
    return select_next_hint(
        stage=stage,
        name="demo",
        notes=notes or [],
        critique_state=critique_state,
        exports_substate=exports_substate,
        source_stale=source_stale,
        export_content_stale=export_content_stale,
        render_state=render_state,
        partial=partial,
        final_artifact={"state": final_artifact_state},
        accepted=accepted,
    )


def test_stage_4_spec_parse_error_beats_export_and_acceptance_hints() -> None:
    hint = _hint(
        stage=4,
        notes=["spec_parse_error"],
        exports_substate=EXPORT_STALE,
        source_stale=True,
        accepted=False,
    )

    assert hint == "fix malformed examples/demo/spec.yaml before continuing."


def test_stage_4_missing_briefing_beats_critique_export_and_final_artifact() -> None:
    hint = _hint(
        stage=4,
        notes=["missing_briefing"],
        critique_state="STALE",
        source_stale=True,
        final_artifact_state="BLOCKED",
    )

    assert hint == "complete examples/demo/briefing.md before continuing."


def test_stage_4_reference_missing_beats_export_stale_hint() -> None:
    hint = _hint(
        stage=4,
        critique_state="REFERENCE_MISSING",
        exports_substate=EXPORT_STALE,
        export_content_stale=True,
    )

    assert hint == (
        "fix declared reference inputs in spec.yaml or add the missing files before continuing."
    )


def test_stage_4_tracked_golden_fresh_render_stale_critique_skips_compile() -> None:
    hint = _hint(
        stage=4,
        critique_state="STALE",
        exports_substate=EXPORT_TRACKED_GOLDEN,
        source_stale=True,
        render_state="FRESH",
    )

    assert "/fig_critique demo" in hint
    assert "/fig_export demo --force-golden" in hint
    assert "/fig_compile demo" not in hint


def test_stage_4_source_stale_stale_render_and_stale_critique_includes_compile() -> None:
    hint = _hint(
        stage=4,
        critique_state="STALE",
        source_stale=True,
        render_state="STALE",
    )

    assert hint == (
        "exports are stale — re-run /fig_compile demo, then /fig_critique demo,"
        " then /fig_export demo."
    )


def test_stage_4_final_artifact_blocked_beats_not_accepted_after_core_outputs_ready() -> None:
    hint = _hint(stage=4, final_artifact_state="BLOCKED", accepted=False)

    assert hint == (
        "final artifact requires semantic backport — patch TikZ/briefing/spec,"
        " rerun compile/export/critique as needed, then rerun"
        " scripts/svg_polish_handoff.py."
    )


def test_stage_4_missing_final_artifact_names_handoff_scaffolder() -> None:
    hint = _hint(stage=4, final_artifact_state="MISSING")

    assert "polish/demo.polished.svg" in hint
    assert "scripts/svg_polish_handoff.py" in hint


def test_stage_4_stale_final_artifact_names_handoff_scaffolder() -> None:
    hint = _hint(stage=4, final_artifact_state="STALE")

    assert "scripts/svg_polish_handoff.py" in hint


def test_stage_4_not_accepted_beats_done_when_final_artifact_ready() -> None:
    hint = _hint(stage=4, accepted=False)

    assert hint == (
        "golden fixture is not accepted yet — resolve examples/demo/QUALITY_AUDIT.md"
        " defects, then set accepted: true in spec.yaml."
    )


def test_stage_3_stale_critique_requires_critique_before_export() -> None:
    hint = _hint(stage=3, critique_state="STALE")

    assert hint == (
        "run /fig_critique demo before /fig_export demo"
        " because reference-grounded pre-export critique is missing or stale."
    )


def test_stage_4_fresh_exports_stale_critique_names_final_snapshot_review() -> None:
    hint = _hint(stage=4, critique_state="STALE")

    assert hint == (
        "run /fig_critique demo as a final review of the current rendered candidate"
        " before treating exports as final; if no edits are needed,"
        " existing exports can remain in place."
    )


def test_stage_2_missing_briefing_avoids_compile_hint() -> None:
    hint = _hint(stage=2, notes=["missing_briefing"])

    assert hint == "complete examples/demo/briefing.md before continuing."


def test_stage_1_spec_parse_error_beats_authoring_hint() -> None:
    hint = _hint(stage=1, notes=["spec_parse_error"])

    assert hint == "fix malformed examples/demo/spec.yaml before continuing."
