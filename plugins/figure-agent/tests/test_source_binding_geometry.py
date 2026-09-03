from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "checks"))

import check_label_path_proximity as proximity  # noqa: E402
import render_source_map  # noqa: E402

# Ten calibration strokes give the placement vote a majority to agree on; the
# bound lead is the eleventh and is what each declaration below measures.
CALIBRATION = "\n".join(
    [
        r"  \draw (0.00,0.00)--(1.00,0.00);",
        r"  \draw (0.00,0.50)--(1.40,0.50);",
        r"  \draw (0.00,1.00)--(1.80,1.00);",
        r"  \draw (0.00,1.50)--(2.20,1.50);",
        r"  \draw (0.00,2.00)--(2.60,2.00);",
        r"  \draw (3.00,0.00)--(3.00,1.10);",
        r"  \draw (3.40,0.00)--(3.40,1.50);",
        r"  \draw (3.80,0.00)--(3.80,1.90);",
        r"  \draw (4.20,0.00)--(4.20,2.30);",
        r"  \draw (4.60,0.00)--(4.60,2.70);",
    ]
)
OFFSET_X_CM = 0.1
OFFSET_Y_CM = 10.0

SPEC = """label_path_proximity_checks:
  - id: bound-lead
    kind: horizontal_line
    role: bound_lead
    y_pdf_cm: {y}
    x_range_pdf_cm: [2.1, 3.1]
    clearance_pt: 1.0
    source_binding:
      source_name: demo.tex
      selector: 'figure-agent-path: bound-lead'
"""


def _tex(lead: str, *, marker: str = "  % figure-agent-path: bound-lead") -> str:
    return "\n".join([r"\begin{tikzpicture}", CALIBRATION, marker, lead, r"\end{tikzpicture}", ""])


def _run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    tex: str,
    declared_y: float,
    rendered_tex: str | None = None,
) -> tuple[int, dict]:
    """Run the checker with the render derived from ``rendered_tex`` (default: ``tex``)."""
    fixture = tmp_path / "demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    pdf = build / "demo.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    (fixture / "demo.tex").write_text(tex, encoding="utf-8")
    (fixture / "spec.yaml").write_text(SPEC.format(y=declared_y), encoding="utf-8")
    ink = [
        (OFFSET_X_CM + ax, OFFSET_Y_CM - ay, OFFSET_X_CM + bx, OFFSET_Y_CM - by)
        for ax, ay, bx, by in render_source_map.source_segments(rendered_tex or tex)
    ]
    monkeypatch.setattr(render_source_map, "pdf_ink_segments", lambda _pdf: ink)
    monkeypatch.setattr(proximity, "extract_pdf_words_and_page", lambda _pdf: ([], (400.0, 400.0)))
    output = build / "label_path_proximity.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_label_path_proximity.py", str(pdf), "--json-output", str(output)],
    )
    return proximity.main(), json.loads(output.read_text(encoding="utf-8"))


def test_main_passes_a_declared_path_that_traces_its_bound_element(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status, report = _run(
        tmp_path,
        monkeypatch,
        tex=_tex(r"  \draw (2.00,3.00)--(3.00,3.00);"),
        declared_y=7.0,
    )

    assert status == 0
    assert report["live_binding"] == {"checked": 1, "state": "passed", "failures": []}


def test_main_fails_closed_when_the_bound_element_moves_under_the_declaration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status, report = _run(
        tmp_path,
        monkeypatch,
        tex=_tex(r"  \draw (2.00,2.70)--(3.00,2.70);"),
        declared_y=7.0,
    )

    assert status == 2
    assert report["live_binding"]["state"] == "failed"
    failure = report["live_binding"]["failures"][0]
    assert failure["check_id"] == "bound-lead"
    assert failure["kind"] == "source_binding_stale"
    assert "8.50 pt off the bound element" in failure["detail"]


def test_main_reports_a_selector_that_names_no_drawing_operation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status, report = _run(
        tmp_path,
        monkeypatch,
        tex=_tex(
            r"  \draw (2.00,3.00)--(3.00,3.00);",
            marker="  % figure-agent-path: bound-lead\n  % an unrelated note\n  % and another",
        ),
        declared_y=7.0,
    )

    assert status == 2
    assert report["live_binding"]["failures"][0]["kind"] == "source_binding_ungrounded"


def test_main_reports_a_bound_operation_whose_geometry_is_unreadable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status, report = _run(
        tmp_path,
        monkeypatch,
        tex=_tex(r"  \draw (undefined-start)--(undefined-end);"),
        rendered_tex=_tex(r"  \draw (2.00,3.00)--(3.00,3.00);"),
        declared_y=7.0,
    )

    assert status == 2
    assert report["live_binding"]["failures"][0]["kind"] == "source_binding_unparsed"


def test_main_refuses_a_render_the_source_cannot_be_placed_against(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = tmp_path / "demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    pdf = build / "demo.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    (fixture / "demo.tex").write_text(_tex(r"  \draw (2.00,3.00)--(3.00,3.00);"), encoding="utf-8")
    (fixture / "spec.yaml").write_text(SPEC.format(y=7.0), encoding="utf-8")
    monkeypatch.setattr(render_source_map, "pdf_ink_segments", lambda _pdf: [])
    monkeypatch.setattr(proximity, "extract_pdf_words_and_page", lambda _pdf: ([], (400.0, 400.0)))
    output = build / "label_path_proximity.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_label_path_proximity.py", str(pdf), "--json-output", str(output)],
    )

    status = proximity.main()
    report = json.loads(output.read_text(encoding="utf-8"))

    assert status == 2
    assert report["live_binding"]["failures"][0]["kind"] == "source_binding_unplaced"


def test_recover_placement_reads_the_scale_and_offset_off_the_render() -> None:
    tex = _tex(r"  \draw (2.00,3.00)--(3.00,3.00);")
    segments = render_source_map.source_segments(tex)
    ink = [
        (0.4 + 2.0 * ax, 12.0 - 2.0 * ay, 0.4 + 2.0 * bx, 12.0 - 2.0 * by)
        for ax, ay, bx, by in segments
    ]

    placement = render_source_map.recover_placement(tex, ink)

    assert placement is not None
    assert placement.scale == pytest.approx(2.0)
    assert placement.offset_x_cm == pytest.approx(0.4)
    assert placement.offset_y_cm == pytest.approx(12.0)
    assert placement.verified_segments == placement.source_segments
    assert placement.project(2.0, 3.0) == pytest.approx((4.4, 6.0))
