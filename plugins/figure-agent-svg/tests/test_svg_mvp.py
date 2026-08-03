from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from svg_contract import issue_codes, validate_semantic_svg  # noqa: E402
from svg_export import prepare_semantic_svg_for_export  # noqa: E402
from svg_primitives import (  # noqa: E402
    load_primitive_doc,
    render_fragment,
    render_source_from_fragments,
)
from svg_qa import (  # noqa: E402
    extract_svg_text,
    has_white_background,
    missing_required_labels,
    pdf_font_issues_from_pdffonts,
    pdf_text_missing_labels,
    visual_diff_fraction,
)
from svg_status import (  # noqa: E402
    EXPORT_FRESH,
    EXPORT_MISSING,
    EXPORT_PARTIAL,
    EXPORT_STALE,
    compute_export_state,
)
from svg_underlay import (  # noqa: E402
    create_locked_underlay,
    create_locked_underlay_from_spec,
)


def test_create_locked_underlay_marks_vtracer_as_coordinate_evidence(tmp_path: Path) -> None:
    reference = tmp_path / "draft.png"
    Image.new("RGB", (4, 4), "white").save(reference)

    def fake_converter(input_path: str, output_path: str, **_: object) -> None:
        assert input_path == str(reference)
        Path(output_path).write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4" '
            'viewBox="0 0 4 4"><path id="raw-vtracer-path" d="M0 0L4 4"/></svg>',
            encoding="utf-8",
        )

    underlay = create_locked_underlay(
        reference,
        tmp_path / "underlay.svg",
        converter=fake_converter,
    )

    text = underlay.read_text(encoding="utf-8")
    assert 'id="vtracer-underlay"' in text
    assert 'data-locked="true"' in text
    assert 'data-final-source="false"' in text
    assert 'data-role="coordinate-evidence"' in text
    assert "raw-vtracer-path" in text


def test_create_locked_underlay_from_spec_resolves_reference_image(tmp_path: Path) -> None:
    figure_dir = tmp_path / "examples" / "fig_spec"
    (figure_dir / "reference").mkdir(parents=True)
    reference = figure_dir / "reference" / "draft.png"
    Image.new("RGB", (4, 4), "white").save(reference)
    (figure_dir / "spec.yaml").write_text(
        "name: fig_spec\nreference_image: reference/draft.png\n",
        encoding="utf-8",
    )

    def fake_converter(input_path: str, output_path: str, **_: object) -> None:
        assert input_path == str(reference)
        Path(output_path).write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4" '
            'viewBox="0 0 4 4"><path d="M0 0L4 4"/></svg>',
            encoding="utf-8",
        )

    underlay = create_locked_underlay_from_spec(figure_dir, converter=fake_converter)

    assert underlay == figure_dir / "underlay" / "fig_spec.underlay.svg"
    text = underlay.read_text(encoding="utf-8")
    assert 'id="vtracer-underlay"' in text
    assert "reference/draft.png" in text


def test_prepare_export_strips_locked_underlay_and_adds_white_background(tmp_path: Path) -> None:
    source = tmp_path / "source.svg"
    source.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <g id="vtracer-underlay" data-final-source="false"><path d="M0 0L10 10"/></g>
  <g id="semantic-layer"><text x="1" y="2">Trap depth</text></g>
</svg>
""",
        encoding="utf-8",
    )
    prepared = tmp_path / "prepared.svg"

    prepare_semantic_svg_for_export(source, prepared)

    text = prepared.read_text(encoding="utf-8")
    assert "vtracer-underlay" not in text
    assert 'id="figure-agent-white-background"' in text
    assert "Trap depth" in text
    assert extract_svg_text(prepared) == ["Trap depth"]


def test_label_qa_reports_missing_declared_labels(tmp_path: Path) -> None:
    svg = tmp_path / "semantic.svg"
    svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <text>Trap depth</text>
  <text>Shallow</text>
</svg>
""",
        encoding="utf-8",
    )

    assert missing_required_labels(svg, ["Trap depth", "Deep"]) == ["Deep"]


