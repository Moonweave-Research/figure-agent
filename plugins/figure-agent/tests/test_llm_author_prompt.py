"""Tests for scripts/llm_author_prompt.py — LLM authoring prompt builder."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import llm_author_prompt  # noqa: E402
from llm_author_prompt import build_prompt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_substitution_for_fig3_fixture() -> None:
    fixture = REPO_ROOT / "examples" / "fig3_trapping_concept"
    if not fixture.exists():
        pytest.skip("fig3_trapping_concept fixture not present")
    result = build_prompt(fixture)
    assert "{{" not in result
    assert "fig3_trapping_concept" in result
    assert "cAmber" in result
    assert "IsoBlock" in result
    assert "deep trap" in result


def test_rendered_signatures_match_preamble_arity() -> None:
    """The signature shown to the LLM for each flagship macro must have a brace
    count matching that macro's `\\newcommand[N]` declared arity. This catches
    drift between the preamble's `\\newcommand` and its `% \\Name{...}: ...`
    signature comment — the failure mode that produced PR 4b's contract bugs.
    """
    sty_path = REPO_ROOT / "styles" / "polymer-paper-preamble.sty"
    sty_text = sty_path.read_text(encoding="utf-8")

    declared: dict[str, int] = {}
    for match in re.finditer(
        r"\\newcommand\{\\(IsoBlock|IsoCharge|GradSlab|IsoConeTip)\}\[(\d+)\]",
        sty_text,
    ):
        declared[match.group(1)] = int(match.group(2))

    signed: dict[str, int] = {}
    for match in re.finditer(r"^%\s*\\(\w+)((?:\{[^}]*\})+)\s*:", sty_text, re.MULTILINE):
        signed[match.group(1)] = match.group(2).count("{")

    for name, arity in declared.items():
        assert name in signed, (
            f"{name} declared with [{arity}] arity but lacks a "
            f"`% \\{name}{{...}}: ...` signature comment in the preamble"
        )
        assert signed[name] == arity, (
            f"{name}: \\newcommand declares [{arity}] arg(s) but signature "
            f"comment has {signed[name]} brace(s); update either the comment or arity"
        )


def test_rendered_prompt_omits_legacy_hardcoded_signatures() -> None:
    """The bridge previously rendered `\\IsoCharge{x}{y}{sign}` and similar
    multi-brace signatures that did not match the preamble's single-comma-arg
    API. Lock that out: the rendered prompt must not contain those wrong forms.
    """
    fixture = REPO_ROOT / "examples" / "fig3_trapping_concept"
    if not fixture.exists():
        pytest.skip("fig3_trapping_concept fixture not present")
    result = build_prompt(fixture)
    assert r"\IsoCharge{x}{y}{sign}" not in result
    assert r"\GradSlab{x}{y}{width}{height}" not in result
    assert r"\IsoConeTip{x}{y}{direction}" not in result
    assert r"\IsoCharge{x,y,sign}" in result
    assert r"\IsoBlock{w}{d}{h}{color}{hook}" in result


def test_missing_template_returns_exit_2(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(llm_author_prompt, "TEMPLATE_PATH", tmp_path / "nonexistent_template.md")
    spec = tmp_path / "spec.yaml"
    briefing = tmp_path / "briefing.md"
    spec.write_text("panels: []\n", encoding="utf-8")
    briefing.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        build_prompt(tmp_path)
    assert exc_info.value.code == 2


def test_missing_spec_returns_exit_1(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc_info:
        build_prompt(tmp_path)
    assert exc_info.value.code == 1


def _write_minimal_inputs(tmp_path: Path, selection_notes_yaml: str) -> None:
    """Write a minimal spec.yaml and briefing.md so build_prompt can run.

    selection_notes_yaml is the raw YAML fragment for the selection_notes
    field (or empty string to omit it entirely).
    """
    spec_text = "name: tmp\npanels: []\n"
    if selection_notes_yaml:
        spec_text += selection_notes_yaml
    (tmp_path / "spec.yaml").write_text(spec_text, encoding="utf-8")
    (tmp_path / "briefing.md").write_text(
        "## 1. What does this figure show?\n\nminimal test fixture.\n",
        encoding="utf-8",
    )


def test_selection_notes_plumbed_when_present(tmp_path: Path) -> None:
    """selection_notes body must appear in the rendered prompt."""
    notes = "selection_notes: |\n  Visual motifs to preserve:\n    - green polymer chain marker\n"
    _write_minimal_inputs(tmp_path, notes)
    result = build_prompt(tmp_path)
    assert "Visual motifs to preserve" in result
    assert "green polymer chain marker" in result
    # Fallback sentinel must not occupy the section body when content is present.
    assert "introduce new invariants.\n\n(none)" not in result


def test_selection_notes_strips_html_comments(tmp_path: Path) -> None:
    """HTML author-only comments must not leak — parity with parse_briefing."""
    notes = (
        "selection_notes: |\n"
        "  <!-- AUTHOR ONLY: revisit on 2026-05-15 -->\n"
        "  Visible directive for the LLM.\n"
    )
    _write_minimal_inputs(tmp_path, notes)
    result = build_prompt(tmp_path)
    assert "AUTHOR ONLY" not in result
    assert "2026-05-15" not in result
    assert "Visible directive for the LLM." in result


def test_selection_notes_fallback_when_absent(tmp_path: Path) -> None:
    """Spec without selection_notes key falls back to the short '(none)' sentinel.

    Matches the parity with `selected_preview` and `_section_body` fallbacks
    so an LLM does not parse the fallback as instruction.
    """
    _write_minimal_inputs(tmp_path, "")
    result = build_prompt(tmp_path)
    assert "### Selection notes (preview-grounded authoring guide)" in result
    # Priority paragraph precedes the placeholder, then fallback fills it.
    assert "introduce new invariants.\n\n(none)" in result
    assert "{{" not in result


def test_selection_notes_non_string_warns_and_coerces(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    """Non-string scalar (int / list / dict / bare YAML date) must warn to stderr
    naming the example dir and the encountered type, then coerce — never crash."""
    _write_minimal_inputs(tmp_path, "selection_notes: 42\n")
    result = build_prompt(tmp_path)
    captured = capfd.readouterr()
    assert "selection_notes" in captured.err
    assert tmp_path.name in captured.err
    assert "int" in captured.err
    assert "42" in result


def test_selection_notes_empty_after_html_strip_warns_and_falls_back(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    """If a user wrote content but it was all <!-- ... -->, warn so they don't
    silently lose work. Fallback to (none) afterward."""
    notes = "selection_notes: |\n  <!-- TODO write me -->\n  <!-- another note -->\n"
    _write_minimal_inputs(tmp_path, notes)
    result = build_prompt(tmp_path)
    captured = capfd.readouterr()
    assert "reduced to empty" in captured.err
    assert tmp_path.name in captured.err
    assert "introduce new invariants.\n\n(none)" in result


def test_priority_order_paragraph_present_in_output(tmp_path: Path) -> None:
    """The priority-order paragraph is the entire correctness rationale for letting
    selection_notes into the prompt. Lock it against silent template regressions."""
    _write_minimal_inputs(tmp_path, "")
    result = build_prompt(tmp_path)
    # Phrase fragments to tolerate the template's hard line wraps.
    assert "Priority order: §6 invariants" in result
    assert "§3 composition intent > selection notes" in result
    assert "honor §6 and ignore the conflicting note" in result
    assert "cannot introduce new invariants" in result


def test_selection_notes_preserves_backslashes(tmp_path: Path) -> None:
    """str.replace must preserve backslashes inside selection_notes (LaTeX fragments are valid)."""
    notes = "selection_notes: |\n  Use \\frac{1}{2} ratio for the trap-depth visual.\n"
    _write_minimal_inputs(tmp_path, notes)
    result = build_prompt(tmp_path)
    assert r"\frac{1}{2}" in result
