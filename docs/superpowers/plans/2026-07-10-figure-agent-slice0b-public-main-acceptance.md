# Figure Agent Slice 0B Public Main Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the public-main publication gate fail closed when `QUALITY_AUDIT.md` contains conflicting `submission-safe` declarations, while keeping `spec.yaml.accepted` as the only machine-readable human-acceptance authority.

**Architecture:** Replace the existential boolean-field check with a private collector that preserves the existing anchored Markdown grammar and returns every recognized normalized value. The publication gate converts the collected `submission-safe` values to booleans, emits one deterministic contradiction failure for `{True, False}`, and otherwise preserves the legacy missing-field behavior. The golden-artifact gate stays a consumer of the publication gate; it must not parse `spec.yaml.accepted` again.

**Tech Stack:** Python 3, `uv`, pytest, Ruff, YAML-backed fixtures, Markdown audit files.

---

## Scope lock and branch boundary

- Implement only in a new clean `codex/` branch based on `origin/main` SHA `9d3db7347261229d6a0ce1c09b8893d49cf06e2f`.
- Treat `4f50af8f0679f9997faed01e6581b6742f577fc3` as the pinned Slice 0 SSOT context; do not merge or rebase the experiment branch into this worktree.
- Do not change either public fixture's `spec.yaml.accepted` or edit a human `QUALITY_AUDIT.md` declaration to make the gate green. The new behavior must expose, not choose between, conflicting human statements.
- Keep this slice inside `plugins/figure-agent` and its tests. Slice 0C will record the resulting commit and evidence in the SSOT branch after both isolated slices are complete.

## File structure

| Path | Responsibility |
| --- | --- |
| `plugins/figure-agent/scripts/publication_gate.py` | Parses recognized audit-field values and creates structured, fail-closed publication-gate failures. |
| `plugins/figure-agent/tests/test_publication_gate.py` | Unit-level regression coverage for contradictory `submission-safe` declarations. |
| `plugins/figure-agent/tests/test_golden_artifact_checks.py` | Integration coverage proving `--require-accepted` carries the contradiction through the public acceptance gate. |

### Task 1: Add red coverage for the contradiction path

**Files:**
- Create: none
- Modify: `plugins/figure-agent/tests/test_publication_gate.py`
- Modify: `plugins/figure-agent/tests/test_golden_artifact_checks.py`
- Test: both files above

- [ ] **Step 1: Add a unit regression test after the complete-audit test.**

  In `plugins/figure-agent/tests/test_publication_gate.py`, add:

  ```python
  def test_publication_compliance_records_reject_contradictory_submission_safe(
      tmp_path: Path,
  ) -> None:
      audit = tmp_path / "QUALITY_AUDIT.md"
      audit.write_text(
          "# Quality Audit\n\n"
          "## Provenance and Publication Compliance\n\n"
          "**submission-safe:** true\n"
          "submission-safe: false\n"
          "disclosure-needed: no\n",
          encoding="utf-8",
      )

      records = publication_compliance_failure_records(audit, require_disclosure=True)

      assert [record.code for record in records] == ["contradictory_submission_safe"]
      assert records[0].category == "publication_provenance"
      assert records[0].actor == "human"
      assert records[0].message == (
          "QUALITY_AUDIT.md declares contradictory submission-safe values"
      )
      assert records[0].required_action == (
          "Human reviewer must resolve the conflicting submission-safe declarations "
          "and retain one explicit value."
      )
  ```

- [ ] **Step 2: Add an accepted-mode integration regression.**

  In `plugins/figure-agent/tests/test_golden_artifact_checks.py`, add this test after `test_require_accepted_mode_requires_publication_compliance`:

  ```python
  def test_require_accepted_mode_rejects_contradictory_submission_safe(
      tmp_path: Path,
      monkeypatch,
  ) -> None:
      fixture = tmp_path / "conflictingSubmissionSafe"
      _make_passing_accepted_fixture(fixture, monkeypatch)
      audit = fixture / "QUALITY_AUDIT.md"
      audit.write_text(
          audit.read_text(encoding="utf-8") + "submission-safe: false\n",
          encoding="utf-8",
      )
      _mark_quality_audit_fresh(fixture)

      failures = check_example(fixture, require_accepted=True)

      assert "QUALITY_AUDIT.md declares contradictory submission-safe values" in failures
      assert "QUALITY_AUDIT.md does not declare submission-safe: true" not in failures
  ```

- [ ] **Step 3: Run the two red tests.**

  Run from `plugins/figure-agent`:

  ```bash
  uv run pytest \
    tests/test_publication_gate.py::test_publication_compliance_records_reject_contradictory_submission_safe \
    tests/test_golden_artifact_checks.py::test_require_accepted_mode_rejects_contradictory_submission_safe \
    -q
  ```

  Expected: both tests fail because the current `_has_field_value` helper finds a `true` declaration and ignores the later `false` declaration.

### Task 2: Make the Markdown parser collect and validate all recognized values

**Files:**
- Create: none
- Modify: `plugins/figure-agent/scripts/publication_gate.py`
- Test: `plugins/figure-agent/tests/test_publication_gate.py`

