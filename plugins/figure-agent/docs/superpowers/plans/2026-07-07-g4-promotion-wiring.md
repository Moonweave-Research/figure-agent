# G4 Promotion Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement only G4 from `docs/superpowers/specs/2026-07-07-geometry-vocabulary-gaps.md`: promote already-detected deterministic findings safely, queue visual_clash for human triage, and stop after one G4 PR.

**Architecture:** Add a small promotion layer between detector JSON outputs and `quality_defect_ledger`. Deterministic fail-closed/P5 detectors can auto-promote into the ledger; visual_clash goes into `build/promotion_queue.json` and only enters the existing bounded critique-finding path after explicit `fig-agent triage` acceptance. Advisory detectors are recorded as intentionally non-promoting.

**Tech Stack:** Python stdlib JSON/YAML/pathlib, existing `fig-agent` CLI, existing detector JSON files under `examples/<fixture>/build`, existing `critique_finding_gate`/`quality_defect_ledger` contracts, pytest.

---

## Scope Lock

- Build G4 only.
- Do not implement G1/G2/G3.
- Do not add detector logic for new geometry relations.
- Do not add LLM or pixel-heuristic pass/fail authority.
- Do not auto-promote visual_clash, layout_drift, hyphenation, or physics_grounding.
- Do not weaken existing gates. Missing/corrupt/wrong-schema evidence must block or fail loud.
- Do not continue to G2 after this PR. Stop and report.

## Phase 0.6d Precheck Finding

Current inspection of main `c60f8a8d`:

- `tex_assertions` appears eligible for auto-promote after tests are re-run on the G4 branch:
  - `check_tex_assertions.py` has `BLOCKING_STATUSES = ("violated", "anchor_missing", "anchor_ambiguous")`.
  - Existing tests include zero-match (`anchor_missing`) and multi-match (`anchor_ambiguous`).
- `semantic_assertions` is not yet auto-promote eligible unless this PR first proves/fixes P5:
  - It has `anchor_missing`.
  - `_find()` returns the first matching word, so multi-match ambiguity is not fail-loud yet.
  - G4 must either exclude semantic_assertions from auto-promote and report that, or add a narrow P5 fix with tests before enabling it.

The first implementation task below codifies this as executable eligibility, so auto-promote cannot silently expand later.

## File Map

- Modify: `plugins/figure-agent/scripts/promotion_wiring.py`
  - New module. Owns schema validation, detector tier classification, auto-promotion records, visual_clash queue records, triage acceptance synthesis, and intentionally non-promoting detector notes.
- Modify: `plugins/figure-agent/scripts/quality/quality_defect_ledger.py`
  - Read G4 auto-promoted ledger entries and triage-promoted entries.
  - Preserve current critique_finding_gate path.
  - Add `promoted_by` and `source_detector` provenance.
- Modify: `plugins/figure-agent/scripts/status.py`
  - Include promotion queue count and top-N visual_clash items in `fig-agent status`.
- Modify: `plugins/figure-agent/scripts/agent_next.py`
  - Include promotion queue count and next triage command in `fig-agent next`.
- Modify: `plugins/figure-agent/bin/fig-agent`
  - Add `fig-agent promotion-queue <fixture> --write --json`.
  - Add `fig-agent triage <fixture> --accept VC012,VC013 --reject-rest --tex-lines VC012:120:126 --defect-class text_overlap --json`.
- Test: `plugins/figure-agent/tests/test_g4_promotion_wiring.py`
  - Unit tests for tiering, fail-loud schema handling, auto-promote eligibility, queue schema, triage synthesis, and non-promoting detector notes.
- Test: `plugins/figure-agent/tests/test_g4_cli.py`
  - CLI tests for queue generation, status/next exposure, triage accept/reject, and error behavior.
- Test: `plugins/figure-agent/tests/test_g4_benchmark_vc012.py`
  - E2E-style fixture test proving VC012 can flow from `build/visual_clash.json` to triage-promoted ledger defect.
- Test: update targeted existing tests only if output shape changes:
  - `plugins/figure-agent/tests/test_status.py`
  - `plugins/figure-agent/tests/test_candidate_generator.py`
  - `plugins/figure-agent/tests/test_quality_patch_plan.py`

## Data Contracts

### `build/promotion_queue.json`

```json
{
  "schema": "figure-agent.promotion-queue.v1",
  "fixture": "fig1_overview_v5f_art_direction_001_vault",
  "source_detector": "visual_clash",
  "status": "review_required",
  "total": 44,
  "top_items": ["VC012"],
  "items": [
    {
      "id": "VC012",
      "source_detector": "visual_clash",
      "promotion_tier": "review_queue",
      "kind": "text_overlap",
      "text": "Energy",
      "bbox_px": [100, 200, 180, 230],
      "metric": 0.91,
      "crop_paths": ["build/audit_crops/visual_clash/VC012_Energy.png"],
      "evidence_inline": [
        {
          "kind": "image",
          "path": "build/audit_crops/visual_clash/VC012_Energy.png",
          "sha256": "sha256:..."
        }
      ],
      "tex_lines": null,
      "defect_class": null,
      "action": "human_review_required"
    }
  ],
  "non_promoting_detectors": [
    {"detector": "layout_drift", "reason": "reference-relative advisory"},
    {"detector": "hyphenation", "reason": "cosmetic advisory"},
    {"detector": "physics_grounding", "reason": "document meta-check advisory"}
  ]
}
```

### Triage Accept Output

```json
{
  "schema": "figure-agent.promotion-triage.v1",
  "fixture": "fig1_overview_v5f_art_direction_001_vault",
  "accepted": [
    {
      "id": "VC012",
      "promoted_by": "triage",
      "source_detector": "visual_clash",
      "tex_lines": [120, 126],
      "defect_class": "text_overlap",
      "target": {"panel": "unknown", "subregion": "text_overlap#0"},
      "evidence": [{"node_id": "VC012", "uri": "figure://fig1_overview_v5f_art_direction_001_vault/audit/visual-clash"}]
    }
  ],
  "rejected": ["VC001", "VC002"]
}
```

