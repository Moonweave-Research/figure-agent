from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import authoring_rules  # noqa: E402


def test_pair001_rule_catalog_requires_source_anchored_rules() -> None:
    catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-pair001.md"
    )

    assert catalog["schema"] == "figure-agent.authoring-rules.v1"
    assert catalog["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert catalog["promotion_state"] == "n1_hypotheses"
    assert len(catalog["rules"]) >= 8
    for rule in catalog["rules"]:
        assert rule["id"].startswith("pair001.")
        assert rule["category"] in {
            "physics_semantics",
            "label_binding",
            "instrument_standard",
            "panel_layout",
            "style_lock",
        }
        assert rule["source"]["kind"] in {
            "iteration_comment",
            "critique_adjudication",
            "hand_patch_commit",
        }
        assert rule["source"]["locator"]
        assert rule["source"]["quote"]
        assert rule["transfer_policy"] in {"use_as_question", "use_as_constraint"}


def test_rule_catalog_rejects_unanchored_generic_guidance(tmp_path: Path) -> None:
    path = tmp_path / "bad.md"
    path.write_text(
        "---\n"
        "schema: figure-agent.authoring-rules.v1\n"
        "fixture: fig1_overview_v2_pair_001_vault\n"
        "promotion_state: n1_hypotheses\n"
        "rules:\n"
        "  - id: pair001.bad\n"
        "    category: panel_layout\n"
        "    rule: Make the figure beautiful.\n"
        "    source:\n"
        "      kind: iteration_comment\n"
        "      locator: ''\n"
        "      quote: ''\n"
        "    transfer_policy: use_as_constraint\n"
        "---\n",
        encoding="utf-8",
    )

    with pytest.raises(authoring_rules.AuthoringRuleError, match="source_anchor_missing"):
        authoring_rules.load_rule_catalog(path)