- [ ] **Step 1: Replace the existential matcher with an all-values collector.**

  Replace `_has_field_value` with these two helpers. The regular expression intentionally preserves the existing whole-line, optional-list-marker, and optional-bold Markdown grammar; it only changes the result from first-match truthiness to a set of every allowed normalized value.

  ```python
  def _field_values(
      audit_text: str,
      field: str,
      values: tuple[str, ...],
  ) -> set[str]:
      value_pattern = "|".join(re.escape(value) for value in values)
      pattern = (
          rf"^\s*(?:[-*]\s*)?(?:\*\*)?{re.escape(field)}(?:\*\*)?\s*:"
          rf"\s*(?:\*\*)?\s*({value_pattern})(?:\*\*)?\s*$"
      )
      return {
          match.group(1).casefold()
          for match in re.finditer(pattern, audit_text, re.IGNORECASE | re.MULTILINE)
      }


  def _has_field_value(audit_text: str, field: str, values: tuple[str, ...]) -> bool:
      return bool(_field_values(audit_text, field, values))


  def _field_boolean_values(audit_text: str, field: str) -> set[bool]:
      values = _field_values(audit_text, field, ("true", "yes", "false", "no"))
      return {value in {"true", "yes"} for value in values}
  ```

- [ ] **Step 2: Add the fail-closed `submission-safe` branch in `publication_compliance_failure_records`.**

  Replace the current `if not _has_field_value(audit_text, "submission-safe", ("true", "yes")):` block with this exact branch. Do not read `spec.yaml` here; `status.py` and `check_golden_artifacts.py` already own that authority boundary.

  ```python
  submission_safe_values = _field_boolean_values(audit_text, "submission-safe")
  if submission_safe_values == {True, False}:
      records.append(
          PublicationGateFailure(
              code="contradictory_submission_safe",
              category="publication_provenance",
              actor="human",
              message="QUALITY_AUDIT.md declares contradictory submission-safe values",
              required_action=(
                  "Human reviewer must resolve the conflicting submission-safe declarations "
                  "and retain one explicit value."
              ),
          )
      )
  elif True not in submission_safe_values:
      records.append(
          PublicationGateFailure(
              code="missing_submission_safe_true",
              category="publication_provenance",
              actor="human",
              message="QUALITY_AUDIT.md does not declare submission-safe: true",
              required_action=(
                  "Human reviewer must decide submission safety and write an explicit value."
              ),
          )
      )
  ```

  This permits repeated equivalent declarations such as two `true` lines, rejects a `true`/`false` or `yes`/`no` conflict with one structured failure, and leaves partial values such as `true-ish` on the legacy missing-value path.

- [ ] **Step 3: Run the red tests again.**

  Run:

  ```bash
  uv run pytest \
    tests/test_publication_gate.py::test_publication_compliance_records_reject_contradictory_submission_safe \
    tests/test_golden_artifact_checks.py::test_require_accepted_mode_rejects_contradictory_submission_safe \
    -q
  ```

  Expected: `2 passed`.

### Task 3: Verify compatibility, parser safety, and the actual public fixtures

**Files:**
- Create: none
- Modify: none
- Test: `plugins/figure-agent/tests/test_publication_gate.py`, `plugins/figure-agent/tests/test_golden_artifact_checks.py`

- [ ] **Step 1: Run the full targeted test set.**

  Run from `plugins/figure-agent`:

  ```bash
  uv run pytest tests/test_publication_gate.py tests/test_golden_artifact_checks.py -q
  ```

  Expected: all selected tests pass. In particular, Markdown-bold `true`, repeated true declarations in the helper fixture, disclosure parsing, and legacy missing-field messages remain covered.

- [ ] **Step 2: Run the scoped Ruff check.**

  ```bash
  uv run ruff check scripts/publication_gate.py scripts/checks/check_golden_artifacts.py \
    tests/test_publication_gate.py tests/test_golden_artifact_checks.py
  ```

  Expected: no lint findings.

- [ ] **Step 3: Inspect both accepted public fixtures without rewriting a human declaration.**

  Run each command separately:

  ```bash
  uv run python scripts/checks/check_golden_artifacts.py \
    examples/fig1_overview_v2_pair_001_vault --require-accepted
  ```

  ```bash
  uv run python scripts/checks/check_golden_artifacts.py \
    examples/fig1_overview_v4_pair_001_vault --require-accepted
  ```

  Expected: both commands read `spec.yaml.accepted: true`. The v2 fixture must now report `QUALITY_AUDIT.md declares contradictory submission-safe values` instead of silently treating its historical `true` plus `false` audit text as safe. Record other pre-existing release-gate failures separately; do not mask them or change `accepted` to make the result green.

- [ ] **Step 4: Inspect the isolated worktree boundary.**

  Run:

  ```bash
  git diff --check
  git status --short
  ```

  Expected: no whitespace errors; only the three planned files are modified.

### Task 4: Commit the public-main acceptance repair

**Files:**
- Modify: `plugins/figure-agent/scripts/publication_gate.py`
- Modify: `plugins/figure-agent/tests/test_publication_gate.py`
- Modify: `plugins/figure-agent/tests/test_golden_artifact_checks.py`

- [ ] **Step 1: Stage only the parser and regression tests.**

  ```bash
  git add plugins/figure-agent/scripts/publication_gate.py \
    plugins/figure-agent/tests/test_publication_gate.py \
    plugins/figure-agent/tests/test_golden_artifact_checks.py
  ```

- [ ] **Step 2: Commit the fail-closed behavior.**

  ```bash
  git commit -m "fix: reject contradictory publication safety audits"
  ```

- [ ] **Step 3: Capture the immutable evidence for Slice 0C.**

  Run:

  ```bash
  git rev-parse HEAD
  git status --short
  ```

  Expected: a commit SHA for the Slice 0B result and a clean isolated worktree. Slice 0C will cite this SHA, the focused test commands, and the v2 fixture's fail-closed result in `FIGURE_AGENT_SPEC.md`.