## Task 1: Prepare Isolated G4 Branch

**Files:**
- No source modifications.

- [ ] **Step 1: Start from main tip**

Run:

```bash
cd /Users/choemun-yeong/workspace/ResearchOS/[figure-agent]
git fetch origin main
git rev-parse --short origin/main
```

Expected:

```text
c60f8a8d
```

- [ ] **Step 2: Create isolated branch/worktree**

Use either a clean worktree or a clean checkout. Do not use the existing dirty Panel F branch.

```bash
git worktree add ../figure-agent-g4-promotion origin/main
cd ../figure-agent-g4-promotion
git switch -c g4-promotion-wiring
cd plugins/figure-agent
export FIGURE_AGENT_PLUGIN_ROOT="$PWD"
```

Expected:

```text
Switched to a new branch 'g4-promotion-wiring'
```

- [ ] **Step 3: Confirm spec and scope**

Run:

```bash
sed -n '1,120p' docs/superpowers/specs/2026-07-07-geometry-vocabulary-gaps.md
```

Expected: changelog explicitly says G4 is first, visual_clash triage is not free, and batching gaps is forbidden.

- [ ] **Step 4: Commit nothing**

Run:

```bash
git status --short
```

Expected: clean working tree.

## Task 2: Write Failing Tests for Detector Eligibility

**Files:**
- Create: `tests/test_g4_promotion_wiring.py`
- Create: `scripts/promotion_wiring.py`

- [ ] **Step 1: Add failing eligibility tests**

Create `tests/test_g4_promotion_wiring.py` with:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import promotion_wiring  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_tex_assertions_is_auto_promote_eligible_when_fail_closed_and_p5() -> None:
    state = promotion_wiring.detector_promotion_eligibility("tex_assertions")

    assert state["detector"] == "tex_assertions"
    assert state["promotion_tier"] == "auto"
    assert state["eligible"] is True
    assert state["fail_closed"] is True
    assert state["p5_zero_match"] is True
    assert state["p5_multi_match"] is True


def test_semantic_assertions_not_auto_promoted_until_multi_match_p5() -> None:
    state = promotion_wiring.detector_promotion_eligibility("semantic_assertions")

    assert state["detector"] == "semantic_assertions"
    assert state["eligible"] is False
    assert "p5_multi_match_missing" in state["blocking_reasons"]


def test_non_promoting_detectors_are_recorded_as_intentional() -> None:
    notes = promotion_wiring.non_promoting_detector_notes()

    assert notes["layout_drift"]["promotion_tier"] == "non_promoting"
    assert notes["hyphenation"]["promotion_tier"] == "non_promoting"
    assert notes["physics_grounding"]["promotion_tier"] == "non_promoting"
    assert "advisory" in notes["layout_drift"]["reason"]
```

- [ ] **Step 2: Create minimal module that still fails missing functions**

Create `scripts/promotion_wiring.py` with:

```python
from __future__ import annotations
```

- [ ] **Step 3: Run failing tests**

Run:

```bash
uv run pytest tests/test_g4_promotion_wiring.py -q
```

Expected: FAIL with missing attributes on `promotion_wiring`.

- [ ] **Step 4: Implement minimal eligibility functions**

Replace `scripts/promotion_wiring.py` with:

```python
from __future__ import annotations

from typing import Any

QUEUE_SCHEMA = "figure-agent.promotion-queue.v1"
TRIAGE_SCHEMA = "figure-agent.promotion-triage.v1"

AUTO_PROMOTE_ELIGIBILITY: dict[str, dict[str, Any]] = {
    "tex_assertions": {
        "detector": "tex_assertions",
        "promotion_tier": "auto",
        "eligible": True,
        "fail_closed": True,
        "p5_zero_match": True,
        "p5_multi_match": True,
        "blocking_reasons": [],
    },
    "semantic_assertions": {
        "detector": "semantic_assertions",
        "promotion_tier": "auto",
        "eligible": False,
        "fail_closed": True,
        "p5_zero_match": True,
        "p5_multi_match": False,
        "blocking_reasons": ["p5_multi_match_missing"],
    },
}

NON_PROMOTING_DETECTORS: dict[str, dict[str, str]] = {
    "layout_drift": {
        "detector": "layout_drift",
        "promotion_tier": "non_promoting",
        "reason": "reference-relative advisory; intentionally not read for ledger promotion",
    },
    "hyphenation": {
        "detector": "hyphenation",
        "promotion_tier": "non_promoting",
        "reason": "cosmetic advisory; intentionally not read for ledger promotion",
    },
    "physics_grounding": {
        "detector": "physics_grounding",
        "promotion_tier": "non_promoting",
        "reason": "document meta-check advisory; intentionally not read for ledger promotion",
    },
}


class PromotionWiringError(ValueError):
    pass


def detector_promotion_eligibility(detector: str) -> dict[str, Any]:
    try:
        return dict(AUTO_PROMOTE_ELIGIBILITY[detector])
    except KeyError as exc:
        raise PromotionWiringError(f"unknown_detector:{detector}") from exc


def non_promoting_detector_notes() -> dict[str, dict[str, str]]:
    return {key: dict(value) for key, value in NON_PROMOTING_DETECTORS.items()}
```

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest tests/test_g4_promotion_wiring.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/promotion_wiring.py tests/test_g4_promotion_wiring.py
git commit -m "test: lock G4 detector promotion eligibility"
```

## Task 3: Add Fail-Loud JSON Loading and Auto-Promote for tex_assertions

**Files:**
- Modify: `scripts/promotion_wiring.py`
- Modify: `tests/test_g4_promotion_wiring.py`

- [ ] **Step 1: Add failing fail-loud and auto-promote tests**

Append to `tests/test_g4_promotion_wiring.py`:

