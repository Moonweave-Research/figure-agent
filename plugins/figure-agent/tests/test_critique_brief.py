from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image

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


def _write_real_render_pair(example_dir: Path, *, size: tuple[int, int] = (200, 100)) -> None:
    build_dir = example_dir / "build"
    image = Image.new("RGB", size, "white")
    image.save(build_dir / "review_demo.png")
    image.save(build_dir / "review_demo.pdf", "PDF", resolution=72)


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
    assert "\n```\n\n## Mandatory Audit Checklists" in brief
    assert "### D. Conceptual Completeness Audit\n" in brief
    assert "\n## Critique rubric" in brief


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
    assert "schema: figure-agent.critique.v1.1" in brief
    assert "panels:" in brief


def test_critique_brief_includes_mandatory_audit_checklists(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Mandatory Audit Checklists (host LLM MUST enumerate)" in brief
    assert "### A. Structural Completeness Audit" in brief
    assert "### B. Label-Target Matching Audit" in brief
    assert "### C. Physical Plausibility Audit" in brief
    assert "### D. Conceptual Completeness Audit" in brief


def test_critique_brief_output_format_includes_hash_manifest_metadata(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "generator: critique_brief.py" in brief
    assert "generator_version: sha256:" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.1" in brief
    assert "critique_input_hash: sha256:" in brief
    assert "audit_enumeration:" in brief
    assert brief.count("category: structural | physics | label_placement") == 2


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

    # All new source files must be older than the build PNG to pass freshness check
    old_time = 1_000_000.0
    for path in (spec_ref, other_ref, example_dir / "spec.yaml"):
        os.utime(path, (old_time, old_time))

    brief = generate_for(example_dir)

    assert "examples/review_demo/reference/foo.png" in brief
    # golden_target_001.png must NOT appear — spec takes precedence
    assert "golden_target_001.png" not in brief


def test_critique_brief_does_not_scan_reference_directory_without_spec_reference(
    tmp_path,
):
    """Reference grounding must be explicit in spec.yaml, not inferred from files."""
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    implicit_ref = ref_dir / "golden_target_001.png"
    implicit_ref.write_bytes(b"PNG")

    old_time = 1_000_000.0
    os.utime(implicit_ref, (old_time, old_time))

    brief = generate_for(example_dir)

    assert "Reference image (for drift detection)" not in brief
    assert "golden_target_001.png" not in brief


def test_critique_brief_allows_coordinate_hints_newer_than_png(tmp_path, capsys, monkeypatch):
    """coordinate_hints.yaml is critique context, not a render source."""
    example_dir = _write_example(tmp_path, section6="- invariant")
    hints = example_dir / "coordinate_hints.yaml"
    hints.write_text("metadata:\n  extraction_version: '0.3'\n", encoding="utf-8")
    # PNG is fresh against render sources but older than coordinate_hints.yaml.
    png_path = example_dir / "build" / "review_demo.png"
    old_time = 1_000_000.0
    png_time = 4_000_000_000.0
    for path in (
        example_dir / "review_demo.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
    ):
        os.utime(path, (old_time, old_time))
    os.utime(png_path, (png_time, png_time))
    os.utime(hints, (png_time + 100, png_time + 100))

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])
    assert main() == 0
    captured = capsys.readouterr()
    assert "run /fig_compile first" not in captured.err
    assert "# Critique brief — review_demo" in captured.out


def test_critique_brief_allows_reference_image_newer_than_png(
    tmp_path, capsys, monkeypatch
):
    """Reference image changes make critique stale, but do not make the render stale."""
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    reference = ref_dir / "foo.png"
    reference.write_bytes(b"PNG")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/foo.png\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    old_time = 1_000_000.0
    png_time = 4_000_000_000.0
    newer_time = png_time + 100
    for path in (
        example_dir / "review_demo.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
    ):
        os.utime(path, (old_time, old_time))
    os.utime(png_path, (png_time, png_time))
    os.utime(reference, (newer_time, newer_time))

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])
    assert main() == 0
    captured = capsys.readouterr()
    assert "run /fig_compile first" not in captured.err
    assert "examples/review_demo/reference/foo.png" in captured.out


def test_critique_brief_blocks_missing_declared_reference_without_fallback(
    tmp_path, capsys, monkeypatch
):
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    (ref_dir / "golden_target_001.png").write_bytes(b"OTHER")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels: []\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/missing.png\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])
    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "reference_image_missing: reference/missing.png" in captured.err
    assert "golden_target_001.png" not in captured.err


