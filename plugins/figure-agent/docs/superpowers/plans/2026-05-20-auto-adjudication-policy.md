# Auto Adjudication Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in deterministic `--policy conservative-v1` support to `critique_adjudication.py` so routine findings can be auto-dismissed, auto-deferred, or converted to at most one safe `apply` decision while core science/policy decisions remain human-gated.

**Architecture:** Keep the existing conservative scaffold as the default. Add a pure policy function inside `scripts/critique_adjudication.py` that takes validated critique frontmatter plus the generated scaffold and returns a validated adjudication mapping; wire it only when `--policy conservative-v1` is explicitly passed to `scaffold` or `sync`. `/fig_loop` and `/fig_driver` need no behavior changes because they already consume `dismiss`, `defer`, `apply`, and `needs_human`.

**Tech Stack:** Python, PyYAML, existing critique schema validator, pytest, ruff, Claude plugin validation.

---

## File Structure

- Modify `scripts/critique_adjudication.py`
  - Add the `conservative-v1` policy constants and pure policy helper.
  - Add `policy: str | None = None` to scaffold/sync functions.
  - Add `--policy {conservative-v1}` to both CLI subcommands.
- Modify `tests/test_critique_adjudication.py`
  - Add focused policy tests using existing critique writer helpers.
  - Add CLI coverage for `scaffold --force --policy conservative-v1`.
- Modify `commands/fig_adjudicate.md`
  - Document conservative default and explicit policy opt-in.
- Modify `docs/superpowers/issues/2026-05-20-issue-13-auto-adjudication-policy.md`
  - Update implementation status after code lands.

No new file is required for the first slice. Keep the policy local to
`critique_adjudication.py`; split later only if the function grows unwieldy.

---

## Task 1: Policy Function and Unit Tests

**Files:**
- Modify: `plugins/figure-agent/scripts/critique_adjudication.py`
- Test: `plugins/figure-agent/tests/test_critique_adjudication.py`

- [ ] **Step 1: Add failing tests for default-conservative and policy auto-dismiss**

Append these tests near the existing scaffold tests in
`tests/test_critique_adjudication.py`:

```python
def test_policy_default_scaffold_remains_conservative(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml() + "micro_defects: []\n",
        findings_yaml=(
            "panels:\n"
            "  - id: D\n"
            "    findings:\n"
            "      - id: P001\n"
            "        severity: MINOR\n"
            "        category: style\n"
            "        status: open\n"
            "        tex_lines: [10, 20]\n"
            "        observation: Iconic abstraction is intentional.\n"
            "        suggested_fix: accept_simplification - no edit required.\n"
            "findings: []\n"
        ),
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["decisions"][0]["decision"] == "needs_human"


def test_policy_auto_dismisses_accepted_simplification_style_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml() + "micro_defects: []\n",
        findings_yaml=(
            "panels:\n"
            "  - id: D\n"
            "    findings:\n"
            "      - id: P001\n"
            "        severity: MINOR\n"
            "        category: style\n"
            "        status: open\n"
            "        tex_lines: [10, 20]\n"
            "        observation: Iconic abstraction is intentional.\n"
            "        suggested_fix: accept_simplification - no edit required.\n"
            "findings: []\n"
        ),
    )

    scaffold = build_adjudication_scaffold(fig_dir, policy="conservative-v1")

    assert scaffold["decisions"][0]["decision"] == "dismiss"
    assert scaffold["decisions"][0]["patch_target"] == ""
    assert scaffold["decisions"][0]["reason"].startswith(
        "AUTO_DISMISS_ACCEPTED_SIMPLIFICATION:"
    )
    assert "critique.md finding P001" in scaffold["decisions"][0]["evidence"]
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_critique_adjudication.py::test_policy_default_scaffold_remains_conservative tests/test_critique_adjudication.py::test_policy_auto_dismisses_accepted_simplification_style_finding
```

Expected:

- First test passes.
- Second test fails with `TypeError: build_adjudication_scaffold() got an unexpected keyword argument 'policy'`.

- [ ] **Step 3: Implement the minimal policy function**

In `scripts/critique_adjudication.py`, change the scaffold signature and add
these helpers above `build_adjudication_scaffold`:

