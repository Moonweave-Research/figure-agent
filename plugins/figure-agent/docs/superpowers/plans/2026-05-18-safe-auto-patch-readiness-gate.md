# Safe Auto-Patch Readiness Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the read-only eligibility gate that decides whether a `/fig_loop` patch target is safe enough for a future auto-patch pilot, without editing figure source.

**Architecture:** Keep `/fig_loop` verify-only and keep the existing `patch_handoff` contract backward compatible. Add a small classifier that labels the selected target as `auto_patch_candidate`, `patch_assisted_only`, or `human_review_required`, with explicit allowed/blocked reasons. This prepares Issue 5 without implementing hidden auto-editing.

**Tech Stack:** Python stdlib, existing `scripts/fig_loop.py`, existing `tests/test_fig_loop.py`, pytest, ruff.

---

## Non-Developer Summary

The next step is not to let the plugin rewrite figures by itself. The next step is to add a safety checkpoint that answers one question:

> "If the loop found exactly one thing to fix, is this the kind of thing an automatic patcher may eventually be allowed to touch?"

The answer must be machine-readable:

- `auto_patch_candidate`: a small visual/layout issue, such as label spacing, clipping, palette/style, or whitespace.
- `patch_assisted_only`: a human or outer agent may patch it, but the plugin should not auto-edit it.
- `human_review_required`: the issue touches science, mechanism, topology, reference interpretation, accepted/golden state, or publication safety.

This means we keep the current safe behavior: the plugin recommends, records, and checks. It still does not secretly edit `.tex`.

## File Structure

- Modify: `plugins/figure-agent/scripts/fig_loop.py`
  - Add read-only auto-patch eligibility classification.
  - Attach the classification to `iteration_001.json` only when a single patch target exists.
  - Do not change source files, compile/export behavior, acceptance behavior, or critique behavior.
- Modify: `plugins/figure-agent/tests/test_fig_loop.py`
  - Add focused tests for safe, unsafe, and human-review classifications.
- Modify: `plugins/figure-agent/commands/fig_loop.md`
  - Document that eligibility is advisory and read-only.
- Modify: `plugins/figure-agent/docs/superpowers/specs/2026-05-17-fig-loop-contract-design.md`
  - Mark Issue 5A as a readiness gate before any safe auto-patch pilot.

## Eligibility Policy

Allowed candidate classes:

- label offset
- text overlap
- clipping
- whitespace balance
- palette/style violation
- line weight/style mismatch

Blocked classes:

- chemistry topology
- physical mechanism
- causal arrow semantics
- theory guard evidence
- reference transfer or interpretation
- accepted/golden/export/build state
- critique text mutation
- broad refactor
- more than one target

Non-candidate class:

- generic label wording or copy edits without a concrete geometry defect

Classification outputs:

```json
{
  "auto_patch_eligibility": {
    "level": "auto_patch_candidate",
    "target_type": "finding",
    "target_id": "C001",
    "allowed_reasons": ["label offset"],
    "blocked_reasons": [],
    "required_evidence": [
      "before compile/export evidence",
      "after compile/export evidence",
      "rollback path"
    ],
    "may_edit": false
  }
}
```

`may_edit` must be `false` in this slice.

## Task 1: Add Safe Candidate Classification

**Files:**

- Modify: `plugins/figure-agent/tests/test_fig_loop.py`
- Modify: `plugins/figure-agent/scripts/fig_loop.py`

- [ ] **Step 1: Write the failing test**

Add a test showing that a single label/spacing finding gets classified as an auto-patch candidate, but still does not grant edit permission.

```python
def test_loop_marks_label_spacing_patch_as_auto_patch_candidate(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "label overlaps arrow; adjust label offset and spacing",
                "patch_target": "panel A label cluster",
                "evidence": "critique.md C001",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "patch_target_recommended"
    assert iteration["auto_patch_eligibility"] == {
        "level": "auto_patch_candidate",
        "target_type": "finding",
        "target_id": "C001",
        "allowed_reasons": ["label offset", "text overlap"],
        "blocked_reasons": [],
        "required_evidence": [
            "before compile/export evidence",
            "after compile/export evidence",
            "rollback path",
        ],
        "may_edit": False,
    }
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_loop.py::test_loop_marks_label_spacing_patch_as_auto_patch_candidate
```

Expected: FAIL because `auto_patch_eligibility` does not exist yet.

