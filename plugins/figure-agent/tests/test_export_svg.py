from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "export_svg.sh"
GOLDEN_SVG = (
    REPO_ROOT
    / "examples"
    / "golden_trap_depth_picture"
    / "exports"
    / "golden_trap_depth_picture.svg"
)


def test_export_svg_rejects_output_without_svg_suffix(tmp_path: Path) -> None:
    """The shell wrapper must reject output paths that lack the .svg suffix
    so dvisvgm does not silently write a no-extension stray file."""
    pdf = tmp_path / "in.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%dummy\n")  # not a real PDF; dvisvgm is unreached
    no_ext_output = tmp_path / "out_without_suffix"
    result = subprocess.run(
        ["bash", str(SCRIPT), str(pdf), str(no_ext_output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "must end with .svg" in result.stderr
    assert not no_ext_output.exists()


def test_golden_export_preserves_text_as_semantic_nodes() -> None:
    """Regression guard: if the export chain regresses to outlining all text
    into glyph paths (as `pdftocairo -svg` does), the manuscript SVG becomes
    uneditable and unsearchable. dvisvgm --pdf preserves only labels rendered
    with the top-level fontspec/Arial setup (italic / math / macro-internal
    labels still outline because lualatex embeds them as CID fonts that
    dvisvgm rasterizes), so the threshold is calibrated to current behavior:
    ~20 nodes preserved. Anything substantially below that is a regression."""
    if not GOLDEN_SVG.exists():
        return  # fixture not regenerated locally; CI will exercise this
    svg_text = GOLDEN_SVG.read_text(encoding="utf-8")
    text_nodes = re.findall(r"<text\b", svg_text)
    assert len(text_nodes) >= 15, (
        f"Golden SVG has too few <text> nodes ({len(text_nodes)}); the export"
        " chain may have regressed to outlining glyphs into paths."
    )


def test_golden_export_contains_canonical_label_text() -> None:
    """At least the top-level non-italic non-math labels must survive as
    semantic <text> bodies. Catches a regression where text nodes exist but
    their content is mojibake (e.g., font-mapping breakage where every glyph
    becomes U+FFFD)."""
    if not GOLDEN_SVG.exists():
        return
    svg_text = GOLDEN_SVG.read_text(encoding="utf-8")
    text_bodies = re.findall(r"<text\b[^>]*>([^<]*)</text>", svg_text)
    joined = " ".join(text_bodies)
    # "Experiment" and "Energy" are the canonical canaries: both render with
    # plain sffamily and survive PDF -> SVG without outlining. If they go
    # missing the export chain has regressed.
    canonical_words = ["Experiment", "Energy"]
    missing = [w for w in canonical_words if w not in joined]
    assert missing == [], (
        f"Golden SVG <text> bodies are missing canonical labels: {missing}."
        " Likely a font-mapping or export-tool regression."
    )