```python
def test_load_detector_report_missing_fails_loud(tmp_path: Path) -> None:
    with pytest.raises(promotion_wiring.PromotionWiringError, match="tex_assertions_missing"):
        promotion_wiring.load_detector_report(tmp_path / "missing.json", "tex_assertions")


def test_load_detector_report_corrupt_fails_loud(tmp_path: Path) -> None:
    path = tmp_path / "tex_assertions.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(promotion_wiring.PromotionWiringError, match="tex_assertions_unreadable"):
        promotion_wiring.load_detector_report(path, "tex_assertions")


def test_load_detector_report_wrong_schema_fails_loud(tmp_path: Path) -> None:
    path = tmp_path / "tex_assertions.json"
    _write_json(path, {"schema": "wrong", "issues": []})

    with pytest.raises(promotion_wiring.PromotionWiringError, match="tex_assertions_schema"):
        promotion_wiring.load_detector_report(path, "tex_assertions")


def test_tex_assertion_violation_auto_promotes_with_measurement(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "fig_demo"
    build = fixture / "build"
    _write_json(
        build / "tex_assertions.json",
        {
            "schema": "figure-agent.tex-assertions.v1",
            "source_tex": "fig_demo.tex",
            "checked": 1,
            "total": 1,
            "issues": [
                {
                    "id": "force-repels",
                    "status": "violated",
                    "message": "assertion 'force-repels' violated",
                    "measured_delta_cm": -0.42,
                }
            ],
        },
    )

    defects = promotion_wiring.auto_promoted_defects(fixture, "fig_demo")

    assert defects == [
        {
            "source": "deterministic_audit",
            "source_detector": "tex_assertions",
            "promoted_by": "auto",
            "severity": "action",
            "owner": "tool",
            "defect_class": "tex_assertion_violation",
            "affected_files": ["examples/fig_demo/fig_demo.tex"],
            "evidence": [
                {
                    "uri": "figure://fig_demo/audit/tex-assertions",
                    "node_id": "force-repels",
                    "status": "violated",
                    "measured_delta_cm": -0.42,
                }
            ],
            "selector_hint": {"kind": "assertion_id", "value": "force-repels"},
            "target": {"panel": "unknown", "subregion": "tex_assertion_violation#0"},
            "suggested_change": {
                "operation_type": "human_review_required",
                "summary": "Fix declared tex assertion violation force-repels",
                "patch": "",
            },
        }
    ]
```

- [ ] **Step 2: Run failing tests**

```bash
uv run pytest tests/test_g4_promotion_wiring.py -q
```

Expected: FAIL on missing loader and auto promotion functions.

- [ ] **Step 3: Implement strict loader and tex auto-promote**

Add to `scripts/promotion_wiring.py`:

```python
import json
from pathlib import Path

EXPECTED_SCHEMAS = {
    "tex_assertions": "figure-agent.tex-assertions.v1",
    "semantic_assertions": "figure-agent.semantic-assertions.v1",
    "visual_clash": "figure-agent.visual-clash.v1",
}


def load_detector_report(path: Path, detector: str) -> dict[str, Any]:
    if not path.is_file():
        raise PromotionWiringError(f"{detector}_missing:{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PromotionWiringError(f"{detector}_unreadable:{path}") from exc
    if not isinstance(payload, dict):
        raise PromotionWiringError(f"{detector}_schema:not_object")
    expected = EXPECTED_SCHEMAS.get(detector)
    if expected is not None and payload.get("schema") != expected:
        raise PromotionWiringError(f"{detector}_schema:{payload.get('schema')}")
    return payload


def _issue_delta(issue: dict[str, Any]) -> float | None:
    value = issue.get("measured_delta_cm")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def auto_promoted_defects(fixture: Path, name: str) -> list[dict[str, Any]]:
    defects: list[dict[str, Any]] = []
    tex_path = fixture / "build" / "tex_assertions.json"
    if tex_path.is_file():
        report = load_detector_report(tex_path, "tex_assertions")
        issues = report.get("issues")
        if not isinstance(issues, list):
            raise PromotionWiringError("tex_assertions_schema:issues")
        for index, issue in enumerate(issues):
            if not isinstance(issue, dict):
                raise PromotionWiringError("tex_assertions_schema:issue")
            status = str(issue.get("status") or "")
            if status not in {"violated", "anchor_missing", "anchor_ambiguous"}:
                continue
            assertion_id = str(issue.get("id") or f"tex_assertion_{index}")
            evidence = {
                "uri": f"figure://{name}/audit/tex-assertions",
                "node_id": assertion_id,
                "status": status,
            }
            delta = _issue_delta(issue)
            if delta is not None:
                evidence["measured_delta_cm"] = delta
            defects.append(
                {
                    "source": "deterministic_audit",
                    "source_detector": "tex_assertions",
                    "promoted_by": "auto",
                    "severity": "action",
                    "owner": "tool",
                    "defect_class": "tex_assertion_violation",
                    "affected_files": [f"examples/{name}/{name}.tex"],
                    "evidence": [evidence],
                    "selector_hint": {"kind": "assertion_id", "value": assertion_id},
                    "target": {
                        "panel": "unknown",
                        "subregion": f"tex_assertion_violation#{len(defects)}",
                    },
                    "suggested_change": {
                        "operation_type": "human_review_required",
                        "summary": f"Fix declared tex assertion violation {assertion_id}",
                        "patch": "",
                    },
                }
            )
    return defects
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_g4_promotion_wiring.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/promotion_wiring.py tests/test_g4_promotion_wiring.py
git commit -m "feat: auto-promote eligible tex assertions"
```

## Task 4: Build visual_clash Promotion Queue

**Files:**
- Modify: `scripts/promotion_wiring.py`
- Modify: `tests/test_g4_promotion_wiring.py`

- [ ] **Step 1: Add failing queue tests**

Append:

```python
def test_visual_clash_queue_contains_inline_crop_evidence(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "fig_demo"
    build = fixture / "build"
    crop = build / "audit_crops" / "visual_clash" / "VC012_Energy.png"
    crop.parent.mkdir(parents=True)
    crop.write_bytes(b"png")
    _write_json(
        build / "visual_clash.json",
        {
            "schema": "figure-agent.visual-clash.v1",
            "candidates": [
                {
                    "id": "VC012",
                    "kind": "text_overlap",
                    "text": "Energy",
                    "bbox_px": [10, 20, 30, 40],
                    "metric": 0.91,
                    "tex_lines": None,
                }
            ],
        },
    )

    queue = promotion_wiring.build_promotion_queue(fixture, "fig_demo", top_n=5)

    assert queue["schema"] == "figure-agent.promotion-queue.v1"
    assert queue["total"] == 1
    item = queue["items"][0]
    assert item["id"] == "VC012"
    assert item["promotion_tier"] == "review_queue"
    assert item["evidence_inline"][0]["path"] == "build/audit_crops/visual_clash/VC012_Energy.png"
    assert item["tex_lines"] is None
    assert item["defect_class"] is None


def test_visual_clash_queue_wrong_schema_fails_loud(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "fig_demo"
    build = fixture / "build"
    _write_json(build / "visual_clash.json", {"schema": "wrong", "candidates": []})

    with pytest.raises(promotion_wiring.PromotionWiringError, match="visual_clash_schema"):
        promotion_wiring.build_promotion_queue(fixture, "fig_demo")
```

- [ ] **Step 2: Run failing tests**

```bash
uv run pytest tests/test_g4_promotion_wiring.py -q
```

Expected: FAIL on missing `build_promotion_queue`.

- [ ] **Step 3: Implement queue builder**

Add:

```python
from hashlib import sha256


def _sha256_file(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _fixture_rel(fixture: Path, path: Path) -> str:
    return path.relative_to(fixture).as_posix()


def _visual_clash_crops(fixture: Path, clash_id: str) -> list[dict[str, str]]:
    crop_dir = fixture / "build" / "audit_crops" / "visual_clash"
    evidence = []
    for path in sorted(crop_dir.glob(f"{clash_id}_*.png")):
        if path.is_file():
            evidence.append(
                {
                    "kind": "image",
                    "path": _fixture_rel(fixture, path),
                    "sha256": _sha256_file(path),
                }
            )
    return evidence


def build_promotion_queue(fixture: Path, name: str, *, top_n: int = 10) -> dict[str, Any]:
    report = load_detector_report(fixture / "build" / "visual_clash.json", "visual_clash")
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        raise PromotionWiringError("visual_clash_schema:candidates")
    items = []
    for raw in candidates:
        if not isinstance(raw, dict):
            raise PromotionWiringError("visual_clash_schema:candidate")
        clash_id = str(raw.get("id") or "")
        if not clash_id:
            raise PromotionWiringError("visual_clash_schema:id")
        evidence = _visual_clash_crops(fixture, clash_id)
        items.append(
            {
                "id": clash_id,
                "source_detector": "visual_clash",
                "promotion_tier": "review_queue",
                "kind": raw.get("kind"),
                "text": raw.get("text"),
                "bbox_px": raw.get("bbox_px"),
                "metric": raw.get("metric"),
                "crop_paths": [item["path"] for item in evidence],
                "evidence_inline": evidence,
                "tex_lines": None,
                "defect_class": None,
                "action": "human_review_required",
            }
        )
    return {
        "schema": QUEUE_SCHEMA,
        "fixture": name,
        "source_detector": "visual_clash",
        "status": "review_required" if items else "empty",
        "total": len(items),
        "top_items": [item["id"] for item in items[:top_n]],
        "items": items,
        "non_promoting_detectors": list(non_promoting_detector_notes().values()),
    }
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_g4_promotion_wiring.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/promotion_wiring.py tests/test_g4_promotion_wiring.py
git commit -m "feat: build visual clash promotion queue"
```

## Task 5: Add `fig-agent promotion-queue` CLI

**Files:**
- Modify: `bin/fig-agent`
- Create: `tests/test_g4_cli.py`

- [ ] **Step 1: Add failing CLI test**

Create `tests/test_g4_cli.py`:

```python
from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fig_agent_promotion_queue_writes_queue(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "fig_demo"
    build = fixture / "build"
    crop = build / "audit_crops" / "visual_clash" / "VC012_Energy.png"
    crop.parent.mkdir(parents=True)
    crop.write_bytes(b"png")
    (fixture / "fig_demo.tex").write_text("\\begin{tikzpicture}\\end{tikzpicture}\n", encoding="utf-8")
    (build / "visual_clash.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.visual-clash.v1",
                "candidates": [
                    {"id": "VC012", "kind": "text_overlap", "text": "Energy", "bbox_px": [1, 2, 3, 4], "metric": 0.9}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(ROOT / "bin" / "fig-agent"),
            "promotion-queue",
            "fig_demo",
            "--write",
            "--json",
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_PLUGIN_ROOT": str(ROOT), "FIGURE_AGENT_WORKSPACE": str(tmp_path)},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["total"] == 1
    assert (build / "promotion_queue.json").is_file()
```

- [ ] **Step 2: Run failing test**

```bash
uv run pytest tests/test_g4_cli.py -q
```

Expected: FAIL because command is unknown.

- [ ] **Step 3: Add CLI handler**

In `bin/fig-agent`, add:

```python
def _promotion_queue(argv: list[str]) -> int:
    import promotion_wiring

    parser = argparse.ArgumentParser(prog="fig-agent promotion-queue")
    parser.add_argument("name")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validated_fixture_name(parser, args.name)
    paths = _paths()
    fixture = paths.examples_dir / name
    try:
        payload = promotion_wiring.build_promotion_queue(fixture, name, top_n=args.top_n)
    except promotion_wiring.PromotionWiringError as exc:
        print(f"fig-agent promotion-queue: {exc}", file=sys.stderr)
        return 1
    if args.write:
        out = fixture / "build" / "promotion_queue.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
```

Then add dispatch:

```python
    if command == "promotion-queue":
        return _promotion_queue(rest)
```

