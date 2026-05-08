from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import critique_brief  # noqa: E402
from critique_brief import generate_for, main  # noqa: E402


def _write_example(tmp_path: Path, *, section6: str | None = None, png: bool = True) -> Path:
    example_dir = tmp_path / "review_demo"
    build_dir = example_dir / "build"
    build_dir.mkdir(parents=True)
    (example_dir / "spec.yaml").write_text(
        """name: review_demo
panels:
  - id: a
    caption: demo panel
style_profile: polymer-default
""",
        encoding="utf-8",
    )
    briefing = """## 1. Topic

Trap-assisted retention schematic.

## 2. Vocabulary

CB, VB, E_t

## 3. Composition

- CB line above trap level.
- Capture arrow points from CB to trap.
"""
    if section6 is not None:
        briefing += f"""

## 6. Physics invariants

{section6}
"""
    (example_dir / "briefing.md").write_text(briefing, encoding="utf-8")
    (example_dir / "review_demo.tex").write_text(
        "\\documentclass{standalone}\n"
        "\\begin{document}\n"
        "\\begin{tikzpicture}\n"
        "\\draw (0,1) -- (2,1) node[right]{CB};\n"
        "\\draw[->] (1,1) -- (1,0) node[right]{$E_t$};\n"
        "\\end{tikzpicture}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    if png:
        (build_dir / "review_demo.png").write_bytes(b"png")
    return example_dir


def test_critique_brief_includes_invariants_when_section6_present(tmp_path):
    example_dir = _write_example(
        tmp_path,
        section6="- E_t must stay inside the bandgap.\n- Capture arrow must point CB to trap.",
    )

    brief = generate_for(example_dir)

    assert "## Physics invariants the figure MUST honor" in brief
    assert "- E_t must stay inside the bandgap." in brief
    assert "- Capture arrow must point CB to trap." in brief


def test_critique_brief_handles_missing_section6_gracefully(tmp_path):
    example_dir = _write_example(tmp_path, section6=None)

    brief = generate_for(example_dir)

    assert "(none provided" in brief
    assert "critic should infer plausible physics constraints from §1+§2" in brief


def test_critique_brief_errors_when_png_missing(tmp_path, capsys, monkeypatch):
    example_dir = _write_example(tmp_path, section6="- invariant", png=False)

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "run /fig_compile first" in captured.err


def test_critique_brief_embeds_full_tex_source(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    tex = (example_dir / "review_demo.tex").read_text(encoding="utf-8")
    assert "```tex\n" in brief
    for line_number, line in enumerate(tex.splitlines(), start=1):
        assert f"{line_number:4d}: {line}" in brief
    assert "\n```\n\n## Critique rubric" in brief


def test_critique_brief_uses_example_relative_png_path(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    absolute_png_path = str((example_dir / "build" / "review_demo.png").resolve())
    assert absolute_png_path not in brief
    assert "`examples/review_demo/build/review_demo.png`" in brief
    assert "host main loop via the Read tool" in brief


def test_critique_brief_errors_when_png_is_older_than_tex(tmp_path, capsys, monkeypatch):
    example_dir = _write_example(tmp_path, section6="- invariant")
    tex_path = example_dir / "review_demo.tex"
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (100, 100))
    os.utime(tex_path, (200, 200))

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "run /fig_compile first" in captured.err


def test_critique_brief_errors_when_png_is_older_than_briefing(tmp_path, capsys, monkeypatch):
    example_dir = _write_example(tmp_path, section6="- invariant")
    briefing_path = example_dir / "briefing.md"
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (100, 100))
    os.utime(briefing_path, (200, 200))

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "run /fig_compile first" in captured.err


def test_critique_brief_errors_when_png_is_older_than_style_lock(tmp_path, capsys, monkeypatch):
    example_dir = _write_example(tmp_path, section6="- invariant")
    style_path = tmp_path / "polymer-paper-preamble.sty"
    style_path.write_text("% style", encoding="utf-8")
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (100, 100))
    os.utime(style_path, (200, 200))
    monkeypatch.setattr(critique_brief, "STYLE_LOCK_PATH", style_path)
    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "run /fig_compile first" in captured.err
    assert "polymer-paper-preamble.sty" in captured.err


def test_critique_brief_includes_rubric_sections_A_and_B(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "### A. Physics correctness" in brief
    assert "### B. Aesthetic placement" in brief
    assert "schema: figure-agent.critique.v1" in brief


def test_critique_brief_uses_spec_reference_image_over_directory_scan(tmp_path):
    """spec.yaml reference_image declaration must take precedence over directory scan."""
    example_dir = _write_example(tmp_path, section6="- invariant")

    # Create a spec-declared reference image at a non-default path
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    spec_ref = ref_dir / "foo.png"
    spec_ref.write_bytes(b"PNG")
    # Also place a different image that the directory scan would find first
    other_ref = ref_dir / "golden_target_001.png"
    other_ref.write_bytes(b"OTHER")

    # Rewrite spec.yaml to declare reference_image
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/foo.png\n",
        encoding="utf-8",
    )

    brief = generate_for(example_dir)

    assert "examples/review_demo/reference/foo.png" in brief
    # golden_target_001.png must NOT appear — spec takes precedence
    assert "golden_target_001.png" not in brief