```python
POLICY_CONSERVATIVE_V1 = "conservative-v1"
POLICY_CHOICES = frozenset({POLICY_CONSERVATIVE_V1})

_AUTO_CATEGORIES = frozenset({"style", "palette", "whitespace", "hierarchy", "label_placement"})
_HUMAN_CATEGORIES = frozenset({"physics", "structural"})
_HUMAN_TERMS = (
    "target_journal_fit",
    "human_review",
    "human_policy",
    "publication safety",
    "mechanism",
    "topology",
    "reference interpretation",
    "accepted",
    "golden",
    "export",
    "final artifact",
    "semantic backport",
    "theory guard",
)


def _finding_text(finding: dict[str, Any]) -> str:
    return " ".join(
        str(finding.get(key, ""))
        for key in ("observation", "suggested_fix", "category", "severity")
    ).lower()


def _finding_by_id(frontmatter: dict[str, Any]) -> dict[str, dict[str, Any]]:
    findings: dict[str, dict[str, Any]] = {}
    for index, finding in enumerate(_findings_from_critique(frontmatter)):
        findings[_finding_id(finding, f"critique finding {index}")] = finding
    return findings


def _is_human_protected(finding: dict[str, Any]) -> bool:
    severity = str(finding.get("severity", "")).strip().upper()
    category = str(finding.get("category", "")).strip().lower()
    text = _finding_text(finding)
    if severity in {"BLOCKER", "MAJOR"}:
        return True
    if category in _HUMAN_CATEGORIES:
        return True
    return any(term in text for term in _HUMAN_TERMS)


def _has_two_int_tex_lines(finding: dict[str, Any]) -> bool:
    tex_lines = finding.get("tex_lines")
    return (
        isinstance(tex_lines, list)
        and len(tex_lines) == 2
        and all(isinstance(value, int) and not isinstance(value, bool) for value in tex_lines)
    )


def _policy_decision_for(
    *,
    decision: dict[str, str],
    finding: dict[str, Any],
    apply_available: bool,
    score_is_gateable: bool | None,
) -> tuple[dict[str, str], bool]:
    if decision["decision"] == "resolved" or _is_human_protected(finding):
        return decision, apply_available

    severity = str(finding.get("severity", "")).strip().upper()
    category = str(finding.get("category", "")).strip().lower()
    text = _finding_text(finding)
    finding_id = decision["finding_id"]

    if (
        severity in {"NIT", "MINOR"}
        and category in _AUTO_CATEGORIES
        and "accept_simplification" in text
    ):
        return {
            **decision,
            "decision": "dismiss",
            "reason": (
                "AUTO_DISMISS_ACCEPTED_SIMPLIFICATION: critique marks this "
                "routine style finding as an accepted schematic simplification."
            ),
            "patch_target": "",
            "evidence": f"critique.md finding {finding_id}.",
        }, apply_available

    if (
        severity in {"NIT", "MINOR"}
        and score_is_gateable is not True
        and any(term in text for term in ("thumbnail", "social-media", "non-submission-scale"))
    ):
        return {
            **decision,
            "decision": "defer",
            "reason": (
                "AUTO_DEFER_NON_GATEABLE_THUMBNAIL_POLISH: non-submission-scale "
                "polish is not gateable for this critique."
            ),
            "patch_target": "",
            "evidence": f"critique.md finding {finding_id}.",
        }, apply_available

    if (
        apply_available
        and severity == "NIT"
        and category in _AUTO_CATEGORIES
        and _has_two_int_tex_lines(finding)
        and decision.get("patch_target")
        and any(term in text for term in ("move", "offset", "spacing", "label", "whitespace"))
    ):
        return {
            **decision,
            "decision": "apply",
            "reason": (
                "AUTO_APPLY_SINGLE_SAFE_NIT_STYLE_PATCH: single local NIT style "
                "patch target selected by conservative policy."
            ),
            "evidence": f"critique.md finding {finding_id}.",
        }, False

    return decision, apply_available


def apply_adjudication_policy(
    scaffold: dict[str, Any],
    frontmatter: dict[str, Any],
    *,
    policy: str | None,
) -> dict[str, Any]:
    if policy is None:
        return scaffold
    if policy != POLICY_CONSERVATIVE_V1:
        raise CritiqueAdjudicationError(f"unknown adjudication policy: {policy}")

    findings = _finding_by_id(frontmatter)
    assessment = frontmatter.get("journal_grade_assessment")
    score_is_gateable = (
        assessment.get("score_is_gateable") if isinstance(assessment, dict) else None
    )
    apply_available = True
    decisions: list[dict[str, str]] = []
    for decision in scaffold["decisions"]:
        finding = findings.get(decision["finding_id"])
        if not isinstance(finding, dict):
            decisions.append(decision)
            continue
        updated, apply_available = _policy_decision_for(
            decision=decision,
            finding=finding,
            apply_available=apply_available,
            score_is_gateable=score_is_gateable,
        )
        decisions.append(updated)
    return validate_adjudication({**scaffold, "decisions": decisions})
```