- [ ] **Step 4: Run test**

```bash
uv run pytest tests/test_g4_cli.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bin/fig-agent tests/test_g4_cli.py
git commit -m "feat: add promotion queue CLI"
```

## Task 6: Add Triage Accept Synthesis

**Files:**
- Modify: `scripts/promotion_wiring.py`
- Modify: `bin/fig-agent`
- Modify: `tests/test_g4_promotion_wiring.py`
- Modify: `tests/test_g4_cli.py`

- [ ] **Step 1: Add failing unit test for triage accept**

Append:

```python
def test_triage_accept_synthesizes_bounded_defect(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "fig_demo"
    build = fixture / "build"
    _write_json(
        build / "promotion_queue.json",
        {
            "schema": "figure-agent.promotion-queue.v1",
            "fixture": "fig_demo",
            "status": "review_required",
            "total": 1,
            "items": [
                {
                    "id": "VC012",
                    "source_detector": "visual_clash",
                    "promotion_tier": "review_queue",
                    "kind": "text_overlap",
                    "text": "Energy",
                    "bbox_px": [10, 20, 30, 40],
                    "metric": 0.91,
                    "crop_paths": ["build/audit_crops/visual_clash/VC012_Energy.png"],
                    "evidence_inline": [],
                    "tex_lines": None,
                    "defect_class": None,
                    "action": "human_review_required",
                }
            ],
        },
    )

    result = promotion_wiring.triage_promotion_queue(
        fixture,
        "fig_demo",
        accept_ids=["VC012"],
        reject_rest=True,
        tex_lines={"VC012": (120, 126)},
        defect_classes={"VC012": "text_overlap"},
    )

    assert result["schema"] == "figure-agent.promotion-triage.v1"
    promoted = result["accepted"][0]
    assert promoted["id"] == "VC012"
    assert promoted["promoted_by"] == "triage"
    assert promoted["source_detector"] == "visual_clash"
    assert promoted["tex_lines"] == [120, 126]
    assert promoted["defect_class"] == "text_overlap"
```

- [ ] **Step 2: Implement triage function**

Add:

```python
SUPPORTED_TRIAGE_DEFECT_CLASSES = {"text_overlap", "label_offset", "whitespace_balance"}


def _load_queue(fixture: Path) -> dict[str, Any]:
    queue = load_detector_report(fixture / "build" / "promotion_queue.json", "promotion_queue")
    if queue.get("schema") != QUEUE_SCHEMA:
        raise PromotionWiringError(f"promotion_queue_schema:{queue.get('schema')}")
    items = queue.get("items")
    if not isinstance(items, list):
        raise PromotionWiringError("promotion_queue_schema:items")
    return queue


EXPECTED_SCHEMAS["promotion_queue"] = QUEUE_SCHEMA


def triage_promotion_queue(
    fixture: Path,
    name: str,
    *,
    accept_ids: list[str],
    reject_rest: bool,
    tex_lines: dict[str, tuple[int, int]],
    defect_classes: dict[str, str],
) -> dict[str, Any]:
    queue = _load_queue(fixture)
    items = {str(item.get("id")): item for item in queue["items"] if isinstance(item, dict)}
    accepted = []
    for item_id in accept_ids:
        if item_id not in items:
            raise PromotionWiringError(f"triage_unknown_id:{item_id}")
        if item_id not in tex_lines:
            raise PromotionWiringError(f"triage_tex_lines_required:{item_id}")
        defect_class = defect_classes.get(item_id)
        if defect_class not in SUPPORTED_TRIAGE_DEFECT_CLASSES:
            raise PromotionWiringError(f"triage_defect_class_required:{item_id}")
        start, end = tex_lines[item_id]
        if start < 1 or end < start:
            raise PromotionWiringError(f"triage_tex_lines_invalid:{item_id}")
        accepted.append(
            {
                "id": item_id,
                "promoted_by": "triage",
                "source_detector": "visual_clash",
                "tex_lines": [start, end],
                "defect_class": defect_class,
                "target": {"panel": "unknown", "subregion": f"{defect_class}#0"},
                "evidence": [
                    {
                        "uri": f"figure://{name}/audit/visual-clash",
                        "node_id": item_id,
                    }
                ],
            }
        )
    rejected = []
    if reject_rest:
        rejected = sorted(item_id for item_id in items if item_id not in set(accept_ids))
    result = {
        "schema": TRIAGE_SCHEMA,
        "fixture": name,
        "accepted": accepted,
        "rejected": rejected,
    }
    out = fixture / "build" / "promotion_triage.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
```

- [ ] **Step 3: Add CLI parser**

In `bin/fig-agent`, add:

```python
def _parse_id_line_map(values: list[str]) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for value in values:
        item_id, start, end = value.split(":", 2)
        out[item_id] = (int(start), int(end))
    return out


def _parse_id_value_map(values: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for value in values:
        item_id, mapped = value.split(":", 1)
        out[item_id] = mapped
    return out


def _triage(argv: list[str]) -> int:
    import promotion_wiring

    parser = argparse.ArgumentParser(prog="fig-agent triage")
    parser.add_argument("name")
    parser.add_argument("--accept", default="")
    parser.add_argument("--reject-rest", action="store_true")
    parser.add_argument("--tex-lines", action="append", default=[])
    parser.add_argument("--defect-class", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validated_fixture_name(parser, args.name)
    accept_ids = [item.strip() for item in args.accept.split(",") if item.strip()]
    try:
        payload = promotion_wiring.triage_promotion_queue(
            _paths().examples_dir / name,
            name,
            accept_ids=accept_ids,
            reject_rest=args.reject_rest,
            tex_lines=_parse_id_line_map(args.tex_lines),
            defect_classes=_parse_id_value_map(args.defect_class),
        )
    except (ValueError, promotion_wiring.PromotionWiringError) as exc:
        print(f"fig-agent triage: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
```

Dispatch:

```python
    if command == "triage":
        return _triage(rest)
```

- [ ] **Step 4: Add CLI acceptance test**

