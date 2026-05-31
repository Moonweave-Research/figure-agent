from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_semantic_diff import (  # noqa: E402
    SVG_SEMANTIC_DIFF_RELATIVE_PATH,
    SvgSemanticDiffError,
    build_svg_semantic_diff_report,
    load_svg_semantic_diff_report,
    svg_semantic_diff_report_is_stale,
)


def _make_fixture(
    tmp_path: Path,
    *,
    source_svg: str,
    polished_svg: str,
    name: str = "demo_fig",
) -> Path:
    fig_dir = tmp_path / "examples" / name
    (fig_dir / "exports").mkdir(parents=True)
    (fig_dir / "polish").mkdir()
    (fig_dir / "exports" / f"{name}.svg").write_text(source_svg, encoding="utf-8")
    (fig_dir / "polish" / f"{name}.polished.svg").write_text(polished_svg, encoding="utf-8")
    return fig_dir


def _base_svg(body: str, *, frame: str = 'viewBox="0 0 100 50" width="100" height="50"') -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" {frame}>{body}</svg>\n'


def test_visual_only_polish_passes(tmp_path: Path) -> None:
    source = _base_svg('<text id="label-a" class="label">A</text><path id="arrow" d="M0 0 L1 1"/>')
    polished = _base_svg(
        '<text id="label-a" class="label" x="1">A</text><path id="arrow" d="M0 0 L1 1"/>'
    )
    fig_dir = _make_fixture(tmp_path, source_svg=source, polished_svg=polished)

    report_path = build_svg_semantic_diff_report(fig_dir)
    report = load_svg_semantic_diff_report(report_path, example_dir=fig_dir)

    assert report_path == fig_dir / SVG_SEMANTIC_DIFF_RELATIVE_PATH
    assert report["summary"]["state"] == "pass"
    assert report["findings"] == []
    assert svg_semantic_diff_report_is_stale(report_path, example_dir=fig_dir) is False


def test_missing_text_label_reports_identity_loss(tmp_path: Path) -> None:
    source = _base_svg(
        '<text id="label-a">V_s meter</text><path id="glyph-outline" d="M0 0 L1 1"/>'
    )
    polished = _base_svg('<path id="glyph-outline" d="M0 0 L1 1"/>')
    fig_dir = _make_fixture(tmp_path, source_svg=source, polished_svg=polished)

    report = load_svg_semantic_diff_report(
        build_svg_semantic_diff_report(fig_dir),
        example_dir=fig_dir,
    )

    assert report["summary"]["state"] == "semantic_backport_required"
    assert report["findings"][0]["kind"] == "text_identity_loss"
    assert "V_s meter" in report["findings"][0]["evidence"]


def test_changed_viewbox_reports_frame_change(tmp_path: Path) -> None:
    source = _base_svg('<text id="label-a">A</text>')
    polished = _base_svg(
        '<text id="label-a">A</text>',
        frame='viewBox="0 0 90 50" width="100" height="50"',
    )
    fig_dir = _make_fixture(tmp_path, source_svg=source, polished_svg=polished)

    report = load_svg_semantic_diff_report(
        build_svg_semantic_diff_report(fig_dir),
        example_dir=fig_dir,
    )

    assert report["summary"]["state"] == "semantic_backport_required"
    assert {finding["kind"] for finding in report["findings"]} == {"frame_change"}


@pytest.mark.parametrize(
    "feature",
    (
        '<foreignObject id="html"/>',
        '<image id="raster" href="https://example.com/a.png"/>',
        '<filter id="blur"/>',
        '<mask id="mask-a"/>',
    ),
)
def test_unsupported_svg_feature_reports_risk(tmp_path: Path, feature: str) -> None:
    source = _base_svg('<text id="label-a">A</text>')
    polished = _base_svg(f'<text id="label-a">A</text>{feature}')
    fig_dir = _make_fixture(tmp_path, source_svg=source, polished_svg=polished)

    report = load_svg_semantic_diff_report(
        build_svg_semantic_diff_report(fig_dir),
        example_dir=fig_dir,
    )

    assert report["summary"]["state"] == "semantic_backport_required"
    assert "unsupported_svg_feature" in {finding["kind"] for finding in report["findings"]}


def test_group_transform_reports_group_transform_risk(tmp_path: Path) -> None:
    source = _base_svg('<g id="panel"><text id="a">A</text><path id="p" d="M0 0 L1 1"/></g>')
    polished = _base_svg(
        '<g id="panel" transform="translate(12,0)">'
        '<text id="a">A</text><path id="p" d="M0 0 L1 1"/></g>'
    )
    fig_dir = _make_fixture(tmp_path, source_svg=source, polished_svg=polished)

    report = load_svg_semantic_diff_report(
        build_svg_semantic_diff_report(fig_dir),
        example_dir=fig_dir,
    )

    assert report["summary"]["state"] == "semantic_backport_required"
    assert "group_transform_risk" in {finding["kind"] for finding in report["findings"]}


def test_marker_or_path_inventory_change_reports_risk(tmp_path: Path) -> None:
    source = _base_svg(
        '<defs><marker id="arrow"/></defs>'
        '<path id="p" marker-end="url(#arrow)" d="M0 0 L1 1"/>'
    )
    polished = _base_svg('<defs><marker id="arrow"/></defs>')
    fig_dir = _make_fixture(tmp_path, source_svg=source, polished_svg=polished)

    report = load_svg_semantic_diff_report(
        build_svg_semantic_diff_report(fig_dir),
        example_dir=fig_dir,
    )

    assert "marker_or_path_change" in {finding["kind"] for finding in report["findings"]}


def test_changed_svg_marks_report_stale(tmp_path: Path) -> None:
    source = _base_svg('<text id="label-a">A</text>')
    fig_dir = _make_fixture(tmp_path, source_svg=source, polished_svg=source)
    report_path = build_svg_semantic_diff_report(fig_dir)

    (fig_dir / "polish" / "demo_fig.polished.svg").write_text(
        _base_svg('<text id="label-a">A</text><text id="b">B</text>'),
        encoding="utf-8",
    )

    assert svg_semantic_diff_report_is_stale(report_path, example_dir=fig_dir) is True


def test_malformed_report_hash_fails_cleanly(tmp_path: Path) -> None:
    source = _base_svg('<text id="label-a">A</text>')
    fig_dir = _make_fixture(tmp_path, source_svg=source, polished_svg=source)
    report_path = build_svg_semantic_diff_report(fig_dir)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["source_svg_hash"] = "sha256:not-a-real-hash"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(SvgSemanticDiffError, match="source_svg_hash"):
        load_svg_semantic_diff_report(report_path, example_dir=fig_dir)


def test_cli_writes_report(tmp_path: Path) -> None:
    source = _base_svg('<text id="label-a">A</text>')
    fig_dir = _make_fixture(tmp_path, source_svg=source, polished_svg=source)

    result = subprocess.run(
        [sys.executable, "scripts/svg_semantic_diff.py", str(fig_dir)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "wrote SVG semantic diff report" in result.stdout
    assert (fig_dir / SVG_SEMANTIC_DIFF_RELATIVE_PATH).is_file()
