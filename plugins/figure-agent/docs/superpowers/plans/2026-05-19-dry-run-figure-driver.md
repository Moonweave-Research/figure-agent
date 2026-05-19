# Dry-Run Figure Driver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dry-run `/fig_drive` surface that reads current figure status and returns one advisory next action without mutating files.

**Architecture:** Implement `scripts/fig_driver.py` as a thin read-only selector over `status.infer_stage()`. It emits stable JSON, uses the Issue 8A action/stop-boundary vocabulary, and refuses to run unless `--dry-run` is present.

**Tech Stack:** Python 3.12, pytest, existing `scripts/status.py`, existing markdown command docs.

---

## Source Of Truth

Read first:

- `docs/superpowers/specs/2026-05-19-figure-driver-orchestration-design.md`
- `docs/superpowers/issues/2026-05-19-issue-8a-figure-driver-protocol.md`
- `docs/superpowers/issues/2026-05-19-issue-8b-dry-run-figure-driver.md`
- `skills/figure-agent/SKILL.md`
- `scripts/status.py`
- `tests/test_status.py`
- `commands/fig_status.md`
- `commands/fig_loop.md`
- `commands/fig_export.md`

## File Structure

- Create `scripts/fig_driver.py`
  - Parse CLI.
  - Require `--dry-run`.
  - Call `status.infer_stage()`.
  - Select exactly one advisory action.
  - Print JSON.
  - Perform no writes.

- Create `commands/fig_drive.md`
  - Document dry-run behavior, modes, JSON fields, stop boundaries, and
    examples.

- Create `tests/test_fig_driver.py`
  - Cover mode routing, stop boundaries, JSON contract, `--dry-run` requirement,
    and no mutation.

Do not modify `scripts/status.py`, `scripts/fig_loop.py`, or
`scripts/run_export.py` unless a test proves the driver cannot be implemented
against their current public behavior.

## Task 1: RED Tests For CLI And JSON Contract

**Files:**
- Create: `tests/test_fig_driver.py`

- [ ] **Step 1: Create import skeleton and helper fixtures**

Create `tests/test_fig_driver.py`:

```python
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_driver  # noqa: E402


def _write_basic_fixture(root: Path, name: str = "driver_demo") -> Path:
    fixture = root / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: driver_demo\npanels: []\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text("% tikz\n", encoding="utf-8")
    return fixture


def _write_fresh_build_and_exports(fixture: Path, name: str = "driver_demo") -> None:
    pdf_bytes = b"%PDF-1.4 driver"
    build = fixture / "build"
    build.mkdir(exist_ok=True)
    (build / f"{name}.pdf").write_bytes(pdf_bytes)
    exports = fixture / "exports"
    exports.mkdir(exist_ok=True)
    (exports / f"{name}.pdf").write_bytes(pdf_bytes)
    (exports / f"{name}.svg").write_text("<svg/>\n", encoding="utf-8")
    (exports / f"{name}.png").write_bytes(b"\x89PNG")
    (exports / f"{name}.tif").write_bytes(b"TIFF")
    old_time = time.time() - 100
    fresh_time = time.time() - 10
    for path in (fixture / "spec.yaml", fixture / "briefing.md", fixture / f"{name}.tex"):
        path.touch()
        import os

        os.utime(path, (old_time, old_time))
    for path in [build / f"{name}.pdf", *exports.iterdir()]:
        import os

        os.utime(path, (fresh_time, fresh_time))


def _run_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict:
    return fig_driver.build_driver_summary(name, mode=mode, goal=goal, repo_root=repo_root)
```

- [ ] **Step 2: Add tests for required dry-run CLI**

Append:

```python
def test_main_requires_dry_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_basic_fixture(tmp_path)

    result = fig_driver.main(["driver_demo", "--mode", "review", "--goal", "review"], repo_root=tmp_path)

    assert result == 2
    captured = capsys.readouterr()
    assert "--dry-run is required" in captured.err
    assert captured.out == ""
```

- [ ] **Step 3: Add tests for JSON fields**

Append:

```python
def test_main_emits_json_summary_in_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_basic_fixture(tmp_path)

    result = fig_driver.main(
        ["driver_demo", "--mode", "authoring", "--goal", "tighten layout", "--dry-run"],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.driver.v1"
    assert payload["fixture"] == "driver_demo"
    assert payload["mode"] == "authoring"
    assert payload["goal"] == "tighten layout"
    assert payload["may_execute"] is False
    assert isinstance(payload["status"], dict)
    assert isinstance(payload["forbidden_actions"], list)
```

- [ ] **Step 4: Verify RED**

Run:

```bash
uv run pytest -q tests/test_fig_driver.py
```

Expected: fail because `scripts/fig_driver.py` does not exist.

## Task 2: Implement Minimal Driver Skeleton

**Files:**
- Create: `scripts/fig_driver.py`

- [ ] **Step 1: Create `fig_driver.py` with CLI and JSON output**

Create `scripts/fig_driver.py`:

```python
"""Dry-run advisory driver for one figure."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from status import infer_stage  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.driver.v1"
MODES = frozenset({"authoring", "review", "release", "polish"})


def _compact_status(status: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "stage",
        "next",
        "notes",
        "render_state",
        "critique_state",
        "export_state",
        "acceptance_state",
        "final_artifact_state",
        "final_artifact_kind",
        "final_artifact_path",
        "workflow_ready",
        "golden_ready",
        "release_ready",
        "final_ready",
    )
    return {key: status.get(key) for key in keys}


def _summary(
    *,
    name: str,
    mode: str,
    goal: str,
    status: dict[str, Any],
    action: str,
    safe_command: str | None,
    stop_boundary: str | None,
    reason: str,
    forbidden_actions: list[str],
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": name,
        "mode": mode,
        "goal": goal,
        "status": _compact_status(status),
        "action": action,
        "safe_command": safe_command,
        "stop_boundary": stop_boundary,
        "reason": reason,
        "forbidden_actions": forbidden_actions,
        "may_execute": False,
    }


def build_driver_summary(
    name: str,
    *,
    mode: str,
    goal: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"unsupported mode: {mode}")
    example_dir = repo_root / "examples" / name
    status = infer_stage(example_dir)
    return _select_action(name, mode=mode, goal=goal, status=status)


def _select_action(name: str, *, mode: str, goal: str, status: dict[str, Any]) -> dict[str, Any]:
    return _summary(
        name=name,
        mode=mode,
        goal=goal,
        status=status,
        action="run_compile",
        safe_command=f"bash scripts/compile.sh examples/{name}/{name}.tex",
        stop_boundary=None,
        reason="render is not fresh",
        forbidden_actions=_forbidden_actions(mode),
    )


def _forbidden_actions(mode: str) -> list[str]:
    if mode == "authoring":
        return ["run_critique", "run_export", "run_fig_loop", "polish_handoff_stop", "release_blocked"]
    if mode == "review":
        return ["set_accepted", "edit_generated_export", "edit_polished_svg"]
    if mode == "release":
        return ["edit_source", "set_accepted", "force_golden", "edit_polished_svg"]
    return ["edit_source", "set_accepted", "edit_generated_export", "run_critique_authoring"]


def main(argv: list[str] | None = None, *, repo_root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--mode", choices=sorted(MODES), required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not args.dry_run:
        print("fig_driver.py: --dry-run is required in Issue 8B", file=sys.stderr)
        return 2
    try:
        summary = build_driver_summary(args.name, mode=args.mode, goal=args.goal, repo_root=repo_root)
    except ValueError as exc:
        print(f"fig_driver.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run tests**

Run:

```bash
uv run pytest -q tests/test_fig_driver.py
```

Expected: JSON/CLI tests pass; mode-routing tests from later tasks are not added yet.

## Task 3: Add Mode Routing Tests And Implementation

**Files:**
- Modify: `tests/test_fig_driver.py`
- Modify: `scripts/fig_driver.py`

- [ ] **Step 1: Add routing tests**

Append these tests:

```python
def test_authoring_mode_completes_when_render_fresh(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None


def test_review_mode_stops_for_reference_missing(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        "name: driver_demo\nreference_image: reference/missing.png\npanels: []\n",
        encoding="utf-8",
    )
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_critique"
    assert summary["stop_boundary"] == "reference_missing"
    assert summary["safe_command"] is None


def test_review_mode_stops_for_host_critique_when_critique_missing(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    reference = fixture / "reference" / "ref.png"
    reference.parent.mkdir()
    reference.write_bytes(b"\x89PNG")
    (fixture / "spec.yaml").write_text(
        "name: driver_demo\nreference_image: reference/ref.png\npanels: []\n",
        encoding="utf-8",
    )
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_critique"
    assert summary["stop_boundary"] == "host_llm_critique_required"
    assert summary["safe_command"] == "/fig_critique driver_demo"


def test_review_mode_runs_fig_loop_when_prerequisites_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _example, _status: False)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert summary["safe_command"] == "uv run python3 scripts/fig_loop.py driver_demo --goal 'review' --json"


def test_release_mode_reports_release_blocked_without_mutation(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "release_blocked"
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"
    assert summary["may_execute"] is False


def test_polish_mode_requires_current_export_before_polish(tmp_path: Path) -> None:
    _write_basic_fixture(tmp_path)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "run_compile"
    assert "polish_handoff_stop" in summary["forbidden_actions"] or summary["stop_boundary"] is None


def test_polish_mode_stops_for_polish_handoff_when_export_current(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["stop_boundary"] is None
```

- [ ] **Step 2: Implement routing**

Update `_select_action()` to:

- return `create_or_fix_source` for stage 0/1 source gaps
- return `run_compile` when `render_state` is `MISSING` or `STALE`
- return `run_critique` with `reference_missing` for `critique_state: REFERENCE_MISSING`
- return `run_critique` with `host_llm_critique_required` for missing/stale critique
- return `run_adjudicate` when review mode has fresh critique and adjudication needs action
- return `run_fig_loop` when review prerequisites are closed
- return `release_blocked` in release mode when `release_ready` is false
- return `polish_handoff_stop` in polish mode after generated export is current and final artifact is absent/missing
- return `complete` when the selected mode's completion condition is met

Add helper:

```python
def _adjudication_needs_action(example_dir: Path, status: dict[str, Any]) -> bool:
    if status.get("critique_state") != "FRESH":
        return False
    adjudication_path = example_dir / "critique_adjudication.yaml"
    if not adjudication_path.is_file():
        return True
    try:
        from critique_adjudication import adjudication_is_stale, load_adjudication

        load_adjudication(adjudication_path)
        return adjudication_is_stale(adjudication_path, example_dir / "critique.md")
    except Exception:
        return True
```

- [ ] **Step 3: Run targeted tests**

Run:

```bash
uv run pytest -q tests/test_fig_driver.py
```

Expected: all `test_fig_driver.py` tests pass.

## Task 4: No-Mutation And Command Docs

**Files:**
- Modify: `tests/test_fig_driver.py`
- Create: `commands/fig_drive.md`

- [ ] **Step 1: Add no-mutation test**

Append:

```python
def test_driver_dry_run_does_not_mutate_fixture_files(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    before = {
        path.relative_to(fixture): path.read_bytes()
        for path in fixture.rglob("*")
        if path.is_file()
    }

    _run_driver("driver_demo", mode="review", goal="dry", repo_root=tmp_path)

    after = {
        path.relative_to(fixture): path.read_bytes()
        for path in fixture.rglob("*")
        if path.is_file()
    }
    assert after == before
```

- [ ] **Step 2: Create command doc**

Create `commands/fig_drive.md`:

```markdown
---
description: Dry-run figure driver that reads status and recommends one next action without mutation.
---

Run the advisory driver for one figure.

**Usage**: `/fig_drive <name> --mode review --goal "<goal>" --dry-run`

Run from the plugin root:

```bash
uv run python3 scripts/fig_driver.py <name> --mode review --goal "<goal>" --dry-run
```

`--dry-run` is required. This command does not compile, export, critique, patch,
polish, accept, stage, commit, or write loop artifacts. It reads current figure
state and prints JSON with one recommended action.

Modes:

- `authoring`: source/build loop only.
- `review`: compile, critique, adjudication, and `/fig_loop` checkpoint.
- `release`: accepted/golden/final readiness.
- `polish`: SVG final-artifact handoff after generated export is current.

The output includes `action`, `safe_command`, `stop_boundary`, `reason`, and
`forbidden_actions`. If `stop_boundary` is non-null, stop and satisfy that
boundary instead of running another command by intuition.
```

- [ ] **Step 3: Run docs and targeted tests**

Run:

```bash
uv run pytest -q tests/test_fig_driver.py tests/test_status.py tests/test_fig_loop.py tests/test_run_export.py
uv run ruff check scripts/fig_driver.py tests/test_fig_driver.py
git diff --check
```

Expected: all pass.

## Task 5: Plugin Validation And Review

**Files:**
- Review all changed files.

- [ ] **Step 1: Validate plugin**

Run:

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all validation commands pass.

- [ ] **Step 2: Run three review passes**

Review 1: driver-state correctness.

- Does every mode return exactly one action?
- Are critique/reference gaps stopped before export?
- Does review mode call `/fig_loop` only after prerequisites?

Review 2: mutation containment.

- Does `fig_driver.py` avoid writing files?
- Are `may_execute` and `--dry-run` enforced?
- Are accepted/golden/SVG/source changes forbidden?

Review 3: handoff readiness.

- Can a future executor use `action`, `safe_command`, and `stop_boundary` without
  parsing prose?
- Are identifiers stable and documented?
- Does `/fig_drive` reduce the `/fig_loop` naming confusion?

Fix any defect and rerun targeted tests before counting the review as clean.

- [ ] **Step 3: Commit**

Run:

```bash
git add scripts/fig_driver.py commands/fig_drive.md tests/test_fig_driver.py docs/superpowers/issues/2026-05-19-issue-8b-dry-run-figure-driver.md docs/superpowers/plans/2026-05-19-dry-run-figure-driver.md
git commit -m "Add dry-run figure driver plan"
```

If implementation was completed in the same branch, use:

```bash
git commit -m "Add dry-run figure driver"
```

## Completion Report Template

```markdown
Issue 8B completion report

Files changed:
- `scripts/fig_driver.py`
- `commands/fig_drive.md`
- `tests/test_fig_driver.py`
- `docs/superpowers/issues/2026-05-19-issue-8b-dry-run-figure-driver.md`
- `docs/superpowers/plans/2026-05-19-dry-run-figure-driver.md`

Implemented:
- dry-run-only CLI
- stable driver JSON schema
- mode-based action selection
- no-mutation tests

Verification:
- command -> result

Review passes:
- Review 1:
- Review 2:
- Review 3:

Remaining risks:
- No known Issue 8B blocker remains.
```