Append to `tests/test_g4_cli.py`:

```python
def test_fig_agent_triage_accept_writes_promotion_triage(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "fig_demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    (fixture / "fig_demo.tex").write_text("\\node at (0,0) {Energy};\n", encoding="utf-8")
    (build / "promotion_queue.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.promotion-queue.v1",
                "fixture": "fig_demo",
                "status": "review_required",
                "total": 1,
                "items": [{"id": "VC012", "source_detector": "visual_clash", "promotion_tier": "review_queue"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            str(ROOT / "bin" / "fig-agent"),
            "triage",
            "fig_demo",
            "--accept",
            "VC012",
            "--reject-rest",
            "--tex-lines",
            "VC012:1:1",
            "--defect-class",
            "VC012:text_overlap",
            "--json",
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_PLUGIN_ROOT": str(ROOT), "FIGURE_AGENT_WORKSPACE": str(tmp_path)},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["accepted"][0]["id"] == "VC012"
    assert (build / "promotion_triage.json").is_file()
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/test_g4_promotion_wiring.py tests/test_g4_cli.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/promotion_wiring.py bin/fig-agent tests/test_g4_promotion_wiring.py tests/test_g4_cli.py
git commit -m "feat: add visual clash promotion triage"
```

## Task 7: Wire Promotions Into Quality Ledger

**Files:**
- Modify: `scripts/quality/quality_defect_ledger.py`
- Modify: `tests/test_g4_promotion_wiring.py`
- Modify or create targeted ledger test if existing fixtures are easier.

- [ ] **Step 1: Add failing ledger tests**

Append:

```python
def test_triage_promoted_visual_clash_becomes_ledger_defect(tmp_path: Path, monkeypatch) -> None:
    fixture = tmp_path / "examples" / "fig_demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    (fixture / "fig_demo.tex").write_text("% Panel A\n\\node at (0,0) {Energy};\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text("panels:\n  - id: A\n", encoding="utf-8")
    _write_json(
        build / "promotion_triage.json",
        {
            "schema": "figure-agent.promotion-triage.v1",
            "fixture": "fig_demo",
            "accepted": [
                {
                    "id": "VC012",
                    "promoted_by": "triage",
                    "source_detector": "visual_clash",
                    "tex_lines": [2, 2],
                    "defect_class": "text_overlap",
                    "target": {"panel": "A", "subregion": "text_overlap#0"},
                    "evidence": [{"uri": "figure://fig_demo/audit/visual-clash", "node_id": "VC012"}],
                }
            ],
            "rejected": [],
        },
    )

    sys.path.insert(0, str(ROOT / "scripts" / "quality"))
    import quality_defect_ledger  # noqa: E402

    monkeypatch.setattr(
        quality_defect_ledger.audit_evidence_graph,
        "build_audit_evidence_graph",
        lambda *_args, **_kwargs: {"schema": "graph", "name": "fig_demo", "nodes": []},
    )
    monkeypatch.setattr(
        quality_defect_ledger.audit_evidence_summary,
        "summarize_audit_evidence",
        lambda *_args, **_kwargs: {"detector_feedback": {}},
    )
    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "fig_demo",
        plugin_root=ROOT,
        workspace_root=tmp_path,
    )

    defect = ledger["defects"][0]
    assert defect["source_detector"] == "visual_clash"
    assert defect["promoted_by"] == "triage"
    assert defect["evidence"][0]["node_id"] == "VC012"
```

- [ ] **Step 2: Implement ledger reader**

In `quality_defect_ledger.py`, import `promotion_wiring` and add:

```python
def _promotion_triage_defects(example_dir: Path, name: str, graph_hash: str) -> list[dict[str, Any]]:
    path = example_dir / "build" / "promotion_triage.json"
    if not path.is_file():
        return []
    payload = promotion_wiring.load_detector_report(path, "promotion_triage")
    if payload.get("schema") != promotion_wiring.TRIAGE_SCHEMA:
        raise ValueError("promotion_triage_schema")
    accepted = payload.get("accepted")
    if not isinstance(accepted, list):
        raise ValueError("promotion_triage_schema:accepted")
    source_hashes = _source_hashes(example_dir, name)
    defects = []
    for item in accepted:
        if not isinstance(item, dict):
            raise ValueError("promotion_triage_schema:item")
        tex_lines = item.get("tex_lines")
        if not isinstance(tex_lines, list) or len(tex_lines) != 2:
            raise ValueError("promotion_triage_schema:tex_lines")
        start, end = tex_lines
        defect_class = str(item.get("defect_class") or "")
        defects.append(
            {
                "source": "critique_adjudication",
                "source_detector": str(item.get("source_detector") or "visual_clash"),
                "promoted_by": str(item.get("promoted_by") or "triage"),
                "evidence": item.get("evidence") if isinstance(item.get("evidence"), list) else [],
                "severity": "action",
                "owner": "tool",
                "defect_class": defect_class,
                "affected_files": [f"examples/{name}/{name}.tex"],
                "freshness": {
                    "status_input_hash": "sha256:" + "0" * 64,
                    "critique_input_hash": "sha256:" + "0" * 64,
                    "audit_evidence_graph_hash": graph_hash,
                    "source_hashes": source_hashes,
                },
                "selector_hint": {"kind": "line_range", "value": f"{start}:{end}"},
                "target": item.get("target") if isinstance(item.get("target"), dict) else {"panel": "unknown", "subregion": f"{defect_class}#0"},
                "suggested_change": {
                    "operation_type": "tikz_coordinate_adjust",
                    "summary": f"Triage-promoted visual clash {item.get('id')}",
                    "patch": "",
                },
            }
        )
    return defects
```

Then in `_detector_defects`, append:

```python
    defects += _promotion_triage_defects(example_dir, name, graph_hash)
    defects += promotion_wiring.auto_promoted_defects(example_dir, name)
```

Also add:

```python
EXPECTED_SCHEMAS["promotion_triage"] = TRIAGE_SCHEMA
```

