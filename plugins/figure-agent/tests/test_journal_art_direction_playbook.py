from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import journal_art_direction_playbook  # noqa: E402


def _example_dir(tmp_path: Path, fixture: str = "demo_fig") -> Path:
    example_dir = tmp_path / "examples" / fixture
    example_dir.mkdir(parents=True)
    return example_dir


def _write_pack(
    example_dir: Path,
    *,
    playbook_id: str = "nc-main-text",
) -> Path:
    pack_dir = example_dir.parent / "_journal_art_direction_playbooks"
    pack_dir.mkdir(parents=True, exist_ok=True)
    path = pack_dir / f"{playbook_id}.yaml"
    path.write_text(
        f"""
schema: figure-agent.journal-art-direction-playbook.v1
playbook_id: {playbook_id}
target_journal: Nature Communications
venue_context: main_text
visual_maturity: restrained
design_center:
  - id: editorial_restraint
    dimension: maturity
    instruction: prefer controlled scientific illustration over decoration
    priority: required
    positive_signals:
      - compact labels are subordinate to visual evidence
    anti_patterns:
      - poster-like saturation without semantic role
    evidence_prompts:
      - check print-scale restraint
  - id: typography_authority
    dimension: typography
    instruction: keep labels typeset and quiet
    priority: required
    positive_signals:
      - math subscripts align cleanly
    anti_patterns:
      - slide-like explanatory labels
    evidence_prompts:
      - inspect reduced-scale labels
  - id: whitespace_breathing
    dimension: whitespace
    instruction: keep dense regions readable
    priority: recommended
    positive_signals:
      - visible resting space around labels
    anti_patterns:
      - near-miss spacing that feels stacked
    evidence_prompts:
      - identify the densest region
anti_patterns:
  - id: toy_schematic
    dimension: maturity
    severity: MAJOR
    pattern: oversized arrows or generic rounded blocks
    preferred_route: continue_tikz
  - id: preset_macro_feel
    dimension: hand_craft
    severity: MINOR
    pattern: repeated elements look mechanically identical
    preferred_route: ready_for_svg_polish
positive_signals:
  - id: restrained_hero
    dimension: hierarchy
    signal: one first-fixation element without poster emphasis
    evidence_prompt: name the first visual object noticed
  - id: print_scale_calm
    dimension: typography
    signal: labels remain readable and quiet at target print scale
    evidence_prompt: check the print-scale crop
polish_route_rules:
  - id: tikz_until_semantics_close
    condition: semantic structure or relative placement still needs edits
    recommended_path: continue_tikz
    forbidden_actions:
      - hide semantic ambiguity behind SVG polish
  - id: svg_for_optical_finish
    condition: semantics are stable but optical spacing limits finish
    recommended_path: ready_for_svg_polish
    forbidden_actions:
      - move scientific components semantically
human_review_triggers:
  - id: taste_direction_conflict
    condition: playbook and fixture intent conflict
    severity: MAJOR
""".lstrip(),
        encoding="utf-8",
    )
    return path


def test_load_journal_art_direction_playbook_accepts_valid_pack(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir)

    pack = journal_art_direction_playbook.load_journal_art_direction_playbook(path)

    assert pack["schema"] == "figure-agent.journal-art-direction-playbook.v1"
    assert pack["playbook_id"] == "nc-main-text"
    assert pack["target_journal"] == "Nature Communications"
    assert [item["id"] for item in pack["design_center"]] == [
        "editorial_restraint",
        "typography_authority",
        "whitespace_breathing",
    ]


def test_load_journal_art_direction_playbook_rejects_unsafe_id(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "playbook_id: nc-main-text",
            "playbook_id: ../escape",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        journal_art_direction_playbook.JournalArtDirectionPlaybookError,
        match="safe id",
    ):
        journal_art_direction_playbook.load_journal_art_direction_playbook(path)


def test_load_journal_art_direction_playbook_rejects_filename_mismatch(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "playbook_id: nc-main-text",
            "playbook_id: other-playbook",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        journal_art_direction_playbook.JournalArtDirectionPlaybookError,
        match="filename",
    ):
        journal_art_direction_playbook.load_journal_art_direction_playbook(path)


def test_load_journal_art_direction_playbook_rejects_missing_ready_svg_rule(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "recommended_path: ready_for_svg_polish",
            "recommended_path: continue_tikz",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        journal_art_direction_playbook.JournalArtDirectionPlaybookError,
        match="ready_for_svg_polish",
    ):
        journal_art_direction_playbook.load_journal_art_direction_playbook(path)


def test_load_optional_journal_art_direction_playbook_returns_none_without_opt_in(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)
    _write_pack(example_dir)

    assert (
        journal_art_direction_playbook.load_optional_journal_art_direction_playbook(
            example_dir,
            {"name": "demo_fig"},
        )
        is None
    )


def test_load_optional_journal_art_direction_playbook_rejects_missing_pack(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)

    with pytest.raises(
        journal_art_direction_playbook.JournalArtDirectionPlaybookError,
        match="missing",
    ):
        journal_art_direction_playbook.load_optional_journal_art_direction_playbook(
            example_dir,
            {"name": "demo_fig", "journal_art_direction_playbook": "nc-main-text"},
        )


def test_journal_playbook_anchors_include_target_fields_and_item_ids(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir)
    pack = journal_art_direction_playbook.load_journal_art_direction_playbook(path)

    anchors = journal_art_direction_playbook.journal_playbook_anchors(pack)

    assert anchors == {
        "nc-main-text",
        "Nature Communications",
        "main_text",
        "restrained",
        "editorial_restraint",
        "typography_authority",
        "whitespace_breathing",
        "toy_schematic",
        "preset_macro_feel",
        "restrained_hero",
        "print_scale_calm",
        "tikz_until_semantics_close",
        "svg_for_optical_finish",
        "taste_direction_conflict",
    }