Then change:

```python
def build_adjudication_scaffold(example_dir: Path) -> dict[str, Any]:
```

to:

```python
def build_adjudication_scaffold(example_dir: Path, *, policy: str | None = None) -> dict[str, Any]:
```

At the end, store the scaffold in a variable and return policy output:

```python
    scaffold = validate_adjudication(
        {
            "schema": SCHEMA,
            "fixture": fixture,
            "source_critique_hash": file_sha256(critique_path),
            "decisions": decisions,
        }
    )
    return apply_adjudication_policy(scaffold, frontmatter, policy=policy)
```

- [ ] **Step 4: Run the tests again**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py::test_policy_default_scaffold_remains_conservative tests/test_critique_adjudication.py::test_policy_auto_dismisses_accepted_simplification_style_finding
```

Expected: both pass.

- [ ] **Step 5: Run the narrow file checks**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py
uv run ruff check scripts/critique_adjudication.py tests/test_critique_adjudication.py
```

Expected: all tests pass and ruff reports `All checks passed!`.

---

## Task 2: Defer and Human-Protection Policy Coverage

**Files:**
- Modify: `plugins/figure-agent/tests/test_critique_adjudication.py`
- Modify: `plugins/figure-agent/scripts/critique_adjudication.py` only if tests expose a bug.

- [ ] **Step 1: Add failing tests for defer and human-protected findings**

Append:

```python
def test_policy_auto_defers_non_gateable_thumbnail_polish(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        critique_input_hash=critique_hash,
        journal_assessment_yaml=(
            _journal_assessment_yaml(assessed_hash=critique_hash, gateable="false")
            + _score_block_yaml()
        ),
        extra_frontmatter_yaml=(
            _complete_v1_3_top_tier_audit_yaml()
            + _micro_defects_yaml(linked_finding_id="C001")
            .replace("kind: wire_crosses_label", "kind: print_scale_unreadable")
            .replace("severity: MAJOR", "severity: MINOR")
        ),
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    severity: MINOR\n"
            "    category: style\n"
            "    status: open\n"
            "    tex_lines: [10, 20]\n"
            "    observation: thumbnail-only readability weak for social-media reuse\n"
            "    suggested_fix: defer until thumbnail reuse becomes a requirement\n"
        ),
    )

    scaffold = build_adjudication_scaffold(fig_dir, policy="conservative-v1")

    assert scaffold["decisions"][0]["decision"] == "defer"
    assert scaffold["decisions"][0]["reason"].startswith(
        "AUTO_DEFER_NON_GATEABLE_THUMBNAIL_POLISH:"
    )


def test_policy_preserves_target_journal_fit_as_needs_human(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml() + "micro_defects: []\n",
        findings_yaml=(
            "findings:\n"
            "  - id: C002\n"
            "    severity: MINOR\n"
            "    category: style\n"
            "    status: open\n"
            "    tex_lines: []\n"
            "    observation: top_tier_audit.target_journal_fit needs target-journal art direction\n"
            "    suggested_fix: human_review - confirm target-journal fit\n"
        ),
    )

    scaffold = build_adjudication_scaffold(fig_dir, policy="conservative-v1")

    assert scaffold["decisions"][0]["decision"] == "needs_human"
    assert scaffold["decisions"][0]["reason"] == (
        "Review C002 before selecting apply, dismiss, defer, or resolved."
    )


@pytest.mark.parametrize(
    ("severity", "category"),
    (("BLOCKER", "style"), ("MAJOR", "style"), ("MINOR", "physics"), ("MINOR", "structural")),
)
def test_policy_keeps_core_findings_human(
    tmp_path: Path,
    severity: str,
    category: str,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml() + "micro_defects: []\n",
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            f"    severity: {severity}\n"
            f"    category: {category}\n"
            "    status: open\n"
            "    tex_lines: [10, 20]\n"
            "    observation: accept_simplification is mentioned but this is protected\n"
            "    suggested_fix: accept_simplification should not bypass protection\n"
        ),
    )

    scaffold = build_adjudication_scaffold(fig_dir, policy="conservative-v1")

    assert scaffold["decisions"][0]["decision"] == "needs_human"
```