def test_white_background_and_visual_diff_are_image_based(tmp_path: Path) -> None:
    white = tmp_path / "white.png"
    changed = tmp_path / "changed.png"
    transparent = tmp_path / "transparent.png"

    Image.new("RGB", (2, 2), "white").save(white)
    Image.new("RGBA", (2, 2), (255, 255, 255, 0)).save(transparent)
    img = Image.new("RGB", (2, 2), "white")
    img.putpixel((1, 1), (0, 0, 0))
    img.save(changed)

    assert has_white_background(white) is True
    assert has_white_background(transparent) is False
    assert visual_diff_fraction(white, white) == 0.0
    assert visual_diff_fraction(white, changed) == 0.25


def test_qa_uses_spec_visual_diff_tolerance(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from svg_qa import main as svg_qa_main  # noqa: PLC0415

    source = tmp_path / "source.svg"
    source.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg"
  data-figure-agent-svg="semantic-v1"
  data-journal-preset="nature-single"
  width="89mm" height="54mm" viewBox="0 0 890 540">
  <g id="semantic-layer">
    <g id="panels"><g id="panel-a" data-role="panel" data-bbox="40 40 810 460"/></g>
    <g id="objects"></g>
    <g id="labels">
      <text data-text-role="label" data-bbox="80 80 150 18" x="80" y="94"
        font-family="Arial" font-size="14" fill="#111827">Valid label</text>
    </g>
  </g>
</svg>
""",
        encoding="utf-8",
    )
    spec = tmp_path / "spec.yaml"
    spec.write_text("visual_diff:\n  tolerance: 5\n", encoding="utf-8")
    reference = tmp_path / "reference.png"
    candidate = tmp_path / "candidate.png"
    Image.new("RGB", (4, 4), (250, 250, 250)).save(reference)
    Image.new("RGB", (4, 4), "white").save(candidate)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "svg_qa.py",
            str(source),
            "--spec",
            str(spec),
            "--png",
            str(candidate),
            "--reference-png",
            str(reference),
            "--max-diff",
            "0",
        ],
    )

    assert svg_qa_main() == 0


def test_pdf_qa_requires_embedded_unicode_fonts_and_required_text() -> None:
    pdffonts_output = """name type encoding emb sub uni object ID
------------------------------------ ----------------- ---------------- --- --- --- ---------
ABCDEF+ArialMT TrueType WinAnsi yes yes yes 7 0
[none] Type 3 Custom yes no yes 8 0
BADFONT TrueType WinAnsi no no no 9 0
"""

    assert pdf_font_issues_from_pdffonts(pdffonts_output) == [
        "font not embedded: BADFONT",
        "font lacks unicode map: BADFONT",
    ]
    assert pdf_text_missing_labels(
        "Fig. 1 SVG-first paper figure workflow\nQA gate\n",
        ["Fig. 1 SVG-first paper figure workflow", "QA gate", "Missing"],
    ) == ["Missing"]


def test_export_freshness_tracks_source_underlay_and_three_outputs(tmp_path: Path) -> None:
    figure_dir = tmp_path / "examples" / "fig_a"
    (figure_dir / "source").mkdir(parents=True)
    (figure_dir / "underlay").mkdir()
    (figure_dir / "exports").mkdir()
    source = figure_dir / "source" / "fig_a.svg"
    underlay = figure_dir / "underlay" / "fig_a.underlay.svg"

    source.write_text("<svg/>", encoding="utf-8")
    assert compute_export_state(figure_dir, "fig_a") == EXPORT_MISSING

    pdf = figure_dir / "exports" / "fig_a.pdf"
    png = figure_dir / "exports" / "fig_a.png"
    tif = figure_dir / "exports" / "fig_a.tif"
    pdf.write_bytes(b"pdf")
    png.write_bytes(b"png")
    assert compute_export_state(figure_dir, "fig_a") == EXPORT_PARTIAL

    tif.write_bytes(b"tif")
    assert compute_export_state(figure_dir, "fig_a") == EXPORT_FRESH

    underlay.write_text("<svg/>", encoding="utf-8")
    future = max(path.stat().st_mtime for path in (pdf, png, tif)) + 10
    source.touch()
    underlay.touch()
    # Make the coordinate-evidence layer newer than every export.
    import os

    os.utime(underlay, (future, future))

    assert compute_export_state(figure_dir, "fig_a") == EXPORT_STALE


def test_semantic_svg_contract_accepts_schema_style_and_required_objects(
    tmp_path: Path,
) -> None:
    svg = tmp_path / "source.svg"
    svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg"
  data-figure-agent-svg="semantic-v1"
  data-journal-preset="nature-single"
  width="89mm" height="54mm" viewBox="0 0 890 540">
  <g id="semantic-layer">
    <g id="panels">
      <g id="panel-a" data-role="panel" data-bbox="40 40 370 460"/>
      <g id="panel-b" data-role="panel" data-bbox="480 40 370 460"/>
    </g>
    <g id="objects">
      <rect data-object-id="device-stack" data-bbox="80 170 260 190"
        x="80" y="170" width="260" height="190" fill="#6B7280" stroke="#111827"
        stroke-width="1.2"/>
      <path data-object-id="charge-flow" data-bbox="520 230 250 60"
        d="M520 260 C620 215 690 215 770 260" fill="none" stroke="#2563EB"
        stroke-width="1.8"/>
    </g>
    <g id="labels">
      <text data-text-role="title" data-bbox="60 64 210 24" x="60" y="82"
        font-family="Arial" font-size="18" fill="#111827">Device overview</text>
      <text data-text-role="label" data-bbox="520 330 145 18" x="520" y="344"
        font-family="Arial" font-size="14" fill="#111827">Trap depth</text>
    </g>
  </g>
</svg>
""",
        encoding="utf-8",
    )
    spec = {
        "required_labels": ["Device overview", "Trap depth"],
        "required_objects": ["device-stack", "charge-flow"],
    }

    assert validate_semantic_svg(svg, spec=spec) == []


