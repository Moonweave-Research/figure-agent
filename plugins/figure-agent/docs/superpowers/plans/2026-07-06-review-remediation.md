# 2026-07-06 Review Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore trust in the verification stack (green deterministic suite + fail-closed gates), give the v0.13 self-learning loop a real gradient (reachable `improved`, stable subregion join, machine-readable human reject), stop the per-defect code-accretion pattern in `quality_search.py`, then remove confirmed dead weight.

**Architecture:** Four strictly ordered phases. Phase 0 fixes the measurement instruments (tests + gates) so every later phase can trust "green". Phase 1 fixes the three broken links that make the experience-log loop learning-inert. Phase 1.5 converts the newest bespoke Panel-F edit families into one data-driven family. Phase 2 is confirm-gated cleanup. Do not start a phase before the previous phase's exit criterion is met.

**Tech Stack:** Python 3.12 via `uv run` (a global hook blocks bare `python3`), pytest, lualatex/pdftocairo pipeline, JSONL experience log (`figure-agent.experience-record.v1`).

**Source of findings:** 2026-07-06 five-agent review (arch / code-quality / learning-loop / test / hygiene). All file:line anchors below were verified at commit `4839d325` except `scripts/quality/quality_search.py` + `tests/test_quality_search.py`, which had an uncommitted diff at review time (~+199 LOC; verdict: no functional bug — safe to land before starting this plan).

---

## Ground rules for every task

1. **Verify anchors before editing.** Line numbers below are from `4839d325` and WILL drift. Before each edit, `Read` the file and confirm the quoted snippet exists; if it moved, find it with `grep -n`. If the snippet is gone entirely, STOP and report — do not improvise a fix for code that changed.
2. **TDD.** Write the failing test first, watch it fail, make it pass, run the affected test file(s), commit. One commit per task unless a task says otherwise.
3. **Run commands from the plugin root:** `cd plugins/figure-agent` (paths in this plan are relative to it unless prefixed with `plugins/figure-agent/` for clarity).
4. **Test invocation:** `uv run pytest -q <target>`. Do NOT pass `--timeout` (pytest-timeout is not installed; Task 0.4 adds it).
5. **Fail-closed doctrine (from the 2026-07-01 wave, still binding):** a gate that cannot read its evidence must BLOCK, never pass. Missing file, unreadable file, wrong schema, unrecognized enum value — all block.
6. **Branch:** create `work/review-remediation-2026-07-06` off the current branch head (`fig1-v3-on-origin-main-20260703` line) and do all work there.
7. **Known-red baseline:** the suite currently has 3 deterministic failures + a flaky cluster (fixed in Phase 0). Until Phase 0 exit, "suite green" claims are limited to the targeted files you ran.

---

# Phase 0 — Trust restoration

**Exit criterion:** `uv run pytest -q` passes 3 consecutive full runs with 0 failures (skips/xfails allowed), and the 7 fail-open gates below block on missing/corrupt/old-schema evidence.

### Task 0.1: Stop tests from writing into the live experience log

The suite pollutes the real learning substrate: `scripts/experience_log.py:862` `_experience_log_path(name, plugin_root)` resolves to `<plugin_root>/docs/experience-log/<name>.jsonl`, and `tests/conftest.py:6` + `tests/test_mcp_facade.py:13` set `PLUGIN_ROOT` to the real repo directory. Full-CLI tests appended real rows (confirmed: stray untracked `docs/experience-log/candidate_demo.jsonl`), and `test_fig_agent_rank_applies_fixture_index_prior_by_default` reads prior data from the same directory → order-dependent flakiness AND fake training data.

**Files:**
- Modify: `scripts/experience_log.py` (`_experience_log_path`, ~:862)
- Modify: `scripts/candidates/candidate_generator.py` and `scripts/quality/quality_memory_index.py` (each has its own copy of the log-path/loader logic — route both through the one helper)
- Modify: `tests/conftest.py`
- Test: `tests/test_experience_log.py` (add to existing file; create if absent)
- Delete: `docs/experience-log/candidate_demo.jsonl` (untracked stray)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_experience_log.py
import os
from pathlib import Path

from scripts.experience_log import _experience_log_path


def test_experience_log_path_defaults_to_plugin_docs(tmp_path, monkeypatch):
    monkeypatch.delenv("FIG_AGENT_EXPERIENCE_LOG_DIR", raising=False)
    plugin_root = tmp_path / "plugin"
    path = _experience_log_path("demo", plugin_root)
    assert path == plugin_root / "docs" / "experience-log" / "demo.jsonl"


