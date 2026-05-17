# Human Gate Escalation Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/fig_loop` ask for human review only when the next action genuinely needs human/domain judgment, while routine command, patch, and stale-state work stays agent-actionable.

**Architecture:** Keep `needs_human` as the hard human-review gate, but add an explicit escalation taxonomy so status actions, safe patch handoffs, manual promotion approvals, and true human review are not conflated. The runner should expose machine-readable escalation fields in `iteration_001.json` and concise wording in `decision.md`.

**Tech Stack:** Python stdlib, existing `scripts/fig_loop.py`, `scripts/status.py`, `scripts/critique_adjudication.py`, pytest.

**Command roots:** Run test and plugin validation commands from `plugins/figure-agent`. Run `git add` and `git commit` commands from the worktree root.

---

## Current Problem

The current runtime behavior is safer after `8f683fe`, but the contract still has a vocabulary problem:

- `needs_human` correctly blocks patch handoff.
- `status_action_required` correctly reports compile/critique/export and local contract-refresh work without asking the user.
- `TRACKED_GOLDEN --force-golden`, `accepted: true`, and publication safety are human decisions, but they should not be described as the same kind of review gate as mechanism/topology ambiguity.
- Multiple actionable patch candidates can still be collapsed to the first `apply` decision, which is not a true "exactly one target" guarantee.

The next slice should make escalation explicit before any safe auto-patch pilot.

## Escalation Taxonomy

Use these levels in runner output:

| Level | Meaning | Ask user? | Patch handoff? |
|---|---|---:|---:|
| `none` | Loop is closed for the requested mode. | no | no |
| `agent_action_required` | User/agent should run an ordinary command or refresh a local loop contract, such as compile, critique, adjudication, or non-force export. | no | no |
| `patch_allowed` | Exactly one safe target is selected. | no | yes |
| `manual_approval_required` | A deliberate promotion or state-changing approval is needed, such as `--force-golden` or `accepted: true`. | yes, but only as an approval checkpoint | no |
| `human_review_required` | Domain judgment is required for mechanism, topology, reference role, publication safety, or conflicting reviewer signals. | yes | no |
| `ambiguous_patch_selection` | More than one actionable target exists or no single safe target can be chosen. | usually no; ask for adjudication refinement | no |

`human_review_required` should stay rare. It is not a synonym for every manual step.

## Issue Breakdown

### Issue 6A: Add Escalation Summary Fields

**Type:** AFK

**Blocked by:** None - can start immediately

**What to build:** Extend `/fig_loop` output with an escalation summary that distinguishes ordinary next commands, safe patch handoff, manual approvals, and true human review.

**Acceptance criteria:**

- [ ] `iteration_001.json` includes `escalation_level`, `requires_user_input`, and `requires_domain_review`.
- [ ] `decision.md` includes the escalation level in one line.
- [ ] Existing `stop_reason`, `active_patch_target`, `patch_handoff`, and `recommended_next_action` remain backward compatible.
- [ ] `status_action_required` maps to `agent_action_required`, not human review.
- [ ] `human_gate_required` maps to `human_review_required`.

### Issue 6B: Guard Against Multiple Apply Targets

**Type:** AFK

**Blocked by:** Issue 6A is helpful but not required

**What to build:** Make the "exactly one target" rule real by refusing to generate a patch handoff when `critique_adjudication.yaml` contains multiple `decision: apply` entries.

**Acceptance criteria:**

- [ ] One `apply` decision still produces `patch_target_recommended` and a non-null `patch_handoff`.
- [ ] Two or more `apply` decisions produce `ambiguous_patch_selection`.
- [ ] Ambiguous selection produces no `patch_handoff`.
- [ ] `recommended_next_action` asks to refine `critique_adjudication.yaml` to one selected target.
- [ ] Existing `needs_human` still takes precedence over `apply`.

### Issue 6C: Separate Manual Promotion Approval from Human Review

