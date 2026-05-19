# Issue 9B Numeric Quality Score Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional advisory numeric score fields to `journal_grade_assessment`, validate their shape, and surface them in `/fig_loop` without changing any release, export, accepted, final-artifact, or human-gate behavior.

**Architecture:** Keep the current v1.2 critique schema and `figure-agent.journal-grade-assessment.v1` assessment schema. Numeric fields are optional additions inside `journal_grade_assessment`; if present they are all-or-nothing and advisory-only. `critique_adjudication.py` owns validation, `critique_brief.py` owns host prompt/schema emission, and `fig_loop.py` only surfaces validated-looking score fields with an explicit non-gate policy marker.

**Tech Stack:** Python stdlib, PyYAML, pytest, ruff, existing figure-agent command scripts.

---

## Source Of Truth

Read these first:

- `plugins/figure-agent/docs/superpowers/specs/2026-05-19-issue-9b-numeric-quality-score-calibration-design.md`
- `plugins/figure-agent/docs/superpowers/issues/2026-05-19-issue-9b-numeric-quality-score-calibration.md`
- `plugins/figure-agent/docs/milestones/2026-05-19-fresh-reaudit-dogfood-evidence.md`
- `plugins/figure-agent/scripts/critique_brief.py`
- `plugins/figure-agent/scripts/critique_adjudication.py`
- `plugins/figure-agent/scripts/fig_loop.py`
- `plugins/figure-agent/tests/test_critique_brief.py`
- `plugins/figure-agent/tests/test_critique_adjudication.py`
- `plugins/figure-agent/tests/test_fig_loop.py`

## Dirty Worktree Guard

Before editing, run from repo root:

```bash
git status --short --branch
```

Expected known unrelated dirty file:

```text
 M plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/subregion_iteration_log.md
```

Do not stage or modify that file in this issue. All 9B edits must stay in:

- `plugins/figure-agent/scripts/critique_brief.py`
- `plugins/figure-agent/scripts/critique_adjudication.py`
- `plugins/figure-agent/scripts/fig_loop.py`
- `plugins/figure-agent/tests/test_critique_brief.py`
- `plugins/figure-agent/tests/test_critique_adjudication.py`
- `plugins/figure-agent/tests/test_fig_loop.py`
- `plugins/figure-agent/docs/superpowers/issues/2026-05-19-issue-9b-numeric-quality-score-calibration.md`

## Task 1: Brief Contract Tests

**Files:**

- Modify: `plugins/figure-agent/tests/test_critique_brief.py`

- [ ] **Step 1: Add a failing test for score schema fields**

Add this test near the existing journal-grade assessment brief tests:

```python
def test_critique_brief_includes_advisory_numeric_score_schema(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "overall_score: 0-100" in brief
    assert "sub_scores:" in brief
    assert "storyline: 0-100" in brief
    assert "composition: 0-100" in brief
    assert "component_fidelity: 0-100" in brief
    assert "scientific_plausibility: 0-100" in brief
    assert "label_semantics: 0-100" in brief
    assert "polish: 0-100" in brief
    assert "reference_fidelity: 0-100" in brief
    assert "export_scale_readability: 0-100" in brief
    assert 'score_rationale: "<why these numbers describe only the current artifact>"' in brief
```

- [ ] **Step 2: Add a failing test for advisory-only policy text**

Add:

```python
def test_critique_brief_states_numeric_scores_are_advisory_not_gates(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "Scores are advisory fresh re-audit diagnostics" in brief
    assert "Scores are not cumulative progress meters" in brief
    assert "Scores cannot override blockers, human gates, stale exports" in brief
    assert "Do not invent journal acceptance probabilities" in brief
```

- [ ] **Step 3: Verify RED**

Run from `plugins/figure-agent`:

```bash
uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_advisory_numeric_score_schema tests/test_critique_brief.py::test_critique_brief_states_numeric_scores_are_advisory_not_gates
```

Expected: FAIL because the brief does not yet include numeric score fields or advisory-only policy text.

## Task 2: Brief Score Schema Implementation