def test_experience_log_path_honors_env_override(tmp_path, monkeypatch):
    override = tmp_path / "isolated-log"
    monkeypatch.setenv("FIG_AGENT_EXPERIENCE_LOG_DIR", str(override))
    path = _experience_log_path("demo", tmp_path / "plugin")
    assert path == override / "demo.jsonl"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest -q tests/test_experience_log.py -k "log_path"`
Expected: FAIL (`_experience_log_path` ignores the env var; second test fails).

- [ ] **Step 3: Implement the override in `_experience_log_path`**

Read `scripts/experience_log.py` around :862 first. Preserve the existing signature; add the env branch:

```python
def _experience_log_path(name: str, plugin_root: Path) -> Path:
    override = os.environ.get("FIG_AGENT_EXPERIENCE_LOG_DIR")
    base = Path(override) if override else plugin_root / "docs" / "experience-log"
    return base / f"{name}.jsonl"
```

(Add `import os` in the same edit if missing — note the ruff hook strips an import added before any usage exists, so add import and usage together.)

- [ ] **Step 4: Route the duplicate resolvers through the helper**

Grep both files: `grep -n "experience-log" scripts/candidates/candidate_generator.py scripts/quality/quality_memory_index.py`. Each resolves the directory independently (loader copies at `candidate_generator.py:55`, `quality_memory_index.py:84`). Replace their directory resolution with an import of `_experience_log_path` (or a new public `experience_log_dir(plugin_root)` in `experience_log.py` if the private import is awkward). Do NOT dedupe the full loader bodies here — that is Task 2.5; only the path resolution must go through one env-aware place.

- [ ] **Step 5: Isolate every test by default**

Append to `tests/conftest.py`:

```python
@pytest.fixture(autouse=True)
def _isolate_experience_log(tmp_path, monkeypatch):
    monkeypatch.setenv("FIG_AGENT_EXPERIENCE_LOG_DIR", str(tmp_path / "experience-log"))