def test_semantic_svg_contract_reports_style_lock_and_schema_failures(
    tmp_path: Path,
) -> None:
    svg = tmp_path / "bad.svg"
    svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg"
  data-figure-agent-svg="semantic-v1"
  data-journal-preset="unknown-journal"
  width="100mm" height="54mm" viewBox="0 0 890 540">
  <g id="semantic-layer">
    <g id="labels">
      <text data-text-role="subtitle" data-bbox="20 20 150 24" x="20" y="40"
        font-family="Times New Roman" font-size="16" fill="#FF00FF">Bad label</text>
    </g>
    <g id="objects">
      <rect data-object-id="device-stack" data-bbox="30 80 200 120"
        x="30" y="80" width="200" height="120" fill="#ABCDEF" stroke="#111827"
        stroke-width="2.7"/>
    </g>
  </g>
</svg>
""",
        encoding="utf-8",
    )

    codes = issue_codes(validate_semantic_svg(svg, spec={"required_labels": ["Missing"]}))

    assert "missing_group:panels" in codes
    assert "unknown_journal_preset" in codes
    assert "journal_width_mismatch" in codes
    assert "unknown_text_role" in codes
    assert "font_family_not_allowed" in codes
    assert "font_size_mismatch" in codes
    assert "fill_not_in_palette" in codes
    assert "stroke_width_not_allowed" in codes
    assert "missing_required_label" in codes


def test_semantic_svg_contract_reports_overlap_and_margin_failures(tmp_path: Path) -> None:
    svg = tmp_path / "layout.svg"
    svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg"
  data-figure-agent-svg="semantic-v1"
  data-journal-preset="nature-single"
  width="89mm" height="54mm" viewBox="0 0 890 540">
  <g id="semantic-layer">
    <g id="panels">
      <g id="panel-a" data-role="panel" data-bbox="20 40 430 440"/>
      <g id="panel-b" data-role="panel" data-bbox="455 40 410 440"/>
    </g>
    <g id="objects">
      <rect data-object-id="stack-a" data-bbox="100 100 220 150"
        x="100" y="100" width="220" height="150" fill="#6B7280" stroke="#111827"
        stroke-width="1.2"/>
      <rect data-object-id="stack-b" data-bbox="180 140 220 150"
        x="180" y="140" width="220" height="150" fill="#E5E7EB" stroke="#111827"
        stroke-width="1.2"/>
      <rect data-object-id="cropped" data-bbox="870 510 60 50"
        x="870" y="510" width="60" height="50" fill="#6B7280" stroke="#111827"
        stroke-width="1.2"/>
    </g>
    <g id="labels">
      <text data-text-role="label" data-bbox="120 80 160 20" x="120" y="96"
        font-family="Arial" font-size="14" fill="#111827">Alpha</text>
      <text data-text-role="label" data-bbox="180 88 160 20" x="180" y="104"
        font-family="Arial" font-size="14" fill="#111827">Beta</text>
    </g>
  </g>
</svg>
""",
        encoding="utf-8",
    )

    codes = issue_codes(validate_semantic_svg(svg))

    assert "panel_gap_too_small" in codes
    assert "object_overlap" in codes
    assert "text_overlap" in codes
    assert "bbox_outside_viewbox" in codes
    assert "content_margin_violation" in codes