to `promotion_wiring.py`.

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/test_g4_promotion_wiring.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add scripts/quality/quality_defect_ledger.py scripts/promotion_wiring.py tests/test_g4_promotion_wiring.py
git commit -m "feat: wire promotions into defect ledger"
```

## Task 8: Surface Queue in Status and Next

**Files:**
- Modify: `scripts/status.py`
- Modify: `scripts/agent_next.py`
- Modify: `tests/test_status.py`
- Create or modify: `tests/test_g4_cli.py`

- [ ] **Step 1: Add failing tests**

Add a status test asserting:

```python
def test_status_exposes_promotion_queue_summary(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "fig_demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    (fixture / "fig_demo.tex").write_text("", encoding="utf-8")
    (fixture / "spec.yaml").write_text("name: fig_demo\n", encoding="utf-8")
    (build / "promotion_queue.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.promotion-queue.v1",
                "fixture": "fig_demo",
                "status": "review_required",
                "total": 1,
                "top_items": ["VC012"],
                "items": [{"id": "VC012"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    import status

    result = status.build_status("fig_demo", workspace_root=tmp_path)

    assert result["promotion_queue"]["state"] == "review_required"
    assert result["promotion_queue"]["total"] == 1
    assert result["promotion_queue"]["top_items"] == ["VC012"]
```

- [ ] **Step 2: Implement status summary**

In `status.py`, add:

```python
def _promotion_queue_summary(path: Path) -> dict[str, Any]:
    payload, error = _load_build_json_mapping(path)
    if error is not None:
        return {"state": error, "path": f"build/{path.name}"}
    if payload.get("schema") != "figure-agent.promotion-queue.v1":
        return {"state": "invalid", "path": f"build/{path.name}"}
    return {
        "state": payload.get("status") or "present",
        "path": f"build/{path.name}",
        "total": payload.get("total"),
        "top_items": payload.get("top_items") if isinstance(payload.get("top_items"), list) else [],
    }
```

Then in `_finalize_status`:

```python
    result["promotion_queue"] = _promotion_queue_summary(example_dir / "build" / "promotion_queue.json")
```

- [ ] **Step 3: Add next summary**

In `agent_next.py`, read `status["promotion_queue"]` and include:

```python
{
    "kind": "promotion_queue_triage",
    "count": promotion_queue["total"],
    "top_items": promotion_queue["top_items"],
    "command": f"fig-agent triage {name} --accept <ids> --reject-rest --tex-lines <id:start:end> --defect-class <id:text_overlap> --json"
}
```

Only emit when queue state is `review_required` and total > 0.

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_status.py tests/test_g4_cli.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/status.py scripts/agent_next.py tests/test_status.py tests/test_g4_cli.py
git commit -m "feat: expose promotion queue in status"
```

## Task 9: Add Acceptance/Orphan Detector Guard Tests

**Files:**
- Modify: `tests/test_g4_promotion_wiring.py`

- [ ] **Step 1: Add grep-style guard tests**

Append:

```python
def test_g4_declared_detector_outputs_are_read_by_promotion_or_recorded() -> None:
    source = (ROOT / "scripts" / "promotion_wiring.py").read_text(encoding="utf-8")
    ledger = (ROOT / "scripts" / "quality" / "quality_defect_ledger.py").read_text(encoding="utf-8")

    assert "tex_assertions.json" in source
    assert "visual_clash.json" in source
    assert "promotion_triage.json" in ledger
    assert "layout_drift" in source and "non_promoting" in source
    assert "hyphenation" in source and "non_promoting" in source
    assert "physics_grounding" in source and "non_promoting" in source


def test_no_pixel_heuristic_auto_promote() -> None:
    source = (ROOT / "scripts" / "promotion_wiring.py").read_text(encoding="utf-8")

    assert '"visual_clash": {' not in source.split("AUTO_PROMOTE_ELIGIBILITY", 1)[1].split("}", 1)[0]
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/test_g4_promotion_wiring.py -q
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_g4_promotion_wiring.py
git commit -m "test: guard G4 detector promotion coverage"
```

## Task 10: Add VC012 Benchmark E2E

**Files:**
- Create: `tests/test_g4_benchmark_vc012.py`

- [ ] **Step 1: Add E2E benchmark test**

Create:

```python
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_vc012_triage_accept_promotes_to_quality_map(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "fig_demo"
    build = fixture / "build"
    crop = build / "audit_crops" / "visual_clash" / "VC012_Energy.png"
    crop.parent.mkdir(parents=True)
    crop.write_bytes(b"png")
    (fixture / "fig_demo.tex").write_text("% Panel A\n\\node at (0,0) {Energy};\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text("name: fig_demo\npanels:\n  - id: A\n", encoding="utf-8")
    (build / "visual_clash.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.visual-clash.v1",
                "candidates": [
                    {
                        "id": "VC012",
                        "kind": "text_overlap",
                        "text": "Energy",
                        "bbox_px": [10, 20, 30, 40],
                        "metric": 0.91,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    env = {"FIGURE_AGENT_PLUGIN_ROOT": str(ROOT), "FIGURE_AGENT_WORKSPACE": str(tmp_path)}

    queue = subprocess.run(
        [str(ROOT / "bin" / "fig-agent"), "promotion-queue", "fig_demo", "--write", "--json"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert queue.returncode == 0, queue.stderr
    assert json.loads(queue.stdout)["top_items"] == ["VC012"]

    triage = subprocess.run(
        [
            str(ROOT / "bin" / "fig-agent"),
            "triage",
            "fig_demo",
            "--accept",
            "VC012",
            "--reject-rest",
            "--tex-lines",
            "VC012:2:2",
            "--defect-class",
            "VC012:text_overlap",
            "--json",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert triage.returncode == 0, triage.stderr
    assert json.loads(triage.stdout)["accepted"][0]["source_detector"] == "visual_clash"
```

- [ ] **Step 2: Extend test to inspect ledger if existing ledger fixtures can be mocked cheaply**

If `quality-map` requires too much status/audit state, keep the unit ledger test in Task 7 as the ledger proof and make this CLI E2E prove queue+triage artifact. Do not stub a fake pass that hides broken ledger wiring.

- [ ] **Step 3: Run E2E test**

```bash
uv run pytest tests/test_g4_benchmark_vc012.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_g4_benchmark_vc012.py
git commit -m "test: prove VC012 promotion triage path"
```

## Task 11: Real Fixture Dogfood and P2 FP Packet

**Files:**
- Create: `plugins/figure-agent/build/g4_promotion_fp_review.json` or fixture-local build artifacts only.
- Do not commit human verdicts.

- [ ] **Step 1: Run real fixture queue**

Run:

```bash
./bin/fig-agent compile fig1_overview_v5f_art_direction_001_vault
./bin/fig-agent helper check_visual_clash fig1_overview_v5f_art_direction_001_vault --write-crops
./bin/fig-agent promotion-queue fig1_overview_v5f_art_direction_001_vault --write --json > build/g4_fig1_promotion_queue.json
```

Expected: `build/promotion_queue.json` exists under the fixture and includes `VC012` if the benchmark fixture still emits it.

- [ ] **Step 2: Prepare P2 human review packet**

Run equivalent queue generation for:

```bash
./bin/fig-agent promotion-queue fig2_overview --write --json > build/g4_fig2_promotion_queue.json
./bin/fig-agent promotion-queue fig3_overview --write --json > build/g4_fig3_promotion_queue.json
```

If fixture names differ, list actual names with:

```bash
find examples -maxdepth 1 -type d | sort
```

- [ ] **Step 3: Do not decide false positives**

Write a short report with candidate IDs, text, metric, bbox, and crop path. Leave verdict blank:

```json
{
  "schema": "figure-agent.g4-p2-human-review.v1",
  "requires_human_verdict": true,
  "fixtures": [
    {
      "fixture": "fig1_overview_v5f_art_direction_001_vault",
      "queue": "examples/fig1_overview_v5f_art_direction_001_vault/build/promotion_queue.json",
      "items": [
        {"id": "VC012", "text": "Energy", "verdict": null}
      ]
    }
  ]
}
```

- [ ] **Step 4: Commit only if report path is intended to be versioned**

Usually do not commit build artifacts. Include paths in PR description instead.

## Task 12: Full Verification and PR

**Files:**
- All modified files.

- [ ] **Step 1: Run targeted tests**

```bash
uv run pytest \
  tests/test_g4_promotion_wiring.py \
  tests/test_g4_cli.py \
  tests/test_g4_benchmark_vc012.py \
  tests/test_status.py \
  tests/test_quality_patch_plan.py \
  tests/test_candidate_generator.py
```

Expected: PASS.

- [ ] **Step 2: Run broader figure-agent tests affected by ledger/status**

```bash
uv run pytest tests/test_quality_benchmark.py tests/test_fig_queue.py tests/test_audit_evidence_dogfood.py
```

Expected: PASS.

- [ ] **Step 3: Run lint if configured**

```bash
uv run ruff check scripts tests bin/fig-agent
```

Expected: PASS. If ruff is not configured or command is unavailable, report that explicitly.

- [ ] **Step 4: Inspect git diff for scope**

```bash
git diff --stat
git diff -- scripts/promotion_wiring.py scripts/quality/quality_defect_ledger.py scripts/status.py scripts/agent_next.py bin/fig-agent
```

Expected: only G4 promotion wiring, queue, triage, status/next, and tests.

- [ ] **Step 5: Commit final fixups if needed**

Use single-line messages only:

```bash
git add .
git commit -m "fix: tighten G4 promotion wiring"
```

- [ ] **Step 6: Push and open PR**

```bash
git push -u origin g4-promotion-wiring
gh pr create \
  --title "Implement G4 promotion wiring" \
  --body "Implements only G4 from geometry-vocabulary-gaps: auto-promote eligible deterministic tex_assertions, visual_clash promotion queue and triage, non-promoting advisory detector notes, provenance, and VC012 benchmark proof. Does not implement G1/G2/G3."
```

- [ ] **Step 7: Stop**

Report:

- PR link
- 3-tier wiring summary
- Phase 0.6d eligibility result
- VC012 benchmark status
- P2 human FP review packet paths
- Explicitly state G2 is not started

## Self-Review

Spec coverage:

- G4 only: covered by Task 1 scope lock and all tasks.
- 3-tier promotion: Tasks 2-8.
- `promotion_queue.json`: Task 4.
- `fig-agent status`/`next`: Task 8.
- `fig-agent triage`: Task 6.
- Evidence crops inline: Task 4.
- Triage synthesis of `tex_lines` and `defect_class`: Task 6.
- Existing critique_finding_gate route: Task 7 reuses ledger-compatible bounded finding fields; implementation should preserve current critique path rather than bypass it.
- Non-promoting advisory detectors: Tasks 2 and 9.
- Provenance: Tasks 3, 6, 7.
- Fail-loud missing/corrupt/wrong-schema: Tasks 3 and 4.
- P5: Task 2 records current eligibility; tex auto-promote only. Semantic excluded until P5 multi-match is implemented.
- VC012 benchmark: Task 10.
- P2 human checkpoint: Task 11; no agent verdict.
- No batching: Tasks 1 and 12 stop after G4.

Known risk to watch during implementation:

- The visual_clash schema string may differ in current reports. If so, adapt `EXPECTED_SCHEMAS["visual_clash"]` to the real checked schema and add the exact wrong-schema test.
- `quality_defect_ledger.build_quality_defect_ledger` may require graph/status setup in tests. Keep unit tests narrow and do not weaken ledger fail-closed behavior.
- If semantic_assertions P5 multi-match is fixed in a separate already-merged Phase 0.6d before implementation starts, update Task 2 to mark semantic eligible and add auto-promote tests for semantic measured deltas. Otherwise keep semantic excluded and report it.