```

`monkeypatch.setenv` mutates `os.environ`, so subprocess CLI invocations inside tests inherit it. If a specific test intentionally exercises the default path, it can `monkeypatch.delenv` locally against a tmp plugin_root.

- [ ] **Step 6: Verify isolation end-to-end**

Run: `git status --porcelain docs/experience-log/ && uv run pytest -q tests/test_experience_log.py tests/test_mcp_facade.py tests/test_candidate_generator.py && git status --porcelain docs/experience-log/`
Expected: the two `git status` outputs are identical (no new/modified jsonl), tests pass or fail exactly as before isolation (flakiness is Task 0.2's job — here only assert NO live-log writes).

- [ ] **Step 7: Remove the stray file and audit for past pollution**

`rm docs/experience-log/candidate_demo.jsonl` (untracked). Then check whether tracked logs contain test-shaped rows: `grep -l "candidate_demo\|tmp_path\|pytest" docs/experience-log/*.jsonl || true`. If any tracked log matches, report the rows to the user — do NOT rewrite tracked dogfood logs without confirmation.

- [ ] **Step 8: Commit**

```bash
git add scripts/experience_log.py scripts/candidates/candidate_generator.py scripts/quality/quality_memory_index.py tests/conftest.py tests/test_experience_log.py
git commit -m "Isolate experience-log writes from tests via env override"
```

### Task 0.2: Bisect and fail-close the candidate-manifest flake

Flaky cluster: `tests/test_candidate_cli_contract.py`, `tests/test_candidate_generator.py`, `tests/test_mcp_facade.py` — each passes alone, fails unpredictably in combination. Reproduced mechanism: `fig-agent render-candidates --compile --export --evaluate` intermittently **reports exit 0 without writing `candidate_manifest.json`** (`tests/test_mcp_facade.py:1759` `_build_apply_ready_candidate` then hits FileNotFoundError). The same CLI sequence outside pytest succeeds. This is a live fail-open in the production CLI, not just test pollution.

**Files:**
- Investigate: `scripts/candidates/candidate_render.py` (manifest write path, ~:625/:708), `bin/fig-agent` (render-candidates dispatch)
- Modify: `scripts/candidates/candidate_render.py`
- Test: `tests/test_candidate_render.py`

- [ ] **Step 1: Re-measure after Task 0.1**

Task 0.1 removed one flake source (fixture-index-prior reading the live log). Run each file alone 5×:

```bash
for i in 1 2 3 4 5; do uv run pytest -q tests/test_candidate_generator.py; done
for i in 1 2 3 4 5; do uv run pytest -q tests/test_candidate_cli_contract.py; done
for i in 1 2 3 4 5; do uv run pytest -q tests/test_mcp_facade.py; done
```

Record pass/fail per run. If all 15 runs pass, run the three files together 5×. Only proceed to bisection for combinations that still fail.

- [ ] **Step 2: Root-cause with the systematic-debugging skill**

Use superpowers:systematic-debugging. Hypotheses to check first (in order): (a) shared sandbox/tmp directory reused across tests within one process, (b) an exception swallowed inside the render loop after which the CLI still returns 0, (c) cwd-dependent path resolution (`candidate_render.py` assumed-CWD paths). Capture the failing run with `-x --tb=long` and inspect whether the render subprocess stderr shows a swallowed error. Do not patch symptoms (e.g., retry in the test) — find why exit 0 coexists with a missing manifest.

- [ ] **Step 3: Write the fail-closed contract test**

Regardless of the root cause found, this contract must hold:

```python
# tests/test_candidate_render.py
def test_render_candidate_set_missing_manifest_is_an_error(tmp_path, monkeypatch):
    """render must never report success without a manifest on disk."""
    # Arrange a render whose manifest write is forced to fail:
    import scripts.candidates.candidate_render as cr
    monkeypatch.setattr(cr, "_write_manifest", lambda *a, **k: None)  # adjust to the real writer name after reading the file
    result = cr.render_candidate_set(...)  # build minimal valid args from existing tests in this file
    assert result.returncode != 0 or result.status == "failed"
```

Adapt the writer name and call signature to reality after reading the file — the assertion (success ⇒ manifest exists) is the fixed requirement, the plumbing is not.

- [ ] **Step 4: Implement the guard + the root-cause fix**

At the end of the render entrypoint, before reporting success: if `candidate_manifest.json` does not exist at the advertised path, exit nonzero with a one-line error naming the path. Plus the specific root-cause fix from Step 2.

- [ ] **Step 5: Verify**

Run the Step 1 matrix again (15 solo runs + 5 combined). Expected: 0 failures. Then `uv run pytest -q tests/test_candidate_render.py`.

- [ ] **Step 6: Commit**

```bash
git add scripts/candidates/candidate_render.py tests/test_candidate_render.py
git commit -m "Fail-close render-candidates on missing manifest; fix <root cause>"
```

### Task 0.3: Fix the three deterministic pre-existing failures

**Files:**
- Modify: whichever side is stale per failure (doc vs contract), see below
- Tests already exist and are the failing ones

- [ ] **Step 1: `tests/test_release_contract.py:501` (inventory header)** — the referenced doc no longer contains the "Current inventory is N scripts, M tests..." sentence at all. Read the test to find which doc it parses, decide: if the doc restructure was intentional, update the test's parsing/expectation to the doc's current structure; if the sentence was lost accidentally, restore it with current counts (compute them the same way the test does). Do not weaken the test to a vacuous pass.
- [ ] **Step 2: `tests/test_release_contract.py:849` (schema-module map)** — 11 schema constants missing from `docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md` (first: `figure-agent.figure-spec.v1` in `scripts/convergence_models.py`). Run the test, take its own diff output, add the missing rows to the doc.
- [ ] **Step 3: `tests/test_real_fixture_audit_adoption.py:63`** — new real fixtures (v5c/v5d/... incl. `fig1_overview_v5f_v013_dogfood_001_vault`) exist under `examples/` but are unregistered in the audit-adoption contract. Read the test to find the registry file, register the new fixtures with honest adoption status (do not mark unaudited fixtures as audited).
- [ ] **Step 4: Verify + commit**

Run: `uv run pytest -q tests/test_release_contract.py tests/test_real_fixture_audit_adoption.py`
Expected: PASS.

```bash
git add -A docs/superpowers/issues/ tests/ scripts/ examples/
git commit -m "Fix release-contract doc drift and register new real fixtures"
```

### Task 0.4: Add pytest-timeout as a dev dependency

- [ ] **Step 1:** `uv add --dev pytest-timeout` (from `plugins/figure-agent/`).
- [ ] **Step 2:** Verify: `uv run pytest -q tests/test_experience_log.py --timeout=120` runs without usage error.
- [ ] **Step 3:** Commit `pyproject.toml` + lockfile: `git commit -m "Add pytest-timeout dev dependency"`.

### Task 0.5: Fail-close the physics-assertions export gate (worst surviving fail-open)

`scripts/checks/check_tex_assertions.py:283-296` `read_blocking_issues()`:

```python
except (OSError, json.JSONDecodeError, UnicodeDecodeError):
    return []
...
if not isinstance(issues, list):
    return []
```

This is THE export gate for physics correctness (reversed-arrow / violated-direction). Missing / `git clean`-deleted / truncated / old-schema `build/tex_assertions.json` → `[]` = "no blocking issues" → a physics violation ships. This is the M1 blind spot from the 2026-07-01 audit, still live.

**Files:**
- Modify: `scripts/checks/check_tex_assertions.py:283-296`
- Test: `tests/test_check_tex_assertions.py` (add to existing test file for this checker; `grep -rn "read_blocking_issues" tests/` to find it)

- [ ] **Step 1: Write the failing tests**

```python
def test_read_blocking_issues_missing_artifact_blocks(tmp_path):
    issues = read_blocking_issues(tmp_path / "tex_assertions.json")
    assert issues, "missing evidence must block export, not pass it"


def test_read_blocking_issues_corrupt_artifact_blocks(tmp_path):
    p = tmp_path / "tex_assertions.json"
    p.write_text("{truncated", encoding="utf-8")
    assert read_blocking_issues(p)


def test_read_blocking_issues_old_schema_blocks(tmp_path):
    p = tmp_path / "tex_assertions.json"
    p.write_text('{"no_issues_key": true}', encoding="utf-8")
    assert read_blocking_issues(p)
```

- [ ] **Step 2: Run to verify all three fail** (`uv run pytest -q <test file> -k read_blocking_issues`).

- [ ] **Step 3: Implement.** First read the function AND its export-gate caller to learn the issue-record shape the caller treats as blocking. Then replace the three silent `return []` paths with synthesized blocking issues in that same shape, e.g. (adapt keys to the real shape):

```python
except FileNotFoundError:
    return [_gate_failure_issue("artifact_missing", path)]
except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
    return [_gate_failure_issue("artifact_unreadable", path, detail=str(exc))]
...
if not isinstance(issues, list):
    return [_gate_failure_issue("artifact_schema_invalid", path)]
```

- [ ] **Step 4: Verify the caller actually blocks** — find the export path that consumes `read_blocking_issues` (`grep -rn "read_blocking_issues" scripts/ bin/`) and run its existing tests. If the caller filters issues by `kind`, ensure the synthesized kinds pass the filter (extend the caller's test with a missing-artifact case).
- [ ] **Step 5: Commit** — `git commit -m "Fail-close tex-assertions export gate on missing or unreadable evidence"`.

### Task 0.6: Fail-close the remaining six gates

Same doctrine, same TDD shape as Task 0.5 (failing test per mode: missing / corrupt / wrong-schema → must block). One commit per gate. For each: read the function and its caller first; synthesize a blocking result in the caller's native shape; extend the caller's test.

- [ ] **0.6a `scripts/critique_evidence_lint.py:40-45`** — `if frontmatter.get("schema") not in SCHEMAS_WITH_PRINT_SCALE_EVIDENCE: return []` with hardcoded `{v1.10, v1.14, v1.17}`. An absent/older/newer schema string bypasses the print-scale-evidence lint entirely. Fix direction: unknown or missing schema on a critique that declares `journal_polish`/`publication_readiness` verdicts ⇒ emit a violation ("schema not lintable"), don't return clean. Known-old schemas that legitimately predate print-scale evidence may stay exempt — keep the exempt list explicit and closed.
- [ ] **0.6b `scripts/composition_post_apply_verify.py:84-111`** — missing `visual_clash.json` → `total=None`; `isinstance(None, int)` is False → not blocked → receipt `"rendered_exported"`. Fix: `_detector_summary` status `"missing"` must map to a blocking `_receipt_status` (e.g. `blocked_missing_detector_report`), never to exported.
- [ ] **0.6c `scripts/checks/check_golden_artifacts.py:611-687`** — `require_accepted = spec_declares_accepted_key(spec)`: a spec that simply omits the `accepted` key skips ALL provenance gates (attestation, PDF labels, audit freshness, publication compliance, theory guard, reference pack, budget) and reports "OK". Fix: for fixtures under the golden/real-fixture class the gate covers, a spec without the `accepted` key is itself a failure ("spec missing accepted declaration"), not permissive mode. Check callers for a legitimate non-golden use first; if one exists, make the permissive mode an explicit opt-in flag, never the missing-key default.
- [ ] **0.6d `scripts/semantic_assertions.py:176-201`** — missing/non-dict `spec.yaml` → `{}` → no assertions → exit 0 "OK". Fix: missing/unreadable spec ⇒ exit nonzero with "spec unreadable"; a readable spec that declares zero assertions stays a pass (that is a legitimate state), but `anchor_missing` should fail without requiring `--strict` — check with the user if `--strict` semantics are load-bearing anywhere before flipping the default.
- [ ] **0.6e `scripts/checks/check_physics_grounding.py:58-66`** — missing `briefing.md` → `""` → classified `"undeclared"` (benign). Fix: missing briefing ⇒ its own non-benign status (e.g. `"briefing_missing"`, WARN at minimum) so the meta-check surfaces the gap instead of scoring absence as "nothing to enforce".
- [ ] **0.6f `scripts/closeout_readiness.py:208-256`** — `_release_check`: absent `publication_gate_failures` → treated as `[]` → "passed" without consulting `release_ready`; `_final_artifact_check`: any state not in `{MISSING, INVALID, STALE, BLOCKED}` passes (unrecognized strings pass). Fix: absent gate data ⇒ blocked ("publication gate not evaluated"); unrecognized artifact state ⇒ blocked ("unknown state").
- [ ] **0.6g (LOW, fold into 0.6c's commit)** `check_golden_artifacts.py:519` — `if len(cells) < 5: continue` silently skips a malformed theory-guard BLOCKER row; make a malformed row a failure.

### Task 0.7: Phase 0 exit check

- [ ] Run `uv run pytest -q` three times in a row. Expected: 0 failed × 3, and `git status --porcelain docs/experience-log/` unchanged by the runs. If any failure appears, it is NEW information — diagnose before proceeding (do not average it away).
- [ ] Commit any straggler fixes; push the branch.

---

# Phase 1 — Learning gradient (makes v0.13 able to learn)

**Why:** across 145 real dogfood rows: `quality_movement="improved"` 0×, `human_label="reject"` 0×, `detector_recheck={}` 100%, `subregion_key="unstable:<name>"` 145/145. The read path (suppression at `candidate_generator.py:51/:500-510`, ε-greedy bandit at `quality_search.py:2446-2499` feeding `_candidate_policy_score` :9246/:9333) is real but its inputs carry no gradient: `empirical_reward = (improved + 0.5*neutral)/attempts` (`quality_search.py:2454`) is capped at 0.5 forever.

**Exit criterion:** a scripted end-to-end run on a real fixture produces at least one row with `quality_movement="improved"`, at least one row with `human_label="reject"`, and zero rows with an `unstable:` subregion key.

### Task 1.1: Capture human reject machine-readably

`experience_log.py:831` maps only `acceptance.json.decision == "accept"` into `human_label`; `_suppression_reason` (`candidate_generator.py:93-100`) is already coded to consume a reject verdict that the write path never produces. The richest training signal is currently discarded.

**Files:**
- Investigate first: where acceptance.json is written (`grep -rn "acceptance.json" scripts/ bin/ mcp/`) and what the human-review flow (`prepare_human_review` / `accept_candidate` MCP tools) writes on a "no".
- Modify: `scripts/experience_log.py` (~:831) + the writer side so a human "no" lands as `decision: "reject"` with an optional `reason`.
- Test: `tests/test_experience_log.py`

- [ ] **Step 1: Failing test**

```python
def test_reject_decision_flows_to_human_label(tmp_path):
    # build the same record fixture the existing accept-path test uses,
    # with acceptance decision "reject"
    record = _build_record_with_acceptance(tmp_path, decision="reject")
    assert record["outcome"]["human_label"] == "reject"
```

(Mirror the construction used by the existing accept-path test in this file — read it first; reuse its helper rather than inventing a parallel fixture.)

- [ ] **Step 2:** Run, verify FAIL. **Step 3:** Implement the mapping (`decision == "reject"` → `human_label="reject"`, thread `human_decision_kind` if present). **Step 4:** Extend the writer side: whichever tool records the human verdict must be able to write `decision: "reject"` (if the current flow simply *doesn't write anything* on reject, add the write). **Step 5:** Confirm the suppression consumer picks it up: run the existing `candidate_generator` suppression tests; add one asserting a rejected (family, subregion) is suppressed. **Step 6:** Commit — `"Capture human reject as machine-readable experience signal"`.

### Task 1.2: Fix the subregion join key (`unstable:` fallback on 145/145 rows)

`experience_log.py:172` `_target` does `selector_text_hash or f"unstable:{subregion}"`; `_selector_text_hash` (:155) returned None on every real row, so per-arm memory and suppression key on coarse names and can never anchor to a durable geometric target.

**Files:**
- Investigate: `scripts/experience_log.py:155-190`; trace where the selector text is *supposed* to come from (the finding → action payload; `grep -rn "selector_text" scripts/`).
- Modify: the producer that builds the action/state payload (likely in `scripts/quality/quality_search.py` where operations are assembled) so selector text is populated; and/or `_selector_text_hash` if it reads the wrong key.
- Test: `tests/test_experience_log.py`

- [ ] **Step 1: Diagnose, don't assume.** Read `_selector_text_hash` and print what fields the real v5f rows carry for the target (`uv run python - <<'EOF'` over one row of `docs/experience-log/fig1_overview_v5f_art_direction_001_vault.jsonl`). Determine: is the selector text absent from the payload, or present under a different key?
- [ ] **Step 2: Failing test** — build a record through the public append path with a realistic operation (use an existing fixture from the current tests) and assert:

```python
def test_subregion_key_is_stable_for_anchored_operation(...):
    record = _append_realistic_apply_record(...)
    assert not record["state"]["target"]["subregion_key"].startswith("unstable:")
```

- [ ] **Step 3:** Implement the population at the producer. The hash input must be deterministic across sessions (selector text = the matched tex block or a normalized anchor, NOT a timestamp or tmp path). **Step 4:** Backfill question — do NOT rewrite historical rows; old `unstable:` rows just age out. **Step 5:** Run `tests/test_experience_log.py` + `tests/test_candidate_generator.py` (suppression keys change shape — fix any test that pinned `unstable:`). **Step 6:** Commit — `"Populate selector hash so subregion join key is stable"`.

### Task 1.3: Make `improved` reachable via a real detector recheck

`_quality_movement` (`experience_log.py:215-222`) returns `"improved"` only when `outcome.detector_recheck.status == "success"`, and `detector_recheck` is `{}` on 100% of real rows: nothing re-runs the detectors after apply. Semantics to implement: **improved = the finding that motivated the candidate is no longer detected on the recompiled artifact (and no new blocking finding appeared)**.

**Files:**
- Investigate: the apply/verify path that already recompiles and runs `labels_unchanged`/`palette_locked` (`grep -rn "detector_recheck" scripts/` to find every producer/consumer; find the post-apply hook in `scripts/quality/quality_search.py` or `scripts/candidates/`).
- Modify: post-apply verification to re-run the *originating* detector (the 4 allowlisted ones: `check_collisions`, `check_golden_artifacts`, `check_text_boundary_clash`, `check_visual_clash`) scoped to the applied finding, and write `detector_recheck = {"status": "success"|"still_present"|"error", "finding_id": ..., "detector": ...}`.
- Test: `tests/test_experience_log.py` + the apply-path test file (find via `grep -rn "apply_status" tests/ | head`).

- [ ] **Step 1: Failing unit test** for the mapping (cheap, no LaTeX):

```python
def test_quality_movement_improved_when_recheck_succeeds(...):
    record = _build_record(detector_recheck={"status": "success", "detector": "check_collisions", "finding_id": "C001"}, ...)
    assert record["outcome"]["quality_movement"] == "improved"
```

(This may already pass if the mapping is correct and only the producer is missing — if so, keep the test and move on; the producer test below is the real work.)

- [ ] **Step 2: Failing integration test** — in the apply-path test file, drive an apply whose finding is resolvable by the edit (reuse the existing apply fixtures; the fig2 C001-style bounded fix from Slice 5 is the canonical case) and assert the appended record has non-empty `detector_recheck`.
- [ ] **Step 3: Implement the recheck producer.** Re-run only the originating detector on the recompiled PDF (not the full suite — keep per-iteration cost bounded); classify: original finding id absent → `success`; still present → `still_present`; detector crashed → `error` (and `quality_movement` must NOT be `improved` on `error` — fail-closed doctrine applies to rewards too).
- [ ] **Step 4:** Run the integration test + `tests/test_experience_log.py`. **Step 5:** Verify the reward moves: `uv run python -` a snippet calling `_arm_statistics` (`quality_search.py:2446`) over a synthetic log containing one improved row and assert `empirical_reward > 0.5` is now possible. **Step 6:** Commit — `"Populate detector_recheck post-apply; improved outcome reachable"`.

### Task 1.4: Phase 1 exit check (scripted E2E on a real fixture)

- [ ] On a copy of a real fixture (e.g. `examples/fig2_*`), run one full loop iteration via the CLI (`bin/fig-agent` quality-search → render → apply with a finding the bounded family can fix), then a scripted reject: confirm the log gains ≥1 `improved` row, ≥1 `reject` row, 0 `unstable:` keys. Paste the three rows into the task report.
- [ ] Push. This is the point to tell the user the learning substrate is live.

---

# Phase 1.5 — Stop the quality_search accretion pattern

**Why:** `scripts/quality/quality_search.py` is 10,751 LOC holding 32 `_panel_f_*_replacement` functions, 36 `_template_applied` guards, and 602 hardcoded coordinate literals — one bespoke code family per human-observed defect, each used exactly once (~28 one-shot families in the v5f log), ~150-225 LOC + a mirror test per iteration. The marginal cost of an iteration is going up, and none of it generalizes to another figure.

**Exit criterion:** the next real element-iteration on fig1 Panel F is expressible as a data entry (no new Python function), proven by porting the 6 newest families.

### Task 1.5.1: Extract the parametric `replace_block` family

**Files:**
- Create: `scripts/quality/panel_block_edits.py` (loader + validator, target <150 LOC)
- Create: `examples/fig1_overview_v5f_art_direction_001_vault/panel_block_edits.yaml` (per-fixture data; confirm the fixture dir naming against reality before creating)
- Modify: `scripts/quality/quality_search.py` (one generic family replaces the 6 newest `_panel_f_post_*` families)
- Test: `tests/test_panel_block_edits.py` + edits to `tests/test_quality_search.py`

- [ ] **Step 1: Diff the 6 newest families to lock the data schema.** `grep -n "_panel_f_post_" scripts/quality/quality_search.py` — read the 6 most recent (registry entry + `_template_applied` guard + `_replacement` fn + dispatch edits + `_goal_hypotheses` branch each). Confirm the varying surface is exactly: `{family_id, panel, match_block (old tex), replacement_block (new tex), protected_labels, goal_keywords}`. If a 7th varying dimension exists, add it to the schema — do not force-fit.
- [ ] **Step 2: Failing loader test:**

```python
def test_panel_block_edit_entries_validate_and_round_trip(tmp_path):
    yaml_text = """
    - family_id: post_gap_label_relief
      panel: F
      match_block: |
        <exact old tex copied from the current _replacement fn>
      replacement_block: |
        <exact new tex>
      protected_labels: [S60, tau_d]
      goal_keywords: [gap, label, relief]
    """
    entries = load_panel_block_edits(io.StringIO(yaml_text))
    assert entries[0].family_id == "post_gap_label_relief"
    assert "S60" in entries[0].protected_labels
```

- [ ] **Step 3:** Implement loader + validation (duplicate family_id = error; empty match_block = error; match_block == replacement_block = error).
- [ ] **Step 4: Port family #1 (the newest).** Move its old/new tex blocks into the YAML; route the generic family through the same registry/dispatch/goal-hypothesis hooks the bespoke one used; delete the bespoke function + its mirror test; the existing behavior tests for that family must pass against the data-driven path (port the test to assert via the public planning API, not the deleted private fn).
- [ ] **Step 5: Port families #2-#6** one commit each, same mechanics. After #6: `grep -c "_panel_f_post_" scripts/quality/quality_search.py` should drop by 6.
- [ ] **Step 6: Write the stop-rule down.** Add to `docs/superpowers/specs/` a 10-line note: new element-iterations on an existing panel = YAML entry; a new Python family requires a new *edit mechanic* (not new coordinates). Reference it from the plan-of-record doc the loop workflow reads (grep `docs/` for what `/fig_*` commands load).
- [ ] **Step 7:** Full targeted run: `uv run pytest -q tests/test_quality_search.py tests/test_panel_block_edits.py`. Commit.

---

# Phase 2 — Cleanup (CONFIRM-GATED: every deletion below needs explicit user confirmation first; present the list, wait)

### Task 2.1: Delete the 32MB duplicate fixture (after rescuing 3 files)

`examples/fig1_overview_v3_pair_001_vault/` (67 files, 32.05 MB) is a near-byte duplicate of `fig1_overview_v2_pair_001_vault/` — all ~90 reference PNGs byte-identical; only `REFERENCE_GAP.md`, `audit_table.md`, `reference_pack.md` differ. v2 has 23 active references; **v3 has zero references** in commands/skills/scripts/tests.

- [ ] **Step 1:** Re-verify zero references at HEAD: `grep -rn "fig1_overview_v3_pair_001_vault" --include="*.py" --include="*.md" --include="*.json" --include="*.yaml" . | grep -v examples/fig1_overview_v3_pair_001_vault` → expect empty.
- [ ] **Step 2:** Diff the 3 diverging files vs v2; if the v3 versions carry unique content, copy them to `docs/historical/fig1_v3_pair_001_divergence/` with a one-line provenance note.
- [ ] **Step 3 (after user confirm):** `git rm -r examples/fig1_overview_v3_pair_001_vault` — note the guard_destructive hook blocks `rm -rf`; use `git rm` per-path. Commit: `"Remove unreferenced 32MB duplicate of v2 pair fixture (diverging docs preserved)"`.
- [ ] **Step 4:** Run `uv run pytest -q tests/test_real_fixture_audit_adoption.py tests/test_fig_queue.py` (fixture-scanning tests) — expect green.

### Task 2.2: Archive unreferenced docs — with one correction to the hygiene report

The hygiene scan found `docs/superpowers/` (427 files) unreferenced by commands/skills/scripts — **but Task 0.3 proved `tests/test_release_contract.py:849` reads `docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md`, and this very plan lives in `docs/superpowers/plans/`.** So: re-verify per subdirectory INCLUDING tests before touching anything.

- [ ] **Step 1:** For each candidate (`docs/superpowers/issues/`, `docs/superpowers/specs/` older items, `docs/milestones-archive/`, `docs/wave8/`, `docs/style-lock-rules/`, `docs/reviews/`, `docs/macros/`): `grep -rn "<subdir name>" tests/ scripts/ commands/ skills/ bin/ mcp/` and list hits.
- [ ] **Step 2:** Present the user a table: subdir, files, bytes, hits found, proposed action (keep / move to `docs/historical/`). Plans + issues referenced by tests stay put.
- [ ] **Step 3 (after confirm):** `git mv` approved subdirs under `docs/historical/`; one commit; run `uv run pytest -q tests/test_release_contract.py` to prove nothing referenced broke.

### Task 2.3: Merged-branch cleanup

16 local branches are fully merged into main (list from hygiene review: `design/figure-agent-v2-svg`, `experiment/svg-first-figure-agent`, `feature/figure-agent-diagnostic-improvements`, `feature/panel-c-15iter-aesthetic-loop`, `feature/panel-e-aesthetic-loop`, `feature/v8.5-aesthetic-upgrade`, `goal1/fig1-overnight-2026-06-04`, `tool-only-p5-20260703`, `work/fig1-layout-drift-dogfood`, `work/fig1-layout-drift-rebaseline`, `work/fig1-layout-drift-triage`, `work/fig1-required-labels-specialize`, `work/fig3-mechanism-schematic`, `work/layout-drift-token-normalization`, `work/sulfur-paper-caption-plan`).

- [ ] **Step 1:** Re-verify: `git branch --merged main`. **Step 2 (after confirm):** `git branch -d <each>` (`-d` not `-D` — it refuses if actually unmerged). Do NOT touch unmerged `codex/*` / `experiment/python-svg-*` branches — those need user judgment individually.

### Task 2.4: Rename the misleading `_legacy_server.py`

`mcp/_legacy_server.py` (2404 LOC) is the LIVE implementation of all 29 MCP tools; `mcp/figure_agent_server.py` is a 30-line re-export shim doing a blind `globals().update` over it.

- [ ] **Step 1:** `grep -rn "_legacy_server" . --include="*.py" --include="*.md" --include="*.json"` — enumerate every reference (imports, .mcp.json, docs, tests).
- [ ] **Step 2:** `git mv mcp/_legacy_server.py mcp/server_impl.py`; update every reference from Step 1 (no blind find-and-replace — edit each hit).
- [ ] **Step 3:** Verify the MCP server still boots: run the doctor/health tool the repo provides (`bin/fig-agent doctor` or the `figure_agent_doctor` invocation used in tests — find via `grep -rn "doctor" tests/ | head`). Run `uv run pytest -q tests/test_mcp_facade.py`. Commit.

### Task 2.5: Performance quick wins (one commit each)

- [ ] **2.5a Hash-gated compile skip.** `candidate_render.py:386-467` computes `candidate_hash` and threads it into manifests (:625/:708) but never compares it to skip work — every candidate unconditionally runs lualatex + pdftocairo PNG@600dpi (:440) + SVG (:453). Implement: before compiling, look up the previous manifest for this candidate set; if a prior entry has the same `candidate_hash` AND its artifacts exist on disk, reuse them and mark the manifest row `"cache": "hit"`. Failing test first: render the same candidate twice, assert the second run performs zero compile subprocess calls (monkeypatch-count the subprocess runner) and produces an identical manifest modulo the cache field.
- [ ] **2.5b Hoist per-candidate invariants.** `candidate_render.py:726` forks `git rev-parse HEAD` per candidate; `_candidate_source_text` (:243) + `_operations_with_source_hashes` (:308) re-read/re-SHA256 the same unchanged source per candidate. Hoist all three to once per batch. Existing tests must stay green.
- [ ] **2.5c Dedupe the experience-log loader.** `_load_experience_records` exists byte-identical at `experience_log.py:56`, `candidate_generator.py:55`, `quality_memory_index.py:84` (+2 variants at `quality_loop_metrics.py:34`, `attempt_store.py:69`). Keep the `experience_log.py` copy as the single source, import it from the others, delete the copies. (Path resolution was already unified in Task 0.1.) Note: `attempt_store.py` is flagged unreachable-from-entrypoints by the arch review — if `grep -rn "attempt_store" scripts/ bin/ mcp/ tests/` confirms nothing imports it, report it as a deletion candidate to the user instead of deduping it.
- [ ] **2.5d PDF-crop util dedupe.** `candidate_render.py:149/:161` (`_pdf_page_size_cm` + `_crop_panel_png`) near-verbatim duplicates `critique_brief.py:366/:382`. Extract to `scripts/pdf_geometry.py`, import from both, port the exception-class difference explicitly.

### Deferred decisions (report to user; NOT tasks in this plan)

- **Retire the old loop engine** (`fig_loop.py` + `scripts/loop/`, 19 modules / 2908 LOC, disjoint from the live quality/candidates path) — folding the stop-diagnoser/basin into the live path is a design decision worth its own brainstorm+plan.
- **9 entrypoint-unreachable modules** (incl. `check_physics_grounding.py`, `check_layout_drift.py`, `attempt_store.py`, `detector_log.py`, ...) — wiring vs deleting is per-module judgment; `check_physics_grounding` in particular was built for the fig5 physics system and probably should be WIRED (Phase 1.3 territory), not deleted.
- **`quality_search.py` full decomposition** beyond the Phase 1.5 extraction (10.7k → target <3k LOC) — only worth doing after Phase 1.5 proves the data-driven pattern on real iterations.
- **MCP exposure of quality-search** (arch finding: the central v0.13 module is CLI-only while the agent drives MCP) — decide together with the loop-engine retirement.
- **`test_release_gate.py` cost** (4 tests ≈ 45% of suite runtime, packaging I/O) — candidate for a session-scoped shared build fixture; measure before optimizing.

---

## Execution order summary

Phase 0 (Tasks 0.1 → 0.7, strictly in order; 0.5/0.6 gates can run in parallel with 0.2 bisection if using subagents) → Phase 1 (1.1 → 1.2 → 1.3 → 1.4) → Phase 1.5 → Phase 2 (each task confirm-gated). Total: ~20 commits. After Phase 0 and after Phase 1.4, push and report to the user before continuing.