def test_external_svg_subtrees_are_valid_when_wrapped_by_semantic_object(
    tmp_path: Path,
) -> None:
    svg = tmp_path / "external.svg"
    svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg"
  data-figure-agent-svg="semantic-v1"
  data-journal-preset="nature-single"
  width="89mm" height="54mm" viewBox="0 0 890 540">
  <g id="semantic-layer">
    <g id="panels"><g id="panel-a" data-role="panel" data-bbox="40 40 810 460"/></g>
    <g id="objects">
      <g data-object-id="external-plot" data-bbox="120 100 320 220"
        data-external-svg="true">
        <svg viewBox="0 0 320 220">
          <text x="20" y="20" font-family="serif" font-size="99" fill="#FF00FF">
            raw generated text
          </text>
          <path d="M0 0L320 220" stroke="#BADBAD" stroke-width="9"/>
        </svg>
      </g>
    </g>
    <g id="labels">
      <text data-text-role="label" data-bbox="120 340 120 18" x="120" y="354"
        font-family="Arial" font-size="14" fill="#111827">External plot</text>
    </g>
  </g>
</svg>
""",
        encoding="utf-8",
    )

    assert validate_semantic_svg(
        svg,
        spec={
            "required_labels": ["External plot"],
            "required_objects": ["external-plot"],
        },
    ) == []


def test_export_rejects_invalid_semantic_source_before_running_converters(
    tmp_path: Path,
) -> None:
    from svg_export import export_artifacts  # noqa: PLC0415

    figure_dir = tmp_path / "fig_bad"
    (figure_dir / "source").mkdir(parents=True)
    (figure_dir / "source" / "fig_bad.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text>unstyled</text></svg>',
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    def runner(args: list[str], **_: object) -> None:
        calls.append(args)

    try:
        export_artifacts(figure_dir, "fig_bad", runner=runner)
    except ValueError as exc:
        assert "semantic SVG validation failed" in str(exc)
    else:
        raise AssertionError("invalid source exported without validation failure")

    assert calls == []


def test_export_renders_png_and_tiff_from_real_600_dpi_raster(tmp_path: Path) -> None:
    from svg_export import export_artifacts  # noqa: PLC0415

    figure_dir = tmp_path / "fig_export"
    (figure_dir / "source").mkdir(parents=True)
    (figure_dir / "source" / "fig_export.svg").write_text(
        """<svg xmlns="http://www.w3.org/2000/svg"
  data-figure-agent-svg="semantic-v1"
  data-journal-preset="nature-single"
  width="89mm" height="54mm" viewBox="0 0 890 540">
  <g id="semantic-layer">
    <g id="panels"><g id="panel-a" data-role="panel" data-bbox="40 40 810 460"/></g>
    <g id="objects"></g>
    <g id="labels">
      <text data-text-role="label" data-bbox="80 80 150 18" x="80" y="94"
        font-family="Arial" font-size="14" fill="#111827">Valid label</text>
    </g>
  </g>
