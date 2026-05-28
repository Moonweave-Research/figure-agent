from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import journal_art_direction_playbook  # noqa: E402
import paper_aesthetic_context  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PLUGIN_ROOT / "examples"
JOURNAL_PACK_DIR = EXAMPLES_DIR / "_journal_art_direction_playbooks"
PAPER_CONTEXT_DIR = EXAMPLES_DIR / "_paper_aesthetic_contexts"

EXPECTED_JOURNAL_PACKS = {
    "nc-main-text": {
        "target_journal": "Nature Communications",
        "venue_context": "main_text",
        "visual_maturity": "restrained",
    },
    "nature-materials-dense": {
        "target_journal": "Nature Materials",
        "venue_context": "main_text",
        "visual_maturity": "editorial",
    },
    "science-compact": {
        "target_journal": "Science",
        "venue_context": "main_text",
        "visual_maturity": "polished",
    },
    "graphical-abstract-expressive": {
        "target_journal": "Nature Communications",
        "venue_context": "graphical_abstract",
        "visual_maturity": "cover_like",
    },
}

EXPECTED_PAPER_CONTEXTS = {
    "nc-main-text-series": {
        "target_journal": "Nature Communications",
        "visual_maturity": "restrained",
        "density": "balanced",
    },
    "nature-materials-dense-series": {
        "target_journal": "Nature Materials",
        "visual_maturity": "editorial",
        "density": "dense",
    },
    "science-compact-series": {
        "target_journal": "Science",
        "visual_maturity": "polished",
        "density": "dense",
    },
    "graphical-abstract-expressive-series": {
        "target_journal": "Nature Communications",
        "visual_maturity": "cover_like",
        "density": "balanced",
    },
}


def _route_paths(pack: dict[str, object]) -> set[str]:
    raw_rules = pack.get("polish_route_rules")
    assert isinstance(raw_rules, list)
    paths = set()
    for rule in raw_rules:
        assert isinstance(rule, dict)
        recommended_path = rule.get("recommended_path")
        assert isinstance(recommended_path, str)
        paths.add(recommended_path)
    return paths


def test_catalog_journal_playbooks_load_with_expected_metadata() -> None:
    for playbook_id, expected in EXPECTED_JOURNAL_PACKS.items():
        path = JOURNAL_PACK_DIR / f"{playbook_id}.yaml"
        assert path.is_file(), f"missing catalog playbook: {path}"

        pack = journal_art_direction_playbook.load_journal_art_direction_playbook(path)

        assert pack["playbook_id"] == playbook_id
        for key, value in expected.items():
            assert pack[key] == value
        assert {"continue_tikz", "ready_for_svg_polish"} <= _route_paths(pack)


def test_catalog_main_text_playbooks_are_restrained_from_cover_contexts() -> None:
    for playbook_id in ("nc-main-text", "nature-materials-dense", "science-compact"):
        pack = journal_art_direction_playbook.load_journal_art_direction_playbook(
            JOURNAL_PACK_DIR / f"{playbook_id}.yaml"
        )

        assert pack["venue_context"] == "main_text"
        assert pack["visual_maturity"] != "cover_like"
        for anti_pattern in pack["anti_patterns"]:
            assert anti_pattern["preferred_route"] != "ready_for_svg_polish" or (
                anti_pattern["dimension"] == "hand_craft"
            )


def test_catalog_expressive_playbook_is_explicitly_not_main_text() -> None:
    pack = journal_art_direction_playbook.load_journal_art_direction_playbook(
        JOURNAL_PACK_DIR / "graphical-abstract-expressive.yaml"
    )

    assert pack["venue_context"] in {"graphical_abstract", "cover_like"}
    assert pack["visual_maturity"] == "cover_like"


def test_catalog_paper_contexts_load_with_expected_metadata() -> None:
    for paper_id, expected in EXPECTED_PAPER_CONTEXTS.items():
        path = PAPER_CONTEXT_DIR / f"{paper_id}.yaml"
        assert path.is_file(), f"missing catalog paper context: {path}"

        pack = paper_aesthetic_context.load_paper_aesthetic_context(path)

        assert pack["paper_id"] == paper_id
        for key, value in expected.items():
            assert pack[key] == value
        assert pack["must_avoid"]


def test_catalog_paper_contexts_do_not_apply_to_real_fixtures_by_default() -> None:
    for paper_id in EXPECTED_PAPER_CONTEXTS:
        pack = paper_aesthetic_context.load_paper_aesthetic_context(
            PAPER_CONTEXT_DIR / f"{paper_id}.yaml"
        )
        fixtures = {
            role["fixture"]
            for role in pack["figure_roles"]
            if isinstance(role, dict) and isinstance(role.get("fixture"), str)
        }

        assert not {
            "fig1_overview_v2_pair_001_vault",
            "fig1_overview_v2",
            "golden_trap_depth_picture",
        } & fixtures