- [ ] **Step 2: Run the tests**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py::test_policy_auto_defers_non_gateable_thumbnail_polish tests/test_critique_adjudication.py::test_policy_preserves_target_journal_fit_as_needs_human tests/test_critique_adjudication.py::test_policy_keeps_core_findings_human
```

Expected: pass if Task 1 implementation is complete. If any test fails, fix
only the policy helper in `critique_adjudication.py`.

- [ ] **Step 3: Run the narrow file checks**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py
uv run ruff check scripts/critique_adjudication.py tests/test_critique_adjudication.py
```

Expected: all tests pass and ruff reports `All checks passed!`.

---

## Task 3: Single Auto-Apply Limit

**Files:**
- Modify: `plugins/figure-agent/tests/test_critique_adjudication.py`
- Modify: `plugins/figure-agent/scripts/critique_adjudication.py` only if tests expose a bug.

- [ ] **Step 1: Add failing test for max-one `apply`**

Append:

```python
def test_policy_auto_applies_at_most_one_safe_nit_style_patch(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml() + "micro_defects: []\n",
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    severity: NIT\n"
            "    category: label_placement\n"
            "    status: open\n"
            "    tex_lines: [10, 12]\n"
            "    observation: label offset is slightly crowded\n"
            "    suggested_fix: move label by 0.05 cm to improve spacing\n"
            "  - id: C002\n"
            "    severity: NIT\n"
            "    category: whitespace\n"
            "    status: open\n"
            "    tex_lines: [20, 22]\n"
            "    observation: whitespace spacing can be adjusted locally\n"
            "    suggested_fix: move spacer by 0.05 cm\n"
        ),
    )

    scaffold = build_adjudication_scaffold(fig_dir, policy="conservative-v1")

    decisions = {item["finding_id"]: item for item in scaffold["decisions"]}
    assert decisions["C001"]["decision"] == "apply"
    assert decisions["C001"]["patch_target"] == "examples/demo_fig/demo_fig.tex lines 10-12"
    assert decisions["C001"]["reason"].startswith(
        "AUTO_APPLY_SINGLE_SAFE_NIT_STYLE_PATCH:"
    )
    assert decisions["C002"]["decision"] == "defer"
    assert decisions["C002"]["reason"].startswith("AUTO_DEFER_APPLY_LIMIT_ONE_TARGET:")
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py::test_policy_auto_applies_at_most_one_safe_nit_style_patch
```

Expected before the apply-limit fix: second decision remains `needs_human`.

- [ ] **Step 3: Implement apply-limit defer**

In `_policy_decision_for`, after the `apply` branch and before the final
`return decision, apply_available`, add:

```python
    if (
        not apply_available
        and severity == "NIT"
        and category in _AUTO_CATEGORIES
        and _has_two_int_tex_lines(finding)
        and decision.get("patch_target")
        and any(term in text for term in ("move", "offset", "spacing", "label", "whitespace"))
    ):
        return {
            **decision,
            "decision": "defer",
            "reason": (
                "AUTO_DEFER_APPLY_LIMIT_ONE_TARGET: another safe NIT style "
                "finding was already selected for apply in this scaffold."
            ),
            "patch_target": "",
            "evidence": f"critique.md finding {finding_id}.",
        }, apply_available
```

