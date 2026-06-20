from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from semantic_contracts import (  # noqa: E402
    SemanticContractError,
    collect_semantic_contracts,
    semantic_claim_questions,
)


def test_existing_specs_are_not_semantic_contract_opt_in() -> None:
    payload = collect_semantic_contracts({"panels": [{"id": "A", "caption": "plain"}]})

    assert payload == {
        "schema": "figure-agent.semantic-contracts.v1",
        "enabled": False,
        "semantic_claims": [],
        "locked_invariants": [],
    }


def test_opt_in_semantic_claims_and_locked_invariants_are_normalized() -> None:
    payload = collect_semantic_contracts(
        {
            "authoring_context_pack": {"enabled": True},
            "panels": [
                {
                    "id": "C",
                    "semantic_claims": [
                        {"id": "trap-depth", "claim": "Deep traps are harder to escape."}
                    ],
                    "locked_invariants": ["Energy increases upward."],
                }
            ],
        }
    )

    assert payload["enabled"] is True
    assert payload["semantic_claims"] == [
        {
            "panel_id": "C",
            "id": "trap-depth",
            "claim": "Deep traps are harder to escape.",
        }
    ]
    assert payload["locked_invariants"] == [
        {
            "panel_id": "C",
            "id": "C.invariant1",
            "invariant": "Energy increases upward.",
        }
    ]
    assert semantic_claim_questions(
        {
            "authoring_context_pack": {"enabled": True},
            "panels": [{"id": "C", "semantic_claims": ["Deep traps are harder to escape."]}],
        }
    ) == [
        "[C:C.claim1] Does the rendered panel visually support this claim without adding "
        "unstated physics? Deep traps are harder to escape."
    ]


def test_opt_in_rejects_empty_claims() -> None:
    with pytest.raises(SemanticContractError, match="claim_missing"):
        collect_semantic_contracts(
            {
                "authoring_context_pack": {"enabled": True},
                "panels": [{"id": "C", "semantic_claims": [{"id": "bad", "claim": ""}]}],
            }
        )
