"""Real-fixture audit adoption contract for Issue 57."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

TESTS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_ROOT))

from real_fixture_contract_helpers import load_yaml_mapping  # noqa: E402

REPO_ROOT = TESTS_ROOT.parents[0]
EXAMPLES_ROOT = REPO_ROOT / "examples"
CONTRACT_PATH = TESTS_ROOT / "real_fixture_audit_adoption.yaml"
ADOPTION_STATUSES = {
    "adopted_high_risk",
    "adopted_low_noise_smoke",
    "deferred_reference_only",
    "deferred_geometry_needed",
    "not_applicable_no_reference",
}


def _load_contracts() -> list[dict[str, Any]]:
    data = load_yaml_mapping(CONTRACT_PATH)
    fixtures = data.get("fixtures")
    assert isinstance(fixtures, list)
    return fixtures


def _load_spec(fixture: str) -> dict[str, Any]:
    spec_path = EXAMPLES_ROOT / fixture / "spec.yaml"
    if not spec_path.is_file():
        pytest.skip(f"real fixture not present in this plugin tree: {fixture}")
    data = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    assert isinstance(data, dict)
    return data


def _real_fixture_names() -> list[str]:
    return sorted(
        path.parent.name
        for path in EXAMPLES_ROOT.glob("*/spec.yaml")
        if not path.parent.name.startswith("_")
    )


def _ids(items: object) -> list[str]:
    assert isinstance(items, list)
    ids = [item.get("id") for item in items if isinstance(item, dict)]
    assert all(isinstance(item, str) and item for item in ids)
    return sorted(ids)


def test_real_fixture_audit_adoption_contract_covers_all_real_fixtures() -> None:
    contracts = _load_contracts()
    contract_names = {contract["fixture"] for contract in contracts}
    assert set(_real_fixture_names()).issubset(contract_names)
    for contract in contracts:
        assert contract["adoption_status"] in ADOPTION_STATUSES
        assert isinstance(contract["rationale"], str)
        assert contract["rationale"].strip()
        if contract["adoption_status"] == "deferred_reference_only":
            assert contract["reference_image"]
        if contract["adoption_status"].startswith("adopted_"):
            assert contract["text_boundary_check_ids"] or contract["label_path_check_ids"]


@pytest.mark.parametrize("contract", _load_contracts(), ids=lambda item: item["fixture"])
def test_real_fixture_audit_adoption_contract(contract: dict[str, Any]) -> None:
    fixture = contract["fixture"]
    spec = _load_spec(fixture)
    example_dir = EXAMPLES_ROOT / fixture

    assert spec.get("name") == fixture
    assert bool(spec.get("reference_image")) == contract["reference_image"]
    assert _ids(spec.get("text_boundary_checks", [])) == sorted(
        contract["text_boundary_check_ids"]
    )
    assert _ids(spec.get("label_path_proximity_checks", [])) == sorted(
        contract["label_path_check_ids"]
    )
    assert (example_dir / "aesthetic_intent.yaml").is_file() == contract[
        "aesthetic_intent"
    ]
    assert (example_dir / "critique_reference_pack.yaml").is_file() == contract[
        "critique_reference_pack"
    ]
    assert spec.get("paper_aesthetic_context") == contract["paper_aesthetic_context"]
    assert spec.get("journal_art_direction_playbook") == contract[
        "journal_art_direction_playbook"
    ]