**Type:** AFK

**Blocked by:** Issue 6A

**What to build:** Teach `/fig_loop` to surface manual promotion decisions as approval checkpoints, not broad human-review gates.

**Acceptance criteria:**

- [ ] `TRACKED_GOLDEN` roll-forward next action maps to `manual_approval_required`.
- [ ] `accepted: false` / `NOT_ACCEPTED` finalization next action maps to `manual_approval_required` only when render, critique, adjudication, and export are otherwise closed.
- [ ] `manual_approval_required` never creates `patch_handoff`.
- [ ] `manual_approval_required` wording says exactly what approval is needed, such as force-golden roll-forward or acceptance declaration.
- [ ] Mechanism/topology/reference ambiguity remains `human_review_required`, not manual approval.

### Issue 6D: Keep Routine Freshness Work Agent-Actionable

**Type:** AFK

**Blocked by:** Issue 6A

**What to build:** Prevent compile/critique/adjudication/export freshness work from being phrased as human review.

**Acceptance criteria:**

- [ ] Missing render maps to `agent_action_required`.
- [ ] Missing/stale critique maps to `agent_action_required`.
- [ ] Missing/stale adjudication maps to `agent_action_required`.
- [ ] Non-golden stale export maps to `agent_action_required`.
- [ ] Reference input missing remains blocking but not a review request; it should be an input repair action.

### Issue 6E: Dogfood Escalation Policy on Pilot Fixture

**Type:** HITL for visual acceptance judgment, AFK for command evidence

**Blocked by:** Issues 6A-6D

**What to build:** Run the pilot fixture through the escalation policy and document whether the loop asks only at real decision points.

**Acceptance criteria:**

- [ ] Run `/fig_loop fig1_overview_v2_pair_001_vault --goal "Verify escalation policy on pilot fixture"` and record the newest `decision.md` summary.
- [ ] Confirm C004 remains resolved and does not request human review.
- [ ] Confirm `TRACKED_GOLDEN --force-golden` is surfaced as manual approval, not human review.
- [ ] Confirm no patch handoff is generated unless exactly one unresolved actionable finding exists.
- [ ] Document any remaining friction in `docs/milestones/2026-05-17-fig-loop-pilot.md`.

## Implementation Tasks

### Task 1: Add Escalation Classifier

**Files:**

- Modify: `scripts/fig_loop.py`
- Test: `tests/test_fig_loop.py`

- [ ] **Step 1: Write failing tests**

Add tests that assert these mappings:

```python
def test_loop_status_action_is_agent_action_required(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "loop_demo.tex").write_text("\\documentclass{standalone}\\n", encoding="utf-8")

    run_dir = run_loop(
        "loop_demo",
        "inspect status action",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["escalation_level"] == "agent_action_required"
    assert iteration["requires_user_input"] is False
    assert iteration["requires_domain_review"] is False
```

```python
def test_loop_human_gate_is_domain_review_required(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C002",
                "decision": "needs_human",
                "reason": "mechanism arrow semantics may change",
                "patch_target": "",
                "evidence": "",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "inspect human gate",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "human_gate_required"
    assert iteration["escalation_level"] == "human_review_required"
    assert iteration["requires_user_input"] is True
    assert iteration["requires_domain_review"] is True
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest -q tests/test_fig_loop.py::test_loop_status_action_is_agent_action_required tests/test_fig_loop.py::test_loop_human_gate_is_domain_review_required
```

Expected: both fail because `iteration_001.json` does not yet contain escalation fields.

- [ ] **Step 3: Implement minimal classifier**

Add this helper to `scripts/fig_loop.py` near `_axis_verdicts`:

```python
def _escalation_summary(loop_decision: dict[str, Any]) -> dict[str, Any]:
    stop_reason = loop_decision["stop_reason"]
    if stop_reason == "human_gate_required":
        level = "human_review_required"
    elif stop_reason == "patch_target_recommended":
        level = "patch_allowed"
    elif stop_reason in {
        "status_action_required",
        "missing_adjudication",
        "stale_adjudication",
        "invalid_adjudication",
        "reference_input_missing",
    }:
        level = "agent_action_required"
    elif stop_reason == "no_actionable_findings":
        level = "none"
    else:
        level = "none"

    return {
        "escalation_level": level,
        "requires_user_input": level in {"manual_approval_required", "human_review_required"},
        "requires_domain_review": level == "human_review_required",
    }
```

In `run_loop()`, compute `escalation = _escalation_summary(loop_decision)` and add `**escalation` to `iteration`.

In `_decision_markdown()`, add:

```python
f"- escalation_level: {escalation['escalation_level']}",
```

If `_decision_markdown()` does not receive `escalation`, extend its signature and call site.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
uv run pytest -q tests/test_fig_loop.py
```

Expected: all fig loop tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/fig_loop.py plugins/figure-agent/tests/test_fig_loop.py
git commit -m "Classify fig loop escalation levels"
```

### Task 2: Enforce One Apply Target

**Files:**

- Modify: `scripts/fig_loop.py`
- Test: `tests/test_fig_loop.py`

- [ ] **Step 1: Write failing test**

```python
def test_loop_stops_when_multiple_apply_decisions_make_patch_target_ambiguous(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "first overlap",
                "patch_target": "panel A",
                "evidence": "critique C001",
            },
            {
                "finding_id": "C002",
                "decision": "apply",
                "reason": "second overlap",
                "patch_target": "panel B",
                "evidence": "critique C002",
            },
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "ambiguous_patch_selection"
    assert iteration["active_patch_target"] is None
    assert iteration["patch_handoff"] is None
    assert iteration["escalation_level"] == "ambiguous_patch_selection"
    assert iteration["recommended_next_action"] == (
        "select exactly one apply decision in critique_adjudication.yaml"
    )
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
uv run pytest -q tests/test_fig_loop.py::test_loop_stops_when_multiple_apply_decisions_make_patch_target_ambiguous
```

Expected: fails because current runner chooses the first `apply`.

- [ ] **Step 3: Implement apply-decision collection**

Replace `_first_decision()` usage for `apply` with a helper:

```python
def _decisions_with_value(adjudication: dict[str, Any], decision: str) -> list[dict[str, Any]]:
    if adjudication["state"] != "fresh":
        return []
    return [item for item in adjudication.get("decisions", []) if item.get("decision") == decision]
```

In `_loop_decision()`:

```python
apply_decisions = _decisions_with_value(adjudication, "apply")
if len(apply_decisions) > 1:
    return {
        "stop_reason": "ambiguous_patch_selection",
        "recommended_next_action": (
            "select exactly one apply decision in critique_adjudication.yaml"
        ),
        "active_patch_target": None,
        "human_gate_status": "not_requested",
    }
if len(apply_decisions) == 1:
    apply_decision = apply_decisions[0]
    finding_id = apply_decision["finding_id"]
    patch_target = apply_decision["patch_target"]
    return {
        "stop_reason": "patch_target_recommended",
        "recommended_next_action": f"patch {finding_id}: {patch_target}",
        "active_patch_target": {
            "finding_id": finding_id,
            "patch_target": patch_target,
            "reason": apply_decision["reason"],
        },
        "human_gate_status": "not_requested",
    }
```

Extend `_escalation_summary()` so `ambiguous_patch_selection` maps to itself and does not require domain review by default.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
uv run pytest -q tests/test_fig_loop.py
```

Expected: all fig loop tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/fig_loop.py plugins/figure-agent/tests/test_fig_loop.py
git commit -m "Reject ambiguous fig loop patch targets"
```

### Task 3: Add Manual Approval Classification

**Files:**

- Modify: `scripts/fig_loop.py`
- Test: `tests/test_fig_loop.py`

- [ ] **Step 1: Write failing test for tracked golden approval**