**Files:**

- Modify: `plugins/figure-agent/scripts/critique_brief.py`

- [ ] **Step 1: Add score guidance to `_journal_grade_assessment()`**

Extend the existing Journal-Grade Fresh Re-Audit Assessment text with:

```python
Scores are advisory fresh re-audit diagnostics. They are optional but
recommended when the current artifact can be scored with concrete visual,
briefing, reference, or theory-guard evidence. Scores are not cumulative
progress meters; a later loop may score lower if a patch introduces a new
defect or makes an old defect visible. Scores cannot override blockers, human
gates, stale exports, final-artifact gates, accepted/golden gates, `quality_axes`
verdicts, or `benchmark_level`. Do not invent journal acceptance probabilities.
If you emit any numeric score, emit the complete `overall_score`, `sub_scores`,
and `score_rationale` block.
```

- [ ] **Step 2: Extend `_journal_grade_assessment_schema()`**

Add these lines after `rationale` in the schema helper:

```python
"  overall_score: 0-100",
"  sub_scores:",
"    storyline: 0-100",
"    composition: 0-100",
"    component_fidelity: 0-100",
"    scientific_plausibility: 0-100",
"    label_semantics: 0-100",
"    polish: 0-100",
"    reference_fidelity: 0-100",
"    export_scale_readability: 0-100",
'  score_rationale: "<why these numbers describe only the current artifact>"',
```

- [ ] **Step 3: Verify GREEN**

Run:

```bash
uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_advisory_numeric_score_schema tests/test_critique_brief.py::test_critique_brief_states_numeric_scores_are_advisory_not_gates
```

Expected: PASS.

## Task 3: Validator Tests

**Files:**

- Modify: `plugins/figure-agent/tests/test_critique_adjudication.py`

- [ ] **Step 1: Add a reusable score block helper**

Add near `_journal_grade_assessment_yaml()`:

```python
def _score_block_yaml(*, overall_score: float = 72) -> str:
    return (
        f"  overall_score: {overall_score}\n"
        "  sub_scores:\n"
        "    storyline: 78\n"
        "    composition: 70\n"
        "    component_fidelity: 55\n"
        "    scientific_plausibility: 82\n"
        "    label_semantics: 76\n"
        "    polish: 64\n"
        "    reference_fidelity: 80\n"
        "    export_scale_readability: 68\n"
        '  score_rationale: "current artifact only; not a progress score"\n'
    )
```

- [ ] **Step 2: Add failing validator tests**

Add:

```python
def test_build_adjudication_scaffold_accepts_v1_2_journal_score_block(tmp_path: Path) -> None:
    fig_dir = tmp_path / "fig_score"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        journal_assessment_yaml=_journal_grade_assessment_yaml() + _score_block_yaml(),
    )

    adjudication = build_adjudication_scaffold(fig_dir, critique)

    assert adjudication.fixture == "fig_score"


def test_build_adjudication_scaffold_rejects_out_of_range_overall_score(tmp_path: Path) -> None:
    fig_dir = tmp_path / "fig_score"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        journal_assessment_yaml=_journal_grade_assessment_yaml() + _score_block_yaml(overall_score=101),
    )

    with pytest.raises(CritiqueAdjudicationError, match="overall_score"):
        build_adjudication_scaffold(fig_dir, critique)


def test_build_adjudication_scaffold_rejects_partial_score_block(tmp_path: Path) -> None:
    fig_dir = tmp_path / "fig_score"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        journal_assessment_yaml=_journal_grade_assessment_yaml() + "  overall_score: 72\n",
    )

    with pytest.raises(CritiqueAdjudicationError, match="score block"):
        build_adjudication_scaffold(fig_dir, critique)


def test_build_adjudication_scaffold_rejects_missing_sub_score_key(tmp_path: Path) -> None:
    fig_dir = tmp_path / "fig_score"
    fig_dir.mkdir()
    score_yaml = _score_block_yaml().replace("    polish: 64\n", "")
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        journal_assessment_yaml=_journal_grade_assessment_yaml() + score_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="sub_scores"):
        build_adjudication_scaffold(fig_dir, critique)


def test_build_adjudication_scaffold_rejects_extra_sub_score_key(tmp_path: Path) -> None:
    fig_dir = tmp_path / "fig_score"
    fig_dir.mkdir()
    score_yaml = _score_block_yaml().replace(
        "    export_scale_readability: 68\n",
        "    export_scale_readability: 68\n    typography: 90\n",
    )
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        journal_assessment_yaml=_journal_grade_assessment_yaml() + score_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="sub_scores"):
        build_adjudication_scaffold(fig_dir, critique)
```