- [ ] **Step 4: Run the test again**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py::test_policy_auto_applies_at_most_one_safe_nit_style_patch
```

Expected: pass.

- [ ] **Step 5: Run fig_loop compatibility checks**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py tests/test_fig_loop.py tests/test_fig_driver.py
```

Expected: pass.

---

## Task 4: CLI Wiring and Documentation

**Files:**
- Modify: `plugins/figure-agent/scripts/critique_adjudication.py`
- Modify: `plugins/figure-agent/tests/test_critique_adjudication.py`
- Modify: `plugins/figure-agent/commands/fig_adjudicate.md`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-20-issue-13-auto-adjudication-policy.md`

- [ ] **Step 1: Add failing CLI test**

Append:

```python
def test_cli_scaffold_supports_conservative_policy(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fig_dir = tmp_path / "examples" / "demo_fig"
    fig_dir.mkdir(parents=True)
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml() + "micro_defects: []\n",
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    severity: MINOR\n"
            "    category: style\n"
            "    status: open\n"
            "    tex_lines: [10, 20]\n"
            "    observation: Iconic simplification is acceptable.\n"
            "    suggested_fix: accept_simplification - no source edit required.\n"
        ),
    )

    result = main(
        [
            "scaffold",
            "demo_fig",
            "--force",
            "--policy",
            "conservative-v1",
            "--repo-root",
            str(tmp_path),
        ]
    )

    assert result == 0
    assert "wrote" in capsys.readouterr().out
    adjudication = load_adjudication(fig_dir / "critique_adjudication.yaml")
    assert adjudication["decisions"][0]["decision"] == "dismiss"
```

- [ ] **Step 2: Run the failing CLI test**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py::test_cli_scaffold_supports_conservative_policy
```

Expected: argparse fails because `--policy` is not yet defined.

- [ ] **Step 3: Wire CLI and function parameters**

In `scripts/critique_adjudication.py`:

1. Change:

```python
def scaffold_adjudication(example_dir: Path, *, force: bool = False) -> Path:
```

to:

```python
def scaffold_adjudication(
    example_dir: Path,
    *,
    force: bool = False,
    policy: str | None = None,
) -> Path:
```

2. Change the write call:

```python
    write_adjudication(path, build_adjudication_scaffold(example_dir, policy=policy))
```

3. Change `sync_adjudication` signature:

```python
def sync_adjudication(
    example_dir: Path,
    *,
    force: bool = False,
    policy: str | None = None,
    repo_root: Path = REPO_ROOT,
) -> Path:
```

4. Change scaffold creation inside sync:

```python
    scaffold = build_adjudication_scaffold(example_dir, policy=policy)
```

5. Add CLI args to both subcommands:

```python
    scaffold_parser.add_argument("--policy", choices=sorted(POLICY_CHOICES))
    sync_parser.add_argument("--policy", choices=sorted(POLICY_CHOICES))
```

6. Pass policy:

```python
path = scaffold_adjudication(example_dir, force=args.force, policy=args.policy)
path = sync_adjudication(
    example_dir,
    force=args.force,
    policy=args.policy,
    repo_root=args.repo_root,
)
```

- [ ] **Step 4: Run CLI and file tests**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py
uv run ruff check scripts/critique_adjudication.py tests/test_critique_adjudication.py
```

Expected: pass.

- [ ] **Step 5: Update `/fig_adjudicate` docs**

In `commands/fig_adjudicate.md`, after the `--force` example, add:

```markdown
To opt into deterministic policy-assisted adjudication:

```bash
uv run python3 scripts/critique_adjudication.py scaffold EXAMPLE_NAME --force --policy conservative-v1
```

