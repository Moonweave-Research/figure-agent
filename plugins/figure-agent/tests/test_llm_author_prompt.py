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