- [ ] **Step 3: Add a high-score-with-draft test**

Add:

```python
def test_build_adjudication_scaffold_allows_high_score_without_level_promotion(tmp_path: Path) -> None:
    fig_dir = tmp_path / "fig_score"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        journal_assessment_yaml=_journal_grade_assessment_yaml(level="draft") + _score_block_yaml(overall_score=95),
    )

    adjudication = build_adjudication_scaffold(fig_dir, critique)

    assert adjudication.fixture == "fig_score"
```

- [ ] **Step 4: Verify RED**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py::test_build_adjudication_scaffold_accepts_v1_2_journal_score_block tests/test_critique_adjudication.py::test_build_adjudication_scaffold_rejects_out_of_range_overall_score tests/test_critique_adjudication.py::test_build_adjudication_scaffold_rejects_partial_score_block tests/test_critique_adjudication.py::test_build_adjudication_scaffold_rejects_missing_sub_score_key tests/test_critique_adjudication.py::test_build_adjudication_scaffold_rejects_extra_sub_score_key tests/test_critique_adjudication.py::test_build_adjudication_scaffold_allows_high_score_without_level_promotion
```

Expected: FAIL because score fields are not validated yet. The first and high-score draft tests may pass before implementation if unknown fields are ignored; in that case the failing tests must still fail for the invalid-score cases.

## Task 4: Validator Implementation

**Files:**

- Modify: `plugins/figure-agent/scripts/critique_adjudication.py`

- [ ] **Step 1: Add score constants**

Near `_JOURNAL_BOTTLENECKS`, add:

```python
_JOURNAL_SCORE_KEYS = {
    "storyline",
    "composition",
    "component_fidelity",
    "scientific_plausibility",
    "label_semantics",
    "polish",
    "reference_fidelity",
    "export_scale_readability",
}
_JOURNAL_SCORE_BLOCK_KEYS = {"overall_score", "sub_scores", "score_rationale"}
```

- [ ] **Step 2: Add numeric range helper**

Add near other validation helpers:

```python
def _require_score_value(value: Any, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CritiqueAdjudicationError(f"{label} must be a number from 0 to 100")
    if value < 0 or value > 100:
        raise CritiqueAdjudicationError(f"{label} must be a number from 0 to 100")
```

- [ ] **Step 3: Add score-block validator**

Add:

```python
def _validate_journal_score_block(assessment: dict[str, Any], label: str) -> None:
    present = _JOURNAL_SCORE_BLOCK_KEYS & assessment.keys()
    if not present:
        return
    if present != _JOURNAL_SCORE_BLOCK_KEYS:
        missing = ", ".join(sorted(_JOURNAL_SCORE_BLOCK_KEYS - present))
        raise CritiqueAdjudicationError(f"{label} score block is incomplete; missing: {missing}")

    _require_score_value(assessment.get("overall_score"), f"{label}.overall_score")
    sub_scores = _require_mapping(assessment.get("sub_scores"), f"{label}.sub_scores")
    keys = set(sub_scores)
    if keys != _JOURNAL_SCORE_KEYS:
        missing = ", ".join(sorted(_JOURNAL_SCORE_KEYS - keys))
        extra = ", ".join(sorted(keys - _JOURNAL_SCORE_KEYS))
        details = []
        if missing:
            details.append(f"missing: {missing}")
        if extra:
            details.append(f"extra: {extra}")
        raise CritiqueAdjudicationError(
            f"{label}.sub_scores must contain exactly the required score keys"
            + (f" ({'; '.join(details)})" if details else "")
        )
    for key, value in sub_scores.items():
        _require_score_value(value, f"{label}.sub_scores.{key}")
    _require_non_empty_string(assessment, "score_rationale", label=label)
```

- [ ] **Step 4: Call the score-block validator**

Inside `_validate_journal_grade_assessment()`, after `_require_non_empty_string(assessment, "rationale", label=label)`, add:

```python
    _validate_journal_score_block(assessment, label)
```

- [ ] **Step 5: Verify GREEN**

Run the same targeted validator command from Task 3. Expected: PASS.

## Task 5: Fig Loop Score Surfacing Tests

**Files:**

- Modify: `plugins/figure-agent/tests/test_fig_loop.py`

- [ ] **Step 1: Extend `_journal_assessment()` helper**

Add optional fields to the helper signature:

```python
with_scores: bool = False,
overall_score: int = 72,
```

When `with_scores` is true, update the returned dict with:

```python
assessment.update(
    {
        "overall_score": overall_score,
        "sub_scores": {
            "storyline": 78,
            "composition": 70,
            "component_fidelity": 55,
            "scientific_plausibility": 82,
            "label_semantics": 76,
            "polish": 64,
            "reference_fidelity": 80,
            "export_scale_readability": 68,
        },
        "score_rationale": "current artifact only",
    }
)
```

- [ ] **Step 2: Add score surfacing test**

Add:

```python
def test_loop_surfaces_advisory_score_block(tmp_path: Path) -> None:
    fixture = _fixture_files(tmp_path, "score_demo")
    critique_hash = file_sha256(fixture["critique"])
    _write_v1_2_critique(
        fixture["critique"],
        _journal_assessment(critique_hash, with_scores=True, overall_score=72),
    )
    _write_adjudication(fixture["dir"], critique_hash)

    iteration = _run_loop(fixture["dir"], "inspect score")

    assessment = iteration["journal_grade_assessment"]
    assert assessment["overall_score"] == 72
    assert assessment["sub_scores"]["component_fidelity"] == 55
    assert assessment["score_rationale"] == "current artifact only"
    assert assessment["score_policy"] == "advisory_fresh_reaudit_not_gate"
    assert iteration["stop_reason"] == "status_action_required"
```

- [ ] **Step 3: Add stale high-score test**

Add:

```python
def test_loop_marks_high_score_stale_when_assessment_hash_mismatches(tmp_path: Path) -> None:
    fixture = _fixture_files(tmp_path, "score_demo")
    critique_hash = file_sha256(fixture["critique"])
    _write_v1_2_critique(
        fixture["critique"],
        _journal_assessment(
            "sha256:" + "0" * 64,
            with_scores=True,
            overall_score=99,
        ),
    )
    _write_adjudication(fixture["dir"], critique_hash)

    iteration = _run_loop(fixture["dir"], "inspect stale score")

    assessment = iteration["journal_grade_assessment"]
    assert assessment["overall_score"] == 99
    assert assessment["score_is_gateable"] is False
    assert assessment["evaluation_state"] == "stale"
```

- [ ] **Step 4: Add human-gate precedence test**

Add:

```python
def test_loop_high_score_does_not_override_human_gate(tmp_path: Path) -> None:
    fixture = _fixture_files(tmp_path, "score_demo")
    critique_hash = file_sha256(fixture["critique"])
    _write_v1_2_critique(
        fixture["critique"],
        _journal_assessment(critique_hash, with_scores=True, overall_score=96),
    )
    _write_adjudication(
        fixture["dir"],
        critique_hash,
        decisions=[
            {
                "finding_id": "C001",
                "decision": "needs_human",
                "reason": "domain decision",
                "patch_target": "",
                "evidence": "human note",
            }
        ],
    )

    iteration = _run_loop(fixture["dir"], "inspect human gate score")

    assert iteration["journal_grade_assessment"]["overall_score"] == 96
    assert iteration["stop_reason"] == "human_gate_required"
    assert iteration["escalation_level"] == "human_review_required"
```

- [ ] **Step 5: Verify RED**

Run:

```bash
uv run pytest -q tests/test_fig_loop.py::test_loop_surfaces_advisory_score_block tests/test_fig_loop.py::test_loop_marks_high_score_stale_when_assessment_hash_mismatches tests/test_fig_loop.py::test_loop_high_score_does_not_override_human_gate
```

Expected: FAIL because `score_policy` is not yet added and helper changes are not implemented.

## Task 6: Fig Loop Score Surfacing Implementation

**Files:**

- Modify: `plugins/figure-agent/scripts/fig_loop.py`

- [ ] **Step 1: Add score key constants**

Near journal assessment constants, add:

```python
_JOURNAL_SCORE_KEYS = {
    "storyline",
    "composition",
    "component_fidelity",
    "scientific_plausibility",
    "label_semantics",
    "polish",
    "reference_fidelity",
    "export_scale_readability",
}
```

- [ ] **Step 2: Add local score-block detection helper**

Add near `_journal_grade_assessment()`:

```python
def _has_complete_score_block(record: dict[str, Any]) -> bool:
    if not {"overall_score", "sub_scores", "score_rationale"} <= record.keys():
        return False
    sub_scores = record.get("sub_scores")
    return isinstance(sub_scores, dict) and set(sub_scores) == _JOURNAL_SCORE_KEYS
```

- [ ] **Step 3: Add score policy in `_journal_grade_assessment()`**

After setting `evidence_path`, add:

```python
    if _has_complete_score_block(record):
        record["score_policy"] = "advisory_fresh_reaudit_not_gate"
```

- [ ] **Step 4: Verify GREEN**

Run the targeted fig loop tests from Task 5. Expected: PASS.

## Task 7: Issue 9B Documentation Closeout

**Files:**

- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-19-issue-9b-numeric-quality-score-calibration.md`

- [ ] **Step 1: Update status**

Change:

```markdown
**Status:** deferred
```

to:

```markdown
**Status:** implemented as advisory-only numeric score contract; final commit pending.
```

- [ ] **Step 2: Replace blocked-by section**

Replace the blocked-by list with:

```markdown
## Preconditions

- [x] Issue 9A implemented.
- [x] Issue 9C reached N=5 valid v1.2 critique-grounded runs.
- [x] Human calibration decision: proceed with advisory-only scores, no score-driven gates.
```

- [ ] **Step 3: Add implementation notes**

Add:

```markdown
## Implementation Policy

- Numeric scores are optional v1.2 `journal_grade_assessment` fields.
- If any score field appears, `overall_score`, complete `sub_scores`, and `score_rationale` are required.
- Scores are fresh re-audit diagnostics, not cumulative progress meters.
- Scores may decrease after a patch.
- Scores cannot override `quality_axes`, `benchmark_level`, stale/freshness gates, human gates, export gates, final-artifact gates, or accepted/golden gates.
```

## Task 8: Final Verification

**Files:**

- No new edits unless verification reveals defects.

- [ ] **Step 1: Run targeted tests**

```bash
uv run pytest -q tests/test_critique_brief.py tests/test_critique_adjudication.py tests/test_fig_loop.py
```

Expected: all pass.

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest -q
```

Expected: all pass with the repository's existing skipped/xfail counts.

- [ ] **Step 3: Run lint and whitespace checks**

```bash
uv run ruff check .
git diff --check
```

Expected: both pass.

- [ ] **Step 4: Run plugin validation**

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all pass.

- [ ] **Step 5: Confirm unrelated dirty file remains unstaged**

From repo root:

```bash
git status --short --branch
git diff --cached --name-only
```

Expected: only intended 9B files are staged before commit; `plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/subregion_iteration_log.md` remains unstaged unless the user explicitly asks to include it.

## Commit Plan

Use two commits if implementation proceeds cleanly:

1. `Specify advisory numeric quality scores` already exists for the design spec.
2. `Implement advisory numeric quality scores` for tests, code, and Issue 9B closeout.

Do not commit unrelated fixture iteration-log changes in this issue.