def test_critique_brief_adds_panel_reference_context_when_ref_and_bbox_present(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant", png=False)
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    Image.new("RGB", (40, 40), "white").save(ref_dir / "panel_a.png")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    reference_image: reference/panel_a.png\n"
        "    bbox_pdf_cm: [0, 0, 3.5, 1.75]\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    _write_real_render_pair(example_dir)
    png_path = example_dir / "build" / "review_demo.png"
    newer_time = 4_000_000_000.0
    os.utime(png_path, (newer_time, newer_time))

    brief = generate_for(example_dir)

    assert "## Per-panel reference contexts" in brief
    assert "Panel `a`" in brief
    assert "`examples/review_demo/reference/panel_a.png`" in brief
    assert "`examples/review_demo/build/panel_crops/a.png`" in brief
    assert (example_dir / "build" / "panel_crops" / "a.png").is_file()


def test_critique_brief_strips_panel_reference_path_whitespace(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant", png=False)
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    Image.new("RGB", (40, 40), "white").save(ref_dir / "panel_a.png")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    reference_image: ' reference/panel_a.png '\n"
        "    bbox_pdf_cm: [0, 0, 3.5, 1.75]\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    _write_real_render_pair(example_dir)
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "Panel `a`" in brief
    assert "`examples/review_demo/reference/panel_a.png`" in brief
    assert "Per-panel reference warnings" not in brief


def test_critique_brief_warns_and_skips_panel_reference_without_bbox(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    (ref_dir / "panel_a.png").write_bytes(b"PNG")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    reference_image: reference/panel_a.png\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    newer_time = 4_000_000_000.0
    os.utime(png_path, (newer_time, newer_time))

    brief = generate_for(example_dir)

    assert "WARN" in brief
    assert "Panel `a` declares reference_image but no bbox_pdf_cm" in brief
    assert "Per-panel reference contexts" not in brief


def test_critique_brief_warns_and_skips_missing_panel_reference_without_bbox(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    reference_image: reference/missing_panel.png\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "WARN" in brief
    assert "Panel `a` declares reference_image `reference/missing_panel.png`" in brief
    assert "Per-panel reference contexts" not in brief


def test_critique_brief_warns_and_skips_panel_bbox_without_reference_image(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    bbox_pdf_cm: [0, 0, 3.5, 1.75]\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    newer_time = 4_000_000_000.0
    os.utime(png_path, (newer_time, newer_time))

    brief = generate_for(example_dir)

    assert "WARN" in brief
    assert "Panel `a` declares bbox_pdf_cm but no reference_image" in brief
    assert "Per-panel reference contexts" not in brief


def test_critique_brief_warns_when_skipped_panel_reference_is_newer_than_png(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    ref_path = ref_dir / "panel_a.png"
    ref_path.write_bytes(b"PNG")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    reference_image: reference/panel_a.png\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    old_time = 1_000_000.0
    for path in (
        example_dir / "review_demo.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
    ):
        os.utime(path, (old_time, old_time))
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))
    os.utime(ref_path, (4_000_000_001.0, 4_000_000_001.0))

    brief = generate_for(example_dir)

    assert "Panel `a` declares reference_image but no bbox_pdf_cm" in brief


def test_critique_brief_includes_reference_conditioned_authoring_docs(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "authoring_contract.md").write_text(
        "# Authoring Contract\n\n"
        "## Theory Invariants\n\n"
        "- BLOCKER: keep topology linear.\n\n"
        "## Forbidden Transfers\n\n"
        "- Do not transfer network topology.\n\n"
        "## Source Limitations\n\n"
        "- coordinate_hints.yaml is absent.\n\n"
        "## Acceptance Rubric\n\n"
        "- BLOCKER rejects acceptance.\n",
        encoding="utf-8",
    )
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    (ref_dir / "reference_pack.md").write_text(
        "# Reference Pack\n\n"
        "| File | Role | Use | Do Not Transfer |\n"
        "|---|---|---|---|\n"
        "| `reference/a.png` | anti_reference | motif only | Do Not Transfer topology |\n",
        encoding="utf-8",
    )
    (example_dir / "authoring_plan.md").write_text(
        "# Authoring Plan\n\n"
        "## Patch Order\n\n"
        "1. Fix Row2-BR2.\n\n"
        "## Human Checkpoints\n\n"
        "- Confirm manuscript chemistry.\n",
        encoding="utf-8",
    )
    (example_dir / "theory_guard.md").write_text(
        "# Theory Guard\n\n"
        "| ID | Severity | Claim | Check Method | Pass/Fail Evidence |\n"
        "|---|---|---|---|---|\n"
        "| TG-A-001 | BLOCKER | topology is linear | source review | pass |\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## Reference-conditioned authoring context" in brief
    assert "### Authoring Contract" in brief
    assert "- BLOCKER: keep topology linear." in brief
    assert "- Do not transfer network topology." in brief
    assert "### Reference Pack" in brief
    assert "| `reference/a.png` | anti_reference | motif only | Do Not Transfer topology |" in brief
    assert "### Authoring Plan" in brief
    assert "1. Fix Row2-BR2." in brief
    assert "- Confirm manuscript chemistry." in brief
    assert "### Theory Guard" in brief
    assert "| TG-A-001 | BLOCKER | topology is linear | source review | pass |" in brief


def test_critique_brief_includes_subregion_active_set(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "subregion_iteration_log.md").write_text(
        "# Sub-Region Iteration Log\n\n"
        "## Active Target Set\n\n"
        "| State | Sub-region ID | Evidence | Notes |\n"
        "|---|---|---|---|\n"
        "| active target | G-2, G-7 | review | patch electrode and gap |\n"
        "| named but stable | D-1..D-3 | log | stable |\n\n"
        "## Iteration Log\n\n"
        "| Iteration | Sub-region ID | Problem | Patch Summary | Result | Follow-up |\n"
        "|---|---|---|---|---|---|\n"
        "| v7 | G-2, G-7 | setup weak | widened gap | improved | recheck |\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "### Sub-region Active Set" in brief
    assert "- Active targets: G-2, G-7" in brief
    assert "- Observed patch units: G-2, G-7" in brief