- [ ] **Step 3: Implement minimal classifier**

Add these constants and helper in `scripts/fig_loop.py` near `_loop_decision()`:

```python
_AUTO_PATCH_ALLOWED_TERMS = {
    "label offset": ("label", "offset"),
    "text overlap": ("overlap",),
    "clipping": ("clip",),
    "whitespace balance": ("whitespace",),
    "palette/style": ("palette", "style"),
    "line weight/style": ("line weight", "stroke weight"),
}

_AUTO_PATCH_BLOCKED_TERMS = {
    "chemistry topology": ("chemistry", "topology", "molecule", "bond"),
    "physical mechanism": ("mechanism", "causal", "physics"),
    "causal arrow semantics": ("arrow semantics", "causal arrow"),
    "theory guard evidence": ("theory", "guard"),
    "reference interpretation": ("reference", "interpretation"),
    "accepted/golden/export/build state": ("accepted", "golden", "export", "build"),
    "critique mutation": ("critique.md", "critique mutation"),
    "broad refactor": ("refactor", "rewrite"),
}


def _auto_patch_eligibility(
    loop_decision: dict[str, Any],
    patch_handoff: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not patch_handoff:
        return None

    haystack = " ".join(
        str(value)
        for value in (
            patch_handoff.get("target_id"),
            patch_handoff.get("patch_target"),
            patch_handoff.get("reason"),
            loop_decision.get("recommended_next_action"),
        )
        if value
    ).lower()

    allowed = [
        name
        for name, terms in _AUTO_PATCH_ALLOWED_TERMS.items()
        if any(term in haystack for term in terms)
    ]
    blocked = [
        name
        for name, terms in _AUTO_PATCH_BLOCKED_TERMS.items()
        if any(term in haystack for term in terms)
    ]

    if blocked:
        level = "human_review_required"
    elif allowed:
        level = "auto_patch_candidate"
    else:
        level = "patch_assisted_only"

    return {
        "level": level,
        "target_type": patch_handoff["target_type"],
        "target_id": patch_handoff["target_id"],
        "allowed_reasons": allowed,
        "blocked_reasons": blocked,
        "required_evidence": [
            "before compile/export evidence",
            "after compile/export evidence",
            "rollback path",
        ],
        "may_edit": False,
    }
```

In `run_loop()`, after `patch_handoff` is computed, add:

```python
auto_patch_eligibility = _auto_patch_eligibility(loop_decision, patch_handoff)
```

Then include this key in the `iteration` dictionary:

