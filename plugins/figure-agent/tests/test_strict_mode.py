"""Exit-code tests for the --strict opt-in on collision/clash checkers.

Default behavior is report-only (exit 0). When --strict is passed the
checkers must exit non-zero on any finding, so compile.sh can be made to
fail under FIGURE_AGENT_STRICT=1 without changing default ergonomics.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_collisions  # noqa: E402
import check_text_boundary_clash  # noqa: E402
import check_visual_clash  # noqa: E402

GOLDEN_PDF = (
    REPO_ROOT / "examples" / "golden_trap_depth_picture" / "build" / "golden_trap_depth_picture.pdf"
)


def test_compile_sh_wires_the_physics_checks() -> None:
    compile_sh = (REPO_ROOT / "scripts" / "compile.sh").read_text(encoding="utf-8")
    # tex-geometry assertions are STRICT-gated (a reversed arrow is a defect);
    assert "scripts/checks/check_tex_assertions.py" in compile_sh
    # the grounding meta-check is advisory (report-only — never fails a build).
    assert "scripts/checks/check_physics_grounding.py" in compile_sh


def test_check_visual_clash_known_false_positive_registry_path_exists() -> None:
    assert check_visual_clash.KNOWN_FALSE_POSITIVES_PATH == (
        REPO_ROOT / "_known_false_positives.yaml"
    )
    patterns = check_visual_clash.load_known_false_positive_patterns()
    assert any(pattern.get("id") == "material_label_pdms_path_edge" for pattern in patterns)


def test_check_visual_clash_false_positive_matching_requires_kind() -> None:
    issue = check_visual_clash.VisualIssue(
        "text_on_path",
        "injection",
        "dark=0.041, edge=0.006",
        (1, 2, 3, 4),
    )
    pattern = {
        "id": "schematic_label_injection",
        "glyph": "injection",
        "kind": "text_on_fill",
    }

    filtered, suppressed = check_visual_clash.suppress_known_false_positives(
        [issue],
        [pattern],
    )

    assert filtered == [issue]
    assert suppressed == 0


def test_check_visual_clash_false_positive_matching_accepts_same_kind() -> None:
    issue = check_visual_clash.VisualIssue(
        "text_on_path",
        "PDMS",
        "dark=0.041, edge=0.004",
        (1, 2, 3, 4),
    )
    patterns = check_visual_clash.load_known_false_positive_patterns()

    filtered, suppressed = check_visual_clash.suppress_known_false_positives(
        [issue],
        patterns,
    )

    assert filtered == []
    assert suppressed == 1


def _require_golden_pdf() -> None:
    if not GOLDEN_PDF.exists():
        pytest.skip(f"{GOLDEN_PDF} not present; run /fig_compile golden_trap_depth_picture")


def test_check_collisions_default_exits_zero(monkeypatch) -> None:
    _require_golden_pdf()
    monkeypatch.setattr(sys, "argv", ["check_collisions.py", str(GOLDEN_PDF)])
    # Golden fixture currently has zero text bbox collisions.
    assert check_collisions.main() == 0


def test_check_collisions_strict_exits_zero_when_no_collisions(monkeypatch) -> None:
    _require_golden_pdf()
    monkeypatch.setattr(sys, "argv", ["check_collisions.py", str(GOLDEN_PDF), "--strict"])
    assert check_collisions.main() == 0


def test_check_visual_clash_default_exits_zero(monkeypatch) -> None:
    _require_golden_pdf()
    monkeypatch.setattr(sys, "argv", ["check_visual_clash.py", str(GOLDEN_PDF)])
    # Default mode reports findings but does not fail.
    assert check_visual_clash.main() == 0


def test_check_visual_clash_strict_fails_on_unsuppressed_clashes(monkeypatch) -> None:
    _require_golden_pdf()
    monkeypatch.setattr(sys, "argv", ["check_visual_clash.py", str(GOLDEN_PDF), "--strict"])
    # Golden fixture currently carries 42 raw clash candidates; strict mode
    # must fail until they are resolved or moved into the false-positive
    # registry.
    assert check_visual_clash.main() == 1


def test_check_visual_clash_json_payload_uses_machine_readable_metrics(tmp_path: Path) -> None:
    pdf = tmp_path / "demo_fixture" / "build" / "demo_fixture.pdf"
    issue = check_visual_clash.VisualIssue(
        "text_on_path",
        "HV+",
        "dark=0.041, edge=0.006",
        (1750, 1409, 1871, 1466),
    )

    payload = check_visual_clash.visual_clash_payload(pdf, [issue])

    assert payload == {
        "fixture": "demo_fixture",
        "render_pdf": "build/demo_fixture.pdf",
        "candidates": [
            {
                "id": "VC001",
                "kind": "text_on_path",
                "text": "HV+",
                "bbox_px": [1750, 1409, 1871, 1466],
                "metric": {"dark": 0.041, "edge": 0.006},
                "tex_lines": None,
            }
        ],
        "total": 1,
    }


def test_check_visual_clash_writes_json_output_without_count_banner(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    pdf = tmp_path / "demo_fixture" / "build" / "demo_fixture.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"%PDF-1.4\n")
    output = pdf.parent / "visual_clash.json"
    issue = check_visual_clash.VisualIssue("text_on_fill", "V", "luma_std=27.4", (1, 2, 3, 4))
    monkeypatch.setattr(check_visual_clash, "extract_pdf_words_and_page", lambda _pdf: ([], (1, 1)))
    monkeypatch.setattr(
        check_visual_clash,
        "render_pdf_first_page",
        lambda _pdf, _dpi: Image.new("RGB", (10, 10), "white"),
    )
    monkeypatch.setattr(check_visual_clash, "detect_visual_clashes", lambda *_args: [issue])
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_visual_clash.py", str(pdf), "--json-output", str(output)],
    )

    assert check_visual_clash.main() == 0
    captured = capsys.readouterr()
    assert "visual clash candidate(s)" not in captured.out
    candidate = json.loads(output.read_text(encoding="utf-8"))["candidates"][0]
    assert candidate["id"] == "VC001"
    assert candidate["text"] == "V"


def test_compile_strict_flag_is_documented_in_script() -> None:
    """compile.sh must propagate FIGURE_AGENT_STRICT to --strict so users can
    opt into a hard gate without editing the script."""
    compile_sh = (REPO_ROOT / "scripts" / "compile.sh").read_text(encoding="utf-8")
    assert "FIGURE_AGENT_STRICT" in compile_sh
    assert "--strict" in compile_sh
    assert "--ignore-known-fp" in compile_sh
    assert "--json-output" in compile_sh
    assert "visual_clash.json" in compile_sh
    assert "check_text_boundary_clash.py" in compile_sh
    assert "text_boundary_clash.json" in compile_sh


def test_check_text_boundary_clash_default_exits_zero_with_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fixture = tmp_path / "demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    pdf = build / "demo.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    (fixture / "spec.yaml").write_text(
        "name: demo\n"
        "text_boundary_checks:\n"
        "  - id: de_column_rule\n"
        "    kind: vertical_line\n"
        "    role: column_rule\n"
        "    x_pdf_cm: 2.54\n"
        "    y_range_pdf_cm: [0.0, 5.08]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        check_text_boundary_clash,
        "extract_pdf_words_and_page",
        lambda _pdf: (
            [{"text": "polymer", "xmin": 70.0, "ymin": 20.0, "xmax": 75.0, "ymax": 30.0}],
            (200.0, 200.0),
        ),
    )
    output = build / "text_boundary_clash.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_text_boundary_clash.py", str(pdf), "--json-output", str(output)],
    )

    assert check_text_boundary_clash.main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["candidates"][0]["id"] == "TB001"