Add this test to `tests/test_fig_loop.py`:

```python
def test_loop_force_golden_status_action_is_manual_approval_required(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "loop_demo.tex").write_text("\\documentclass{standalone}\n", encoding="utf-8")
    run_dir = run_loop(
        "loop_demo",
        "inspect tracked golden approval",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration_path = run_dir / "iteration_001.json"
    data = json.loads(iteration_path.read_text(encoding="utf-8"))
    data["stop_reason"] = "status_action_required"
    data["recommended_next_action"] = (
        "tracked golden artifact is intentionally stale; "
        "to roll forward run /fig_export loop_demo --force-golden."
    )

    escalation = _escalation_summary(data)
    assert escalation["escalation_level"] == "manual_approval_required"
    assert escalation["requires_user_input"] is True
    assert escalation["requires_domain_review"] is False
```

Also update the import line in `tests/test_fig_loop.py` to include `_escalation_summary`.

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
uv run pytest -q tests/test_fig_loop.py::test_loop_force_golden_status_action_is_manual_approval_required
```

Expected: fails because status action currently maps to `agent_action_required`.

- [ ] **Step 3: Implement approval detection**

In `_escalation_summary(loop_decision)`, read `recommended_next_action` before the generic `status_action_required` branch:

```python
recommended = loop_decision.get("recommended_next_action", "")
if stop_reason == "status_action_required" and "--force-golden" in recommended:
    level = "manual_approval_required"
elif stop_reason == "status_action_required" and "accepted: true" in recommended:
    level = "manual_approval_required"
```

Keep ordinary compile/critique/export actions as `agent_action_required`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
uv run pytest -q tests/test_fig_loop.py tests/test_status.py tests/test_run_export.py
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/fig_loop.py plugins/figure-agent/tests/test_fig_loop.py
git commit -m "Separate fig loop manual approvals"
```

### Task 4: Update Command Docs and Pilot Notes

**Files:**

- Modify: `commands/fig_loop.md`
- Modify: `docs/milestones/2026-05-17-fig-loop-pilot.md`
- Modify: `docs/superpowers/specs/2026-05-17-fig-loop-contract-design.md`

- [ ] **Step 1: Document escalation taxonomy**

Add the taxonomy table from this plan to `/fig_loop` docs in a concise form.

- [ ] **Step 2: Record dogfood expectation**

Update the pilot doc to state:

```markdown
The desired steady state is that `/fig_loop` asks for human/domain review only
for mechanism, topology, reference-role, publication-safety, or conflicting
reviewer judgments. Routine stale-state and single-target polish work should be
agent-actionable.
```

- [ ] **Step 3: Verify docs**

Run:

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add plugins/figure-agent/commands/fig_loop.md plugins/figure-agent/docs/milestones/2026-05-17-fig-loop-pilot.md plugins/figure-agent/docs/superpowers/specs/2026-05-17-fig-loop-contract-design.md
git commit -m "Document fig loop escalation policy"
```

## Final Verification

Run from `plugins/figure-agent`:

```bash
uv run pytest -q tests/test_fig_loop.py tests/test_status.py tests/test_run_export.py tests/test_critique_adjudication.py
uv run pytest
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected:

- No tests fail.
- `/fig_loop` still preserves old stop reason fields.
- Human review is requested only for `needs_human` or explicitly classified high-risk states.
- Manual approvals are distinct from domain review.
- Multi-target patch ambiguity no longer silently selects the first target.

## Review Checklist

- [ ] Can a routine stale critique/export state proceed without asking the user?
- [ ] Can exactly one minor visual patch produce a patch handoff?
- [ ] Can two patch candidates avoid accidental first-target selection?
- [ ] Can `needs_human` still block patch handoff?
- [ ] Are `--force-golden` and `accepted: true` approval checkpoints, not domain-review requests?
- [ ] Does the pilot fixture show the intended escalation level after the change?