</svg>
""",
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    def runner(args: list[str], **_: object) -> None:
        calls.append(args)
        output = Path(args[args.index("-o") + 1])
        if args[args.index("-f") + 1] == "png":
            Image.new("RGB", (2103, 1276), "white").save(output)
        else:
            output.write_bytes(b"%PDF-1.7\n")

    artifacts = export_artifacts(figure_dir, "fig_export", runner=runner)

    png_call = next(args for args in calls if args[args.index("-f") + 1] == "png")
    assert "-d" in png_call
    assert png_call[png_call.index("-d") + 1] == "600"
    assert "-p" in png_call
    assert png_call[png_call.index("-p") + 1] == "600"
    with Image.open(artifacts["tif"]) as image:
        assert image.size == (2103, 1276)
        assert image.info["dpi"] == (600.0, 600.0)


def test_schema_documentation_names_required_svg_contract() -> None:
    doc = (REPO_ROOT / "docs" / "semantic-svg-schema-v1.md").read_text(encoding="utf-8")

    assert 'data-figure-agent-svg="semantic-v1"' in doc
    assert 'id="semantic-layer"' in doc
    assert 'data-object-id="' in doc
    assert "vtracer underlay" in doc
    assert "not final source" in doc


def test_trap_depth_reference_example_is_semantic_and_editable() -> None:
    import yaml  # noqa: PLC0415

    figure_dir = REPO_ROOT / "examples" / "n3_trial_01_trap_depth"
    spec = yaml.safe_load((figure_dir / "spec.yaml").read_text(encoding="utf-8"))

    assert (figure_dir / spec["reference_image"]).is_file()
    assert validate_semantic_svg(
        figure_dir / "source" / "n3_trial_01_trap_depth.svg",
        spec=spec,
    ) == []


def test_primitive_fragments_replace_template_markers_with_semantic_svg() -> None:
    template = """<svg xmlns="http://www.w3.org/2000/svg">
  <g id="objects">
    <!-- figure-agent-fragment:test-band -->
  </g>
</svg>
"""
    primitive_doc = {
        "fragments": {
            "test-band": {
                "kind": "energy_band",
                "object_id": "unified-energy-diagram",
                "bbox": [100, 100, 320, 360],
                "cb_label": "CB",
                "vb_label": "VB",
                "shallow_label": "Shallow traps",
                "deep_label": "Deep traps",
                "density_label": "g(E_t)",
            }
        }
    }

    rendered = render_source_from_fragments(template, primitive_doc)

    assert "figure-agent-fragment:test-band" not in rendered
    assert 'data-generated-by="svg_primitives"' in rendered
    assert 'data-object-id="unified-energy-diagram"' in rendered
    assert 'data-object-id="shallow-trap-levels"' in rendered
    assert "Shallow traps" in rendered
    assert "Deep traps" in rendered


def _object_bbox(rendered: str, object_id: str) -> tuple[float, float, float, float]:
    import xml.etree.ElementTree as ET  # noqa: PLC0415

    root = ET.fromstring(rendered)
    for element in root.iter():
        if element.attrib.get("data-object-id") == object_id:
            return tuple(float(part) for part in element.attrib["data-bbox"].split())  # type: ignore[return-value]
    raise AssertionError(f"missing semantic object bbox: {object_id}")


def test_energy_band_v2_declares_paper_figure_geometry_objects() -> None:
    template = """<svg xmlns="http://www.w3.org/2000/svg">
  <g id="objects">
    <!-- figure-agent-fragment:test-band -->
  </g>
</svg>
"""
    primitive_doc = {
        "fragments": {
            "test-band": {
                "kind": "energy_band_v2",
                "object_id": "unified-energy-diagram",
                "bbox": [100, 100, 640, 760],
            }
        }
    }

    rendered = render_source_from_fragments(template, primitive_doc)

    assert 'data-generated-by="energy_band_v2"' in rendered
    for object_id in (
        "unified-energy-diagram",
        "energy-axis",
        "band-gap-window",
        "conduction-band",
        "valence-band",
        "shallow-trap-levels",
        "deep-trap-levels",
        "trap-depth-distribution",
        "density-axis",
    ):
        assert f'data-object-id="{object_id}"' in rendered
    for label in ("CB", "VB", "Shallow traps", "Deep traps", "g(E_t)", "E_t", "E_g"):
        assert label in rendered


def test_energy_band_v2_keeps_traps_between_cb_and_vb() -> None:
    template = """<svg xmlns="http://www.w3.org/2000/svg">
  <g id="objects">
    <!-- figure-agent-fragment:test-band -->
  </g>