`conservative-v1` can auto-dismiss accepted simplifications, auto-defer
non-gateable thumbnail polish, and select at most one safe `NIT` local style
finding as `apply`. It does not auto-resolve physics, structural,
target-journal, high-impact, accepted/golden/export, final-artifact, or
semantic-backport questions.
```

Also update the default decisions section to say the default remains
conservative unless `--policy conservative-v1` is passed.

- [ ] **Step 6: Update Issue 13 status**

In `docs/superpowers/issues/2026-05-20-issue-13-auto-adjudication-policy.md`:

- change `**Status:** proposed` to `**Status:** implemented and verified`;
- check off each acceptance criterion after tests pass.

Do not include the commit hash until after commit, or use `implemented and
verified` instead.

---

## Task 5: Dogfood and Final Verification

**Files:**
- May modify: `plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/critique_adjudication.yaml`
- Create or modify: `plugins/figure-agent/docs/milestones/2026-05-20-auto-adjudication-policy-dogfood.md`

- [ ] **Step 1: Run policy dogfood on the v1.4 fixture**

Run:

```bash
uv run python3 scripts/critique_adjudication.py scaffold fig1_overview_v2_pair_001_vault --force --policy conservative-v1
uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault --goal 'auto adjudication policy dogfood' --json
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal 'auto adjudication policy dogfood' --dry-run
```

Expected:

- `P001`, `P002`, `P003` become `dismiss`.
- `C001` becomes `defer`.
- `C002` remains `needs_human`.
- `/fig_loop` still stops at `human_gate_required`, but now for `C002`.
- `/fig_drive` returns `human_gate_stop`.

- [ ] **Step 2: If dogfood differs, inspect before changing policy**

If the expected decisions do not happen, inspect the actual `critique.md`
strings before changing code. Do not broaden the policy just to satisfy the
fixture; the safety rules in the spec are authoritative.

- [ ] **Step 3: Record dogfood evidence**

Create `docs/milestones/2026-05-20-auto-adjudication-policy-dogfood.md`:

```markdown
# Auto Adjudication Policy Dogfood

**Date:** 2026-05-20 KST
**Fixture:** `fig1_overview_v2_pair_001_vault`
**Status:** pass

## Commands

- `uv run python3 scripts/critique_adjudication.py scaffold fig1_overview_v2_pair_001_vault --force --policy conservative-v1`
- `uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault --goal 'auto adjudication policy dogfood' --json`
- `uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal 'auto adjudication policy dogfood' --dry-run`

## Result

- `P001`: dismiss
- `P002`: dismiss
- `P003`: dismiss
- `C001`: defer
- `C002`: needs_human
- `/fig_loop final_stop_reason`: human_gate_required
- `/fig_driver action`: human_gate_stop
- `/fig_driver stop_boundary`: human_gate_required

## Judgment

The policy reduced routine human adjudication while preserving the fundamental
human gate.
```

If any result differs, replace this file with the actual command output and
explain whether the difference is an implementation bug, fixture wording
mismatch, or intentional safety fallback.

- [ ] **Step 4: Run final verification**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py tests/test_fig_loop.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected:

- targeted tests pass;
- full suite passes with only known legacy warnings/skips/xfails;
- ruff passes;
- diff check is clean;
- all plugin validations pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add \
  plugins/figure-agent/scripts/critique_adjudication.py \
  plugins/figure-agent/tests/test_critique_adjudication.py \
  plugins/figure-agent/commands/fig_adjudicate.md \
  plugins/figure-agent/docs/superpowers/issues/2026-05-20-issue-13-auto-adjudication-policy.md \
  plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/critique_adjudication.yaml \
  plugins/figure-agent/docs/milestones/2026-05-20-auto-adjudication-policy-dogfood.md
git commit -m "Add conservative auto adjudication policy"
```

After commit, run:

```bash
git status --short --branch
```

Expected: clean working tree. Do not push unless the user asks or the current
handoff requires remote availability.

---

## Self-Review Checklist

- [ ] Every spec goal maps to a task.
- [ ] Default behavior remains conservative without `--policy`.
- [ ] Policy is opt-in and deterministic.
- [ ] Human-protected findings cannot be auto-dismissed, auto-deferred, or
  auto-applied.
- [ ] At most one automatic `apply` can appear in one scaffold.
- [ ] No task edits source `.tex`, exports, accepted/golden state, or
  `critique.md`.
- [ ] Final verification includes targeted tests, full tests, ruff, diff check,
  and plugin validation.
