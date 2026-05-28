from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_reference_pack import (  # noqa: E402
    CritiqueReferencePackError,
    load_optional_reference_pack,
    load_reference_pack,
)


def _write_valid_pack(path: Path) -> None:
    path.write_text(
        """
schema: figure-agent.critique-reference-pack.v1
fixture: demo
target_journal: Nature Communications
reference_class: mechanism_schematic
visual_ambition: high_impact_candidate
comparison_references:
  - id: R001
    source: paper
    path_or_citation: Doe et al., Nature Materials 2025
    role: journal_register
must_match_traits:
  - id: T001
    trait: clean cross-panel visual grammar
    reference_id: R001
must_avoid_traits:
  - id: A001
    trait: generic clip-art apparatus boxes
    severity: MAJOR
calibration_questions:
  - id: Q001
    question: Would the first glance read as a mechanism figure?
""".lstrip(),
        encoding="utf-8",
    )


def test_load_reference_pack_accepts_valid_pack(tmp_path: Path) -> None:
    pack_path = tmp_path / "critique_reference_pack.yaml"
    _write_valid_pack(pack_path)

    pack = load_reference_pack(pack_path)

    assert pack["schema"] == "figure-agent.critique-reference-pack.v1"
    assert pack["fixture"] == "demo"
    assert pack["target_journal"] == "Nature Communications"
    assert pack["comparison_references"][0]["id"] == "R001"
    assert pack["must_match_traits"][0]["reference_id"] == "R001"


def test_load_reference_pack_accepts_reference_learning_contract(tmp_path: Path) -> None:
    pack_path = tmp_path / "critique_reference_pack.yaml"
    _write_valid_pack(pack_path)
    pack_path.write_text(
        pack_path.read_text(encoding="utf-8")
        + """
reference_learning:
  schema: figure-agent.reference-learning.v1
  references:
    - path: reference/example.png
      roles:
        - style_anchor
        - density_reference
      allowed_transfer:
        - restrained palette
        - compact label hierarchy
      forbidden_transfer:
        - copy component topology
        - override physics story
      rationale: Use as journal-tone anchor, not content authority.
""",
        encoding="utf-8",
    )

    pack = load_reference_pack(pack_path)

    learning = pack["reference_learning"]
    assert learning["schema"] == "figure-agent.reference-learning.v1"
    assert learning["references"][0]["roles"] == ["style_anchor", "density_reference"]
    assert "copy component topology" in learning["references"][0]["forbidden_transfer"]


def test_load_reference_pack_rejects_unknown_reference_learning_role(
    tmp_path: Path,
) -> None:
    pack_path = tmp_path / "critique_reference_pack.yaml"
    _write_valid_pack(pack_path)
    pack_path.write_text(
        pack_path.read_text(encoding="utf-8")
        + """
reference_learning:
  schema: figure-agent.reference-learning.v1
  references:
    - path: reference/example.png
      roles:
        - copy_target
      allowed_transfer:
        - exact panel geometry
      forbidden_transfer:
        - none
      rationale: bad role
""",
        encoding="utf-8",
    )

    with pytest.raises(CritiqueReferencePackError, match="roles"):
        load_reference_pack(pack_path)


def test_load_reference_pack_rejects_empty_reference_learning_transfer_lists(
    tmp_path: Path,
) -> None:
    pack_path = tmp_path / "critique_reference_pack.yaml"
    _write_valid_pack(pack_path)
    pack_path.write_text(
        pack_path.read_text(encoding="utf-8")
        + """
reference_learning:
  schema: figure-agent.reference-learning.v1
  references:
    - path: reference/example.png
      roles:
        - style_anchor
      allowed_transfer: []
      forbidden_transfer:
        - copy component topology
      rationale: empty allowed list is ambiguous
""",
        encoding="utf-8",
    )

    with pytest.raises(CritiqueReferencePackError, match="allowed_transfer"):
        load_reference_pack(pack_path)


def test_load_reference_pack_rejects_empty_reference_learning_forbidden_transfer(
    tmp_path: Path,
) -> None:
    pack_path = tmp_path / "critique_reference_pack.yaml"
    _write_valid_pack(pack_path)
    pack_path.write_text(
        pack_path.read_text(encoding="utf-8")
        + """
reference_learning:
  schema: figure-agent.reference-learning.v1
  references:
    - path: reference/example.png
      roles:
        - style_anchor
      allowed_transfer:
        - restrained palette
      forbidden_transfer: []
      rationale: empty forbidden list is ambiguous
""",
        encoding="utf-8",
    )

    with pytest.raises(CritiqueReferencePackError, match="forbidden_transfer"):
        load_reference_pack(pack_path)


def test_load_optional_reference_pack_returns_none_when_missing(tmp_path: Path) -> None:
    assert load_optional_reference_pack(tmp_path) is None


def test_load_optional_reference_pack_rejects_fixture_mismatch(tmp_path: Path) -> None:
    example_dir = tmp_path / "actual"
    example_dir.mkdir()
    _write_valid_pack(example_dir / "critique_reference_pack.yaml")

    with pytest.raises(CritiqueReferencePackError, match="fixture"):
        load_optional_reference_pack(example_dir)


def test_load_reference_pack_rejects_malformed_yaml(tmp_path: Path) -> None:
    pack_path = tmp_path / "critique_reference_pack.yaml"
    pack_path.write_text("schema: [", encoding="utf-8")

    with pytest.raises(CritiqueReferencePackError, match="malformed YAML"):
        load_reference_pack(pack_path)


def test_load_reference_pack_rejects_bad_enum(tmp_path: Path) -> None:
    pack_path = tmp_path / "critique_reference_pack.yaml"
    _write_valid_pack(pack_path)
    text = pack_path.read_text(encoding="utf-8").replace(
        "visual_ambition: high_impact_candidate",
        "visual_ambition: impossible",
    )
    pack_path.write_text(text, encoding="utf-8")

    with pytest.raises(CritiqueReferencePackError, match="visual_ambition"):
        load_reference_pack(pack_path)


def test_load_reference_pack_rejects_unknown_trait_reference(tmp_path: Path) -> None:
    pack_path = tmp_path / "critique_reference_pack.yaml"
    _write_valid_pack(pack_path)
    text = pack_path.read_text(encoding="utf-8").replace(
        "reference_id: R001",
        "reference_id: R999",
    )
    pack_path.write_text(text, encoding="utf-8")

    with pytest.raises(CritiqueReferencePackError, match="reference_id"):
        load_reference_pack(pack_path)