</svg>
"""
    primitive_doc = {
        "fragments": {
            "test-band": {
                "kind": "energy_band_v2",
                "object_id": "unified-energy-diagram",
                "bbox": [100, 100, 640, 760],
            }
        }
    }

    rendered = render_source_from_fragments(template, primitive_doc)

    _, cb_y, _, cb_h = _object_bbox(rendered, "conduction-band")
    _, vb_y, _, _ = _object_bbox(rendered, "valence-band")
    _, gap_y, _, gap_h = _object_bbox(rendered, "band-gap-window")
    _, shallow_y, _, shallow_h = _object_bbox(rendered, "shallow-trap-levels")
    _, deep_y, _, deep_h = _object_bbox(rendered, "deep-trap-levels")
    _, density_y, _, density_h = _object_bbox(rendered, "density-axis")

    assert cb_y + cb_h < shallow_y < shallow_y + shallow_h < deep_y
    assert deep_y + deep_h < vb_y
    assert gap_y <= shallow_y
    assert deep_y + deep_h <= gap_y + gap_h
    assert density_y <= cb_y
    assert density_y + density_h >= vb_y


def test_js_backed_primitives_wrap_external_svg_with_semantic_metadata(
    monkeypatch,
) -> None:
    import subprocess  # noqa: PLC0415

    import svg_primitives  # noqa: PLC0415

    template = """<svg xmlns="http://www.w3.org/2000/svg">
  <g id="objects">
    <!-- figure-agent-fragment:test-plot -->
    <!-- figure-agent-fragment:test-molecule -->
  </g>
</svg>
"""
    primitive_doc = {
        "fragments": {
            "test-plot": {
                "kind": "vega_loglog_plot",
                "object_id": "external-plot",
                "bbox": [120, 80, 320, 220],
                "data": [{"x": 1, "y": 10}, {"x": 10, "y": 2}],
            },
            "test-molecule": {
                "kind": "openchemlib_molecule",
                "object_id": "external-molecule",
                "bbox": [460, 80, 180, 120],
                "smiles": "CCSCC",
            },
        }
    }
    calls: list[list[str]] = []

    def fake_run(
        args: list[str],
        *,
        input: str,
        text: bool,
        capture_output: bool,
        check: bool,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        assert input
        assert text is True
        assert capture_output is True
        assert check is False
        assert cwd == svg_primitives.REPO_ROOT
        stdout = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
            '<path d="M0 0L10 10"/></svg>'
        )
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(svg_primitives.subprocess, "run", fake_run)

    rendered = render_source_from_fragments(template, primitive_doc)

    assert len(calls) == 2
    assert 'data-object-id="external-plot"' in rendered
    assert 'data-object-id="external-molecule"' in rendered
    assert 'data-generated-by="vega_loglog_plot"' in rendered
    assert 'data-generated-by="openchemlib_molecule"' in rendered
    assert 'data-external-svg="true"' in rendered
    assert 'data-source-smiles="CCSCC"' in rendered
    assert "figure-agent-fragment:test-plot" not in rendered
    assert "figure-agent-fragment:test-molecule" not in rendered


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex is not installed")
def test_tikz_primitive_wraps_external_svg_and_preserves_bbox() -> None:
    primitive_doc = {
        "fragments": {
            "tikz-fixture": {
                "kind": "tikz",
                "object_id": "tikz-fixture",
                "bbox": [10, 20, 120, 80],
                "source": r"""
\begin{tikzpicture}
  \draw[draw=fgink,line width=1.2pt] (0,0) rectangle (2,1);
\end{tikzpicture}
""",
            }
        }
    }

    rendered = render_fragment("tikz-fixture", primitive_doc)

    assert "<svg" in rendered
    assert 'data-external-svg="true"' in rendered
    assert 'data-bbox="10 20 120 80"' in rendered


def test_n3_template_renders_to_valid_semantic_svg(tmp_path: Path) -> None:
    import yaml  # noqa: PLC0415

    figure_dir = REPO_ROOT / "examples" / "n3_trial_01_trap_depth"
    spec = yaml.safe_load((figure_dir / "spec.yaml").read_text(encoding="utf-8"))
    primitive_doc = load_primitive_doc(figure_dir / "primitives.yaml")
    rendered = render_source_from_fragments(
        (figure_dir / "source" / "n3_trial_01_trap_depth.template.svg").read_text(
            encoding="utf-8"
        ),
        primitive_doc,
    )
    source = tmp_path / "n3_trial_01_trap_depth.svg"
    source.write_text(rendered, encoding="utf-8")

    assert validate_semantic_svg(source, spec=spec) == []
