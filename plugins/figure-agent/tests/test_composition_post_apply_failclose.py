"""Fail-closed behavior for the post-apply visual receipt detector summary (Task 0.6b)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import composition_post_apply_verify as verify  # noqa: E402

pytestmark = pytest.mark.quarantine

_PRESENT = {"status": "present"}
_EXPORT_PRESENT = {"status": "present"}


def _reports(*, visual: str = "present", text: str = "present", label: str = "present") -> dict:
    def summary(status: str) -> dict:
        return {"status": status, "total": 0 if status == "present" else None}

    return {
        "visual_clash": summary(visual),
        "text_boundary_clash": summary(text),
        "label_path_proximity": summary(label),
    }


def test_missing_visual_clash_report_blocks() -> None:
    strict = verify._strict_compile_summary(_PRESENT, _reports(visual="missing"))
    assert strict["status"] == "blocked_missing_detector_report"
    assert "visual_clash" in strict["missing_detector_reports"]


def test_missing_any_detector_report_blocks() -> None:
    strict = verify._strict_compile_summary(_PRESENT, _reports(label="missing"))
    assert strict["status"] == "blocked_missing_detector_report"


def test_missing_detector_receipt_status_is_not_rendered_exported() -> None:
    strict = verify._strict_compile_summary(_PRESENT, _reports(visual="missing"))
    status = verify._receipt_status(_PRESENT, _EXPORT_PRESENT, strict)
    assert status == "blocked_missing_detector_report"


def test_all_present_no_clash_still_rendered_exported() -> None:
    strict = verify._strict_compile_summary(_PRESENT, _reports())
    assert strict["status"] == "no_known_strict_blocker"
    status = verify._receipt_status(_PRESENT, _EXPORT_PRESENT, strict)
    assert status == "rendered_exported"


def test_present_reports_with_visual_clash_still_warns() -> None:
    reports = _reports()
    reports["visual_clash"]["total"] = 2
    strict = verify._strict_compile_summary(_PRESENT, reports)
    assert strict["status"] == "blocked_by_visual_clash"
    status = verify._receipt_status(_PRESENT, _EXPORT_PRESENT, strict)
    assert status == "rendered_exported_with_strict_visual_warnings"