```python
"auto_patch_eligibility": auto_patch_eligibility,
```

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_loop.py::test_loop_marks_label_spacing_patch_as_auto_patch_candidate
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/fig_loop.py plugins/figure-agent/tests/test_fig_loop.py
git commit -m "Classify fig loop auto-patch eligibility"
```

## Task 2: Block Science and Mechanism Targets

**Files:**

- Modify: `plugins/figure-agent/tests/test_fig_loop.py`
- Modify: `plugins/figure-agent/scripts/fig_loop.py`

- [ ] **Step 1: Write the failing test**

Add a test proving that mechanism/topology/reference-like targets cannot become auto-patch candidates.

```python
def test_loop_marks_mechanism_patch_as_human_review_required(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C002",
                "decision": "apply",
                "reason": "causal arrow semantics change the physical mechanism",
                "patch_target": "panel B mechanism arrow",
                "evidence": "critique.md C002",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "patch_target_recommended"
    assert iteration["patch_handoff"] is not None
    assert iteration["auto_patch_eligibility"]["level"] == "human_review_required"
    assert iteration["auto_patch_eligibility"]["may_edit"] is False
    assert iteration["auto_patch_eligibility"]["blocked_reasons"] == [
        "physical mechanism",
        "causal arrow semantics",
    ]
```

- [ ] **Step 2: Run test to verify RED or confirm existing classifier covers it**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_loop.py::test_loop_marks_mechanism_patch_as_human_review_required
```

Expected: PASS if Task 1 already included the blocked terms exactly. If it fails, update `_AUTO_PATCH_BLOCKED_TERMS` only enough to pass this test.

- [ ] **Step 3: Run focused tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_loop.py::test_loop_marks_label_spacing_patch_as_auto_patch_candidate tests/test_fig_loop.py::test_loop_marks_mechanism_patch_as_human_review_required
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add plugins/figure-agent/scripts/fig_loop.py plugins/figure-agent/tests/test_fig_loop.py
git commit -m "Block unsafe fig loop auto-patch classes"
```

## Task 3: Document the Read-Only Boundary

**Files:**

- Modify: `plugins/figure-agent/commands/fig_loop.md`
- Modify: `plugins/figure-agent/docs/superpowers/specs/2026-05-17-fig-loop-contract-design.md`

- [ ] **Step 1: Update `/fig_loop` command docs**

Add this section to `commands/fig_loop.md` near the patch handoff description:

```markdown
## Auto-Patch Eligibility

`/fig_loop` may report `auto_patch_eligibility` when exactly one patch handoff
exists. This is advisory and read-only.

- `auto_patch_candidate`: the target appears to be a small label, spacing,
  clipping, palette/style, or line-weight issue.
- `patch_assisted_only`: the target can be handed to an outer agent or human,
  but is not classified as safe for future automation.
- `human_review_required`: the target touches science, mechanism, topology,
  reference interpretation, accepted/golden state, or publication safety.

In this version, `may_edit` is always `false`. The runner must not edit figure
source, critique output, exports, accepted metadata, or golden contracts.
```

- [ ] **Step 2: Update contract spec**

Under Issue 5 in `docs/superpowers/specs/2026-05-17-fig-loop-contract-design.md`, add:

```markdown
### Issue 5A: Safe Auto-Patch Readiness Gate

Before any safe auto-patch runner exists, `/fig_loop` must classify a single
patch handoff as `auto_patch_candidate`, `patch_assisted_only`, or
`human_review_required`. This classification is read-only and must set
`may_edit: false`.

Acceptance:

- no source or artifact mutation,
- one selected target only,
- candidate classes limited to label/style/spacing/clipping/whitespace,
- mechanism, topology, theory, reference interpretation, accepted/golden, and
  publication-safety changes blocked,
- before/after evidence and rollback path listed as required future evidence.
```

- [ ] **Step 3: Verify docs formatting**

Run:

```bash
cd plugins/figure-agent
git diff --check
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add plugins/figure-agent/commands/fig_loop.md plugins/figure-agent/docs/superpowers/specs/2026-05-17-fig-loop-contract-design.md
git commit -m "Document fig loop auto-patch readiness gate"
```

## Task 4: Full Verification and Review

**Files:**

- Review: all modified files

- [ ] **Step 1: Run targeted verification**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_loop.py
```

Expected: all fig loop tests pass.

- [ ] **Step 2: Run full plugin verification**

Run:

```bash
cd plugins/figure-agent
uv run pytest
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all commands pass.

- [ ] **Step 3: Review safety boundary**

Check:

- `may_edit` is always `false`.
- No code writes to `.tex`, `spec.yaml`, `critique.md`, exports, build, accepted, or golden state.
- Multiple apply targets still produce `ambiguous_patch_selection`.
- `needs_human` still blocks before any patch handoff.
- Existing `patch_handoff`, `stop_reason`, and `escalation_level` fields remain backward compatible.

- [ ] **Step 4: Commit any review fixes**

Only if Step 3 finds defects:

```bash
git add plugins/figure-agent/scripts/fig_loop.py plugins/figure-agent/tests/test_fig_loop.py plugins/figure-agent/commands/fig_loop.md plugins/figure-agent/docs/superpowers/specs/2026-05-17-fig-loop-contract-design.md
git commit -m "Harden fig loop auto-patch readiness gate"
```

## Final Acceptance

Issue 5A is complete only when:

- `/fig_loop` emits read-only auto-patch eligibility for exactly one patch target.
- Safe visual/layout classes can be identified.
- Science/mechanism/reference/acceptance classes are blocked.
- No automatic editing is implemented.
- Tests and plugin validation pass.
- The result is documented as a readiness gate, not as auto-patch execution.

## Self-Review

Spec coverage:

- Issue 5 limited classes are covered by the candidate term list.
- No theory or mechanism edits are covered by blocked classes and tests.
- Rollback and before/after evidence are listed as required future evidence.
- The plan does not implement hidden source mutation.

Placeholder scan:

- No TBD/TODO placeholders.
- Each implementation step has exact files, code, commands, and expected outcomes.

Type consistency:

- The planned field is consistently named `auto_patch_eligibility`.
- The planned levels are consistently `auto_patch_candidate`, `patch_assisted_only`, and `human_review_required`.
- The read-only guard is consistently `may_edit: false`.
