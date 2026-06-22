# Issue 57 Real Fixture Audit Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lock the current real-fixture audit adoption state in a tested contract and document the next adoption gaps without editing figure source.

**Architecture:** Add a YAML contract under `tests/` that describes each real fixture's audit opt-ins and deferrals. Add one pytest module that compares the contract to each fixture's `spec.yaml` and companion pack files. Add one milestone document that summarizes the adoption matrix and explains why no new detector declarations were added in this slice.

**Tech Stack:** Python 3.12, pytest, PyYAML, existing `plugins/figure-agent/tests` real-fixture contract pattern.

---

### Task 1: Add The Failing Contract Test

**Files:**
- Create: `plugins/figure-agent/tests/test_real_fixture_audit_adoption.py`
- Create later: `plugins/figure-agent/tests/real_fixture_audit_adoption.yaml`

- [ ] **Step 1: Write the failing test**

```python
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


def _load_contracts() -> list[dict[str, Any]]:
    data = load_yaml_mapping(CONTRACT_PATH)
    fixtures = data.get("fixtures")
    assert isinstance(fixtures, list)
    return fixtures


def _load_spec(fixture: str) -> dict[str, Any]:
    spec_path = EXAMPLES_ROOT / fixture / "spec.yaml"
    assert spec_path.is_file(), f"missing spec.yaml for {fixture}"
    data = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    assert isinstance(data, dict)
    return data


def _ids(items: object) -> list[str]:
    assert isinstance(items, list)
    ids = [item.get("id") for item in items if isinstance(item, dict)]
    assert all(isinstance(item, str) and item for item in ids)
    return sorted(ids)


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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_real_fixture_audit_adoption.py
```

Expected: FAIL because `tests/real_fixture_audit_adoption.yaml` does not exist.

### Task 2: Add The Audit Adoption Contract

**Files:**
- Create: `plugins/figure-agent/tests/real_fixture_audit_adoption.yaml`

- [ ] **Step 1: Write the contract**

```yaml
fixtures:
  - fixture: fig1_overview_v2_pair_001_vault
    reference_image: true
    text_boundary_check_ids:
      - panel_e_hv_display_avoid_inside
      - panel_e_vs_meter_display_avoid_inside
      - panel_f_psu_display_avoid_inside
      - row2_contain_text
      - row2_de_column_rule
      - row2_ef_column_rule
    label_path_check_ids:
      - panel_c_deep_escape_curve
      - panel_c_mobility_edge_reference
    aesthetic_intent: true
    critique_reference_pack: false
    paper_aesthetic_context:
    journal_art_direction_playbook:
    adoption_status: adopted_high_risk
    rationale: row-2 apparatus and panel-C semantic paths already have deterministic checks.

  - fixture: smoke_trap_demo
    reference_image: false
    text_boundary_check_ids: []
    label_path_check_ids:
      - smoke_cb_reference_line
      - smoke_deep_trap_line
      - smoke_vb_reference_line
    aesthetic_intent: false
    critique_reference_pack: false
    paper_aesthetic_context:
    journal_art_direction_playbook:
    adoption_status: adopted_low_noise_smoke
    rationale: compact band diagram has three semantic horizontal-line checks.
```

Add entries for the remaining six fixtures with empty check ids and explicit
`adoption_status` values. Use `deferred_reference_only` for reference-backed
fixtures that need fixture-specific geometry before adding deterministic checks,
and `not_applicable_no_reference` for critique-not-required fixtures without
known low-noise hazards.

- [ ] **Step 2: Run test to verify it passes**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_real_fixture_audit_adoption.py
```

Expected: PASS.

### Task 3: Add The Human-Readable Milestone

**Files:**
- Create: `plugins/figure-agent/docs/milestones-archive/2026-05-28-real-fixture-audit-adoption.md`

- [ ] **Step 1: Write the milestone**

Include:

- summary of all eight real fixtures;
- which fixtures already have deterministic text-boundary or label-path checks;
- which fixtures are deferred and why;
- statement that no `.tex`, export, accepted, golden, or generated artifacts are changed;
- next issue handoff to Issue 58.

- [ ] **Step 2: Review the milestone against the YAML contract**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_real_fixture_audit_adoption.py
```

Expected: PASS.

### Task 4: Close Issue 57 And Verify

**Files:**
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-27-issue-57-real-fixture-audit-adoption.md`

- [ ] **Step 1: Update status and implementation notes**

Change `Status: proposed` to `Status: implemented` and record:

- contract file path;
- test file path;
- milestone file path;
- no fixture source edits;
- no generated artifacts committed.

- [ ] **Step 2: Run targeted verification**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_real_fixture_audit_adoption.py tests/test_label_path_proximity.py tests/test_text_boundary_clash.py
uv run ruff check tests/test_real_fixture_audit_adoption.py
git diff --check
```

Expected: all pass.

- [ ] **Step 3: Run final review**

Check:

- no active figure source changed;
- no generated build/export artifact staged;
- no fixture is silently omitted from the matrix;
- Issue 58 can consume the matrix as input.
