"""Reproductions from the September 2026 quality-kernel audit."""

from pathlib import Path

import pytest
from inputs import normalize_bbox_pdf_cm, parse_spec
from status import CRITIQUE_BRIEFING_REQUIRED, compute_critique_state


@pytest.mark.parametrize(
    "text",
    [
        "- a\n- b\n",
        "panels: {a: {reference_image: missing.png}}\n",
        "panels: [broken]\n",
        "semantic_contract_required: true\nsemantic_contract_required: false\n",
        "panels: [{id: a}, {id: a}]\n",
        "accepted: 'false'\n",
        "final_size_contract: {target_width_mm: .nan}\n",
    ],
)
def test_invalid_spec_cannot_remove_a_gate(text: str) -> None:
    with pytest.raises(ValueError):
        parse_spec(text)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, ".nan"])
def test_bbox_rejects_nonfinite_and_boolean_coordinates(bad: object) -> None:
    with pytest.raises(ValueError):
        normalize_bbox_pdf_cm([0, 0, bad, 2], label="bbox")


def test_reference_free_fixture_cannot_skip_vision(tmp_path: Path) -> None:
    (tmp_path / "spec.yaml").write_text("name: demo\n")
    assert compute_critique_state(tmp_path, "demo") == CRITIQUE_BRIEFING_REQUIRED


def test_intro_briefing_is_usable_context(tmp_path: Path) -> None:
    from briefing_grounding import has_reference_free_grounding_context

    (tmp_path / "build").mkdir()
    (tmp_path / "build/visual_clash.json").write_text("{}")
    (tmp_path / "briefing.md").write_text(
        "# Overview\n\nA polymer mechanism schematic linking molecular disorder "
        "to the experimental charging and relaxation workflows.\n\n"
        "## 6. Physics invariants\n- Must preserve charge and ground ownership.\n"
    )
    assert has_reference_free_grounding_context(tmp_path)


def _text_pdf(path: Path, transform: str) -> None:
    stream = f"q {transform} cm BT /F1 10 Tf 10 10 Td (Label) Tj ET Q".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
    ]
    data = b"%PDF-1.4\n"
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(data)
    data += b"xref\n0 6\n0000000000 65535 f \n"
    data += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    data += f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(data)


@pytest.mark.parametrize(
    "transform,expected",
    [
        (".2 0 0 .2 0 0", 2),
        ("0 1 -1 0 90 0", 10),
    ],
)
def test_pdf_font_probe_accounts_for_scale_and_rotation(tmp_path, transform, expected):
    from check_print_size_contract import rendered_font_sizes_pt

    pdf = tmp_path / "text.pdf"
    _text_pdf(pdf, transform)
    assert rendered_font_sizes_pt(pdf) == pytest.approx([expected] * 5)


def test_custom_style_is_explicit_and_content_bound(tmp_path):
    import hashlib

    import yaml
    from lint_tex import lint

    preamble = tmp_path / "arial-preamble.sty"
    preamble.write_text(r"\definecolor{cGray}{RGB}{12,12,12}")
    tex = tmp_path / "demo.tex"
    tex.write_text(
        r"\documentclass{standalone}"
        + "\n"
        + r"\usepackage{arial-preamble}"
        + "\n"
        + r"\definecolor{cGray}{RGB}{0,0,0}"
    )
    assert any(item.category == "missing_preamble" for item in lint(tex))
    spec = {
        "style_lock": {
            "preamble": preamble.name,
            "sha256": "sha256:" + hashlib.sha256(preamble.read_bytes()).hexdigest(),
            "source_color_definitions": [r"\definecolor{cGray}{RGB}{0,0,0}"],
        }
    }
    (tmp_path / "spec.yaml").write_text(yaml.safe_dump(spec))
    assert not any(item.severity == "blocker" for item in lint(tex))
    tex.write_text(tex.read_text().replace("{0,0,0}", "{1,1,1}"))
    assert any(item.category == "definecolor" for item in lint(tex))
    preamble.write_text("modified")
    with pytest.raises(ValueError, match="hash mismatch"):
        lint(tex)
