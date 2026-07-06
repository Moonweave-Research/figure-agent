from __future__ import annotations

import io

import panel_block_edits
import pytest

_VALID_ENTRY = """
- family_id: post_gap_label_relief
  template_id: v5f_panel_f_post_gap_label_relief_v1
  panel: F
  requires:
  - "% predecessor marker"
  applied_signature:
  - "% quality-search F post-gap label relief: clear label backgrounds"
  preserve_after: []
  replacements:
  - old: |-
      \\node at (1,1) {S60};
    new: |-
      \\node at (1,2) {S60};
  protected_labels: [S60, tau_d]
  goal_trigger:
  - [gap, label]
  - [relief, polish]
  goal_hypothesis:
    reason: goal requests gap label relief
    expected_detector_movement: label defect clears
    expected_visual_movement: label sits clear of the gap
    rollback_condition: reject if S60 disappears
"""


def test_panel_block_edit_entries_validate_and_round_trip() -> None:
    entries = panel_block_edits.load_panel_block_edits(io.StringIO(_VALID_ENTRY))
    assert len(entries) == 1
    entry = entries[0]
    assert entry.family_id == "post_gap_label_relief"
    assert "S60" in entry.protected_labels
    assert entry.replacements[0].old != entry.replacements[0].new
    assert entry.goal_trigger == (("gap", "label"), ("relief", "polish"))
    assert entry.goal_hypothesis["reason"] == "goal requests gap label relief"


def test_empty_document_yields_no_entries() -> None:
    assert panel_block_edits.load_panel_block_edits(io.StringIO("")) == []


def test_duplicate_family_id_is_rejected() -> None:
    doc = _VALID_ENTRY + _VALID_ENTRY.strip() + "\n"
    with pytest.raises(ValueError, match="duplicate family_id"):
        panel_block_edits.load_panel_block_edits(io.StringIO(doc))


def test_empty_match_block_is_rejected() -> None:
    doc = _VALID_ENTRY.replace("\\node at (1,1) {S60};", "")
    with pytest.raises(ValueError, match="empty old"):
        panel_block_edits.load_panel_block_edits(io.StringIO(doc))


def test_identical_match_and_replacement_is_rejected() -> None:
    doc = _VALID_ENTRY.replace("\\node at (1,2) {S60};", "\\node at (1,1) {S60};")
    with pytest.raises(ValueError, match="old == new"):
        panel_block_edits.load_panel_block_edits(io.StringIO(doc))


def test_missing_applied_signature_is_rejected() -> None:
    doc = _VALID_ENTRY.replace(
        '  - "% quality-search F post-gap label relief: clear label backgrounds"',
        "",
    ).replace("  applied_signature:\n", "  applied_signature: []\n")
    with pytest.raises(ValueError, match="applied_signature"):
        panel_block_edits.load_panel_block_edits(io.StringIO(doc))


def test_bundled_entries_load_and_validate() -> None:
    entries = panel_block_edits.load_bundled_panel_block_edits()
    assert entries, "bundled panel_block_edits.yaml must have at least one entry"
    seen: set[str] = set()
    for entry in entries:
        assert entry.applied_signature
        assert entry.replacements
        assert entry.family_id not in seen
        seen.add(entry.family_id)
