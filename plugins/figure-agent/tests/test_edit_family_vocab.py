"""Contract tests for the edit-family controlled vocabulary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import edit_family_vocab  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_aliases_fold_into_canonical_without_collisions() -> None:
    canonical = set(edit_family_vocab.CANONICAL_EDIT_FAMILIES)
    aliases = edit_family_vocab.LEGACY_EDIT_FAMILY_ALIASES

    assert not canonical.intersection(aliases)
    assert set(aliases.values()) <= canonical
    assert all(
        description.strip() for description in edit_family_vocab.CANONICAL_EDIT_FAMILIES.values()
    )


def test_canonical_edit_family_folds_and_passes_unknown_history_through() -> None:
    assert edit_family_vocab.canonical_edit_family("label_reposition") == "label_reposition"
    assert edit_family_vocab.canonical_edit_family("label_reflow") == "label_reposition"
    assert edit_family_vocab.canonical_edit_family("never_seen_name") == "never_seen_name"


def test_validate_edit_family_accepts_canonical_and_folds_aliases() -> None:
    assert edit_family_vocab.validate_edit_family("density_reduce") == "density_reduce"
    assert edit_family_vocab.validate_edit_family("mechanism_redraw") == "subregion_redraw"


def test_validate_edit_family_rejects_unknown_names_with_vocabulary() -> None:
    with pytest.raises(ValueError, match="controlled vocabulary"):
        edit_family_vocab.validate_edit_family("panel_f_new_campaign_lane")
    with pytest.raises(ValueError, match="non-empty"):
        edit_family_vocab.validate_edit_family("  ")


def test_every_committed_experience_row_resolves_to_canonical() -> None:
    """Ratchet: the historical corpus is fully classified; new writes are
    validated, so an unresolvable family can only appear by bypassing both."""
    log_dir = REPO_ROOT / "docs" / "experience-log"
    unresolved: set[str] = set()
    rows = 0
    for log in sorted(log_dir.glob("*.jsonl")):
        for line in log.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            family = record.get("action", {}).get("edit_family")
            rows += 1
            folded = edit_family_vocab.canonical_edit_family(str(family))
            if folded not in edit_family_vocab.CANONICAL_EDIT_FAMILIES:
                unresolved.add(str(family))
    assert rows > 0
    assert not unresolved, f"unclassified edit families: {sorted(unresolved)}"
