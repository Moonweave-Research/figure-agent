# Reference-Aware Candidate Search Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first reference-aware candidate-search vertical slice: intent model, candidate set, sandbox manifest, ranking authority, and explicit apply boundary.

**Architecture:** Keep CLI as the source of truth and MCP as a facade. Implement small schema-first modules under `plugins/figure-agent/scripts/`, wire public `fig-agent` commands only after module tests pass, and add MCP tools only after CLI behavior is stable. Candidate generation is deterministic and fixture-local; rendering/ranking can only preserve or downgrade mutation authority.

**Tech Stack:** Python 3 standard library, existing figure-agent script modules, PyYAML where current scripts already use it, pytest, ruff, existing `bin/fig-agent`, existing MCP stdio facade.

---

## Scope

This plan implements the spec in conservative slices. The first useful shipped
state is:

```text
fig-agent intent <name> --json
fig-agent candidates <name> --json --output build/candidates/candidate_set.json
fig-agent render-candidates <name> --candidate-set build/candidates/candidate_set.json
fig-agent rank-candidates <name> --candidate-set build/candidates/candidate_set.json --json
fig-agent review-candidate <name> CAND001 --json
```

`apply-candidate` is implemented after the read/render/rank contracts prove that
mutation authority is unambiguous.

Do not modify user manuscript fixtures. Use synthetic fixtures under `tmp_path`
for tests and fixture-local generated artifacts under `examples/<name>/build/candidates/`.

## File Structure

Create:

- `plugins/figure-agent/scripts/figure_intent_model.py`
  - Read-only fixture intent model.
  - Owns fixture-local input contract and missing-input downgrade decisions.
- `plugins/figure-agent/scripts/candidate_contracts.py`
  - Shared schema constants, canonical hash helper, path validation, and authority enums.
- `plugins/figure-agent/scripts/candidate_generator.py`
  - Builds deterministic candidate sets from intent model and quality-map style evidence.
- `plugins/figure-agent/scripts/candidate_render.py`
  - Creates sandbox candidate copies and manifests without touching source exports.
- `plugins/figure-agent/scripts/candidate_rank.py`
  - Computes hard-gate state, scores, and `effective_apply_authority`.
- `plugins/figure-agent/scripts/candidate_review_packet.py`
  - Emits JSON review packets with artifact descriptors.
- `plugins/figure-agent/scripts/candidate_apply.py`
  - Explicit `--apply` source mutation, stale checks, and rollback handoff.
- `plugins/figure-agent/tests/test_figure_intent_model.py`
- `plugins/figure-agent/tests/test_candidate_contracts.py`
- `plugins/figure-agent/tests/test_candidate_generator.py`
- `plugins/figure-agent/tests/test_candidate_render.py`
- `plugins/figure-agent/tests/test_candidate_rank.py`
- `plugins/figure-agent/tests/test_candidate_review_packet.py`
- `plugins/figure-agent/tests/test_candidate_apply.py`
- `plugins/figure-agent/tests/test_candidate_cli_contract.py`

Modify:

- `plugins/figure-agent/bin/fig-agent`
  - Add public command routing.
- `plugins/figure-agent/mcp/figure_agent_server.py`
  - Add read/rank/review tools after CLI contracts land.
- `plugins/figure-agent/scripts/release_gate.py`
  - Add focused candidate-search tests.
- `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md`
  - Add new schema/module ownership.
- `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md`
  - Update inventory rows.

## Phase 1: Intent Model

### Task 1: Intent Model Schema and Fixture-Local Inputs

**Files:**
- Create: `plugins/figure-agent/scripts/figure_intent_model.py`
- Test: `plugins/figure-agent/tests/test_figure_intent_model.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import figure_intent_model  # noqa: E402


def _fixture(workspace: Path, name: str = "intent_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        """
name: intent_demo
panels:
  - id: A
    caption: Kinetic panel
    bbox_pdf_cm: [0.0, 0.0, 4.0, 3.0]
    reference_image: reference/panel_a.png
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "intent_demo.tex").write_text("% source\n", encoding="utf-8")
    (fixture / "reference").mkdir()
    (fixture / "reference" / "panel_a.png").write_bytes(b"fake")
    return fixture


def test_intent_model_reads_fixture_local_inputs(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = figure_intent_model.build_intent_model(
        "intent_demo",
        workspace_root=workspace,
        plugin_root=Path("plugins/figure-agent").resolve(),
    )

    assert payload["schema"] == "figure-agent.intent-model.v1"
    assert payload["fixture"] == "intent_demo"
    assert payload["panels"][0]["id"] == "A"
    assert payload["panels"][0]["role"] == "Kinetic panel"
    assert payload["panels"][0]["apply_authority_floor"] == "apply_eligible"
    assert payload["inputs"]["panel_references"]["state"] == "present"


def test_intent_model_rejects_reference_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "spec.yaml").write_text(
        """
name: intent_demo
panels:
  - id: A
    reference_image: ../outside.png
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = figure_intent_model.build_intent_model(
        "intent_demo",
        workspace_root=workspace,
        plugin_root=Path("plugins/figure-agent").resolve(),
    )

    assert payload["panels"][0]["apply_authority_floor"] == "review_only"
    assert payload["inputs"]["panel_references"]["state"] == "blocked"
    assert "path_escape" in payload["inputs"]["panel_references"]["reasons"]


def test_intent_model_missing_caption_does_not_invent_claims(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = figure_intent_model.build_intent_model(
        "intent_demo",
        workspace_root=workspace,
        plugin_root=Path("plugins/figure-agent").resolve(),
    )

    assert payload["inputs"]["caption"]["state"] == "missing_optional"
    assert payload["panels"][0]["semantic_claims"] == []
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_figure_intent_model.py
```

Expected: collection fails with `ModuleNotFoundError: No module named 'figure_intent_model'`.

- [ ] **Step 3: Implement minimal intent model**

Create `plugins/figure-agent/scripts/figure_intent_model.py`:

```python
"""Build a read-only fixture intent model for candidate search."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.intent-model.v1"


def _state(path: Path, *, required: bool) -> dict[str, Any]:
    if path.is_file():
        return {"state": "present", "path": str(path)}
    return {
        "state": "missing_required" if required else "missing_optional",
        "path": str(path),
    }


def _fixture_relative_path(example_dir: Path, value: Any) -> tuple[str, list[str]]:
    if not isinstance(value, str) or not value.strip():
        return "", ["missing"]
    candidate = (example_dir / value).resolve()
    try:
        candidate.relative_to(example_dir.resolve())
    except ValueError:
        return str(candidate), ["path_escape"]
    if not candidate.is_file():
        return str(candidate), ["missing"]
    return str(candidate), []


def _load_spec(spec_path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def build_intent_model(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    spec_path = example_dir / "spec.yaml"
    spec = _load_spec(spec_path)
    panels_raw = spec.get("panels")
    panels = panels_raw if isinstance(panels_raw, list) else []

    panel_reference_state = "missing_optional"
    panel_reference_reasons: list[str] = []
    output_panels: list[dict[str, Any]] = []
    for index, raw_panel in enumerate(panels):
        panel = raw_panel if isinstance(raw_panel, dict) else {}
        reference_path, reference_reasons = _fixture_relative_path(
            example_dir,
            panel.get("reference_image"),
        )
        if reference_reasons:
            panel_reference_reasons.extend(reference_reasons)
            panel_reference_state = "blocked" if "path_escape" in reference_reasons else panel_reference_state
        else:
            panel_reference_state = "present"
        role = str(panel.get("caption") or panel.get("role") or "unknown")
        output_panels.append(
            {
                "id": str(panel.get("id") or f"panel_{index + 1}"),
                "role": role,
                "bbox_pdf_cm": panel.get("bbox_pdf_cm") if isinstance(panel.get("bbox_pdf_cm"), list) else [],
                "reference_image": reference_path,
                "semantic_claims": [],
                "visual_priorities": [],
                "locked_invariants": [],
                "allowed_edit_classes": ["label_offset", "whitespace", "style_normalization"],
                "apply_authority_floor": "review_only" if reference_reasons else "apply_eligible",
            }
        )

    return {
        "schema": SCHEMA,
        "fixture": name,
        "workspace_root": str(paths.workspace_root),
        "inputs": {
            "spec": _state(spec_path, required=True),
            "briefing": _state(example_dir / "briefing.md", required=True),
            "source": _state(example_dir / f"{name}.tex", required=True),
            "caption": _state(example_dir / "caption.md", required=False),
            "panel_references": {
                "state": panel_reference_state,
                "reasons": sorted(set(panel_reference_reasons)),
            },
            "coordinate_hints": _state(example_dir / "coordinate_hints.yaml", required=False),
            "perception_pack": {
                "state": "present" if (example_dir / "build" / "perception").is_dir() else "missing_optional"
            },
            "semantic_invariants": _state(example_dir / "semantic_invariants.yaml", required=False),
        },
        "panels": output_panels,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(build_intent_model(args.name), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_figure_intent_model.py
```

Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/figure_intent_model.py plugins/figure-agent/tests/test_figure_intent_model.py
git commit -m "Add candidate intent model"
```

## Phase 2: Candidate Contracts and Generation

### Task 2: Shared Candidate Contract Helpers

**Files:**
- Create: `plugins/figure-agent/scripts/candidate_contracts.py`
- Test: `plugins/figure-agent/tests/test_candidate_contracts.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_contracts  # noqa: E402


def test_effective_authority_downgrades_hard_gate_states() -> None:
    assert (
        candidate_contracts.effective_apply_authority("apply_eligible", "pass")
        == "apply_eligible"
    )
    assert (
        candidate_contracts.effective_apply_authority("apply_eligible", "human_required")
        == "review_only"
    )
    assert (
        candidate_contracts.effective_apply_authority("apply_eligible", "rejected")
        == "rejected"
    )


def test_fixture_path_rejects_escape(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "demo"
    fixture.mkdir(parents=True)

    assert candidate_contracts.fixture_relative_path(fixture, "demo.tex") == fixture / "demo.tex"
    try:
        candidate_contracts.fixture_relative_path(fixture, "../outside.tex")
    except candidate_contracts.CandidateContractError as exc:
        assert "path_escape" in str(exc)
    else:
        raise AssertionError("expected path_escape")
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_contracts.py
```

Expected: `ModuleNotFoundError: No module named 'candidate_contracts'`.

- [ ] **Step 3: Implement contract helper**

Create `plugins/figure-agent/scripts/candidate_contracts.py`:

```python
"""Shared contracts for candidate-search artifacts."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

APPLY_AUTHORITIES = frozenset({"apply_eligible", "review_only", "rejected"})
HARD_GATE_STATES = frozenset({"pass", "human_required", "rejected"})


class CandidateContractError(ValueError):
    """Expected user-facing candidate contract error."""


def canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()


def fixture_relative_path(example_dir: Path, value: str) -> Path:
    candidate = (example_dir / value).resolve()
    try:
        candidate.relative_to(example_dir.resolve())
    except ValueError as exc:
        raise CandidateContractError("path_escape") from exc
    return candidate


def effective_apply_authority(apply_authority: str, hard_gate_state: str) -> str:
    if apply_authority not in APPLY_AUTHORITIES:
        raise CandidateContractError(f"invalid apply_authority: {apply_authority}")
    if hard_gate_state not in HARD_GATE_STATES:
        raise CandidateContractError(f"invalid hard_gate_state: {hard_gate_state}")
    if hard_gate_state == "rejected":
        return "rejected"
    if hard_gate_state == "human_required":
        return "review_only"
    return apply_authority
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_contracts.py
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/candidate_contracts.py plugins/figure-agent/tests/test_candidate_contracts.py
git commit -m "Add candidate contract helpers"
```

### Task 3: Candidate Generator

**Files:**
- Create: `plugins/figure-agent/scripts/candidate_generator.py`
- Test: `plugins/figure-agent/tests/test_candidate_generator.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_generator  # noqa: E402


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    return fixture


def test_candidates_include_required_provenance_fields(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    candidate = payload["candidates"][0]
    assert payload["schema"] == "figure-agent.candidate-set.v1"
    assert payload["base"]["tex_hash"].startswith("sha256:")
    assert candidate["affected_files"] == ["examples/candidate_demo/candidate_demo.tex"]
    assert candidate["selector"]["original_hash"].startswith("sha256:")
    assert candidate["rollback"]["strategy"] == "reverse_operations"
    assert candidate["verification"]["required_commands"] == [
        "fig-agent compile candidate_demo --strict",
        "fig-agent status candidate_demo --json",
    ]
    assert candidate["apply_authority"] == "apply_eligible"


def test_candidates_do_not_emit_for_missing_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples" / "candidate_demo").mkdir(parents=True)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"][0]["code"] == "source_missing"
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_generator.py
```

Expected: `ModuleNotFoundError: No module named 'candidate_generator'`.

- [ ] **Step 3: Implement minimal candidate generator**

Create `plugins/figure-agent/scripts/candidate_generator.py` with a narrow first
candidate family: one label-offset text replacement only when the synthetic
source has one line containing `(0,0)`.

```python
"""Generate deterministic candidate improvement sets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import candidate_contracts
import fixture_identity
import runtime_paths
from quality_manifest import file_sha256

SCHEMA = "figure-agent.candidate-set.v1"


def _source_hash(source: Path) -> str:
    return file_sha256(source) if source.is_file() else "sha256:" + "0" * 64


def build_candidate_set(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    source_rel = Path("examples") / name / f"{name}.tex"
    source = paths.workspace_root / source_rel
    base = {
        "tex_hash": _source_hash(source),
        "status_hash": "sha256:" + "0" * 64,
        "intent_model_hash": "sha256:" + "0" * 64,
    }
    if not source.is_file():
        return {
            "schema": SCHEMA,
            "fixture": name,
            "base": base,
            "candidates": [],
            "refusals": [{"code": "source_missing"}],
        }
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    candidates: list[dict[str, Any]] = []
    if len(lines) == 1 and "(0,0)" in lines[0]:
        original = lines[0]
        replacement = original.replace("(0,0)", "(0.2,0)", 1)
        candidates.append(
            {
                "id": "CAND001",
                "target": {"panel": "unknown", "subregion": "label-a"},
                "edit_class": "label_offset",
                "affected_files": [source_rel.as_posix()],
                "selector": {
                    "kind": "line_range_with_hash",
                    "path": source_rel.as_posix(),
                    "start_line": 1,
                    "end_line": 1,
                    "original_hash": candidate_contracts.canonical_hash(original),
                },
                "operations": [
                    {
                        "kind": "replace_text",
                        "path": source_rel.as_posix(),
                        "original": original,
                        "replacement": replacement,
                    }
                ],
                "risk": "low",
                "expected_delta": ["improve label clearance"],
                "semantic_risks": [],
                "rollback": {"strategy": "reverse_operations"},
                "verification": {
                    "required_commands": [
                        f"fig-agent compile {name} --strict",
                        f"fig-agent status {name} --json",
                    ]
                },
                "apply_authority": "apply_eligible",
                "blocked_if": ["semantic_invariant_failed", "render_failed"],
            }
        )
    return {
        "schema": SCHEMA,
        "fixture": name,
        "base": base,
        "candidates": candidates,
        "refusals": [] if candidates else [{"code": "no_supported_candidate"}],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(build_candidate_set(args.name), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_generator.py
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/candidate_generator.py plugins/figure-agent/tests/test_candidate_generator.py
git commit -m "Add deterministic candidate generator"
```

## Phase 3: Render Sandbox and Ranking

### Task 4: Candidate Manifest Sandbox

**Files:**
- Create: `plugins/figure-agent/scripts/candidate_render.py`
- Test: `plugins/figure-agent/tests/test_candidate_render.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_generator  # noqa: E402
import candidate_render  # noqa: E402


def test_render_writes_manifest_without_touching_exports(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    (fixture / "candidate_demo.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    before_exports = sorted((fixture / "exports").rglob("*")) if (fixture / "exports").exists() else []
    candidate_set = candidate_generator.build_candidate_set("candidate_demo", workspace_root=workspace)

    result = candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
    )

    manifest = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    assert result["rendered"][0]["candidate_id"] == "CAND001"
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["schema"] == "figure-agent.candidate-manifest.v1"
    assert data["base"]["source_commit"]
    assert data["tool_versions"]["fig_agent"]
    assert data["effective_apply_authority"] == "apply_eligible"
    after_exports = sorted((fixture / "exports").rglob("*")) if (fixture / "exports").exists() else []
    assert after_exports == before_exports
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_render.py
```

Expected: `ModuleNotFoundError: No module named 'candidate_render'`.

- [ ] **Step 3: Implement manifest-only sandbox render**

Create `plugins/figure-agent/scripts/candidate_render.py`. The first slice does
not run TeX; it writes candidate source copy and manifest. Real compile enters a
later refinement.

```python
"""Create candidate sandbox manifests without touching source exports."""

from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path
from typing import Any

import candidate_contracts
import runtime_paths

SCHEMA = "figure-agent.candidate-manifest.v1"


def _source_commit(workspace_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=workspace_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def render_candidate_set(
    name: str,
    candidate_set: dict[str, Any],
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    rendered: list[dict[str, Any]] = []
    for candidate in candidate_set.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        candidate_id = str(candidate["id"])
        out_dir = example_dir / "build" / "candidates" / candidate_id
        out_dir.mkdir(parents=True, exist_ok=True)
        hard_gate_state = "pass"
        effective = candidate_contracts.effective_apply_authority(
            str(candidate.get("apply_authority")),
            hard_gate_state,
        )
        manifest = {
            "schema": SCHEMA,
            "candidate_id": candidate_id,
            "fixture": name,
            "base": {
                "source_commit": _source_commit(paths.workspace_root),
                "tex_hash": candidate_set.get("base", {}).get("tex_hash", "sha256:" + "0" * 64),
                "status_hash": candidate_set.get("base", {}).get("status_hash", "sha256:" + "0" * 64),
                "render_hash": "sha256:" + "0" * 64,
            },
            "tool_versions": {
                "fig_agent": "0.11.x",
                "python": platform.python_version(),
                "tex_engine": "not_run",
            },
            "operations": candidate.get("operations", []),
            "artifacts": {},
            "verification": {
                "commands": candidate.get("verification", {}).get("required_commands", []),
                "hard_gate_state": hard_gate_state,
            },
            "apply_authority": candidate.get("apply_authority"),
            "effective_apply_authority": effective,
        }
        path = out_dir / "candidate_manifest.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        rendered.append({"candidate_id": candidate_id, "manifest": str(path)})
    return {"schema": "figure-agent.candidate-render-result.v1", "fixture": name, "rendered": rendered}
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_render.py
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/candidate_render.py plugins/figure-agent/tests/test_candidate_render.py
git commit -m "Add candidate sandbox manifests"
```

### Task 5: Ranking Authority

**Files:**
- Create: `plugins/figure-agent/scripts/candidate_rank.py`
- Test: `plugins/figure-agent/tests/test_candidate_rank.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_rank  # noqa: E402


def test_human_required_gate_downgrades_effective_authority() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "verification": {"hard_gate_state": "human_required"},
    }

    score = candidate_rank.score_manifest(manifest)

    assert score["schema"] == "figure-agent.candidate-score.v1"
    assert score["hard_gate_state"] == "human_required"
    assert score["effective_apply_authority"] == "review_only"
    assert score["verdict"] == "reviewable"


def test_rejected_gate_blocks_ranking_above_reviewable() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "verification": {"hard_gate_state": "rejected"},
    }

    score = candidate_rank.score_manifest(manifest)

    assert score["effective_apply_authority"] == "rejected"
    assert score["rank_score"] == 0.0
    assert score["verdict"] == "rejected"
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_rank.py
```

Expected: `ModuleNotFoundError: No module named 'candidate_rank'`.

- [ ] **Step 3: Implement ranking helper**

Create `plugins/figure-agent/scripts/candidate_rank.py`:

```python
"""Rank candidate manifests and compute effective apply authority."""

from __future__ import annotations

from typing import Any

import candidate_contracts

SCHEMA = "figure-agent.candidate-score.v1"


def score_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    hard_gate_state = str((manifest.get("verification") or {}).get("hard_gate_state", "rejected"))
    effective = candidate_contracts.effective_apply_authority(
        str(manifest.get("apply_authority", "rejected")),
        hard_gate_state,
    )
    verdict = "rejected" if hard_gate_state == "rejected" else "reviewable"
    rank_score = 0.0 if hard_gate_state == "rejected" else 0.5
    return {
        "schema": SCHEMA,
        "candidate_id": str(manifest.get("candidate_id")),
        "hard_gate_state": hard_gate_state,
        "hard_gate_failures": [] if hard_gate_state == "pass" else [hard_gate_state],
        "scores": {
            "legibility": 0.0,
            "reference_faithfulness": 0.0,
            "semantic_preservation": 1.0 if hard_gate_state != "rejected" else 0.0,
            "review_burden": 0.5,
        },
        "rank_score": rank_score,
        "verdict": verdict,
        "effective_apply_authority": effective,
    }
```

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_rank.py
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/candidate_rank.py plugins/figure-agent/tests/test_candidate_rank.py
git commit -m "Add candidate ranking authority"
```

## Phase 4: CLI Integration

### Task 6: Public `fig-agent` Candidate Commands

**Files:**
- Modify: `plugins/figure-agent/bin/fig-agent`
- Test: `plugins/figure-agent/tests/test_candidate_cli_contract.py`

- [ ] **Step 1: Write CLI contract tests**

```python
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def test_fig_agent_intent_and_candidates_are_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: candidate_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "candidate_demo.tex").write_text("\\node (label-a) at (0,0) {Old Label};\n", encoding="utf-8")
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))

    intent = subprocess.run(
        [str(FIG_AGENT), "intent", "candidate_demo", "--json"],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )
    candidates = subprocess.run(
        [str(FIG_AGENT), "candidates", "candidate_demo", "--json"],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert intent.returncode == 0, intent.stderr
    assert candidates.returncode == 0, candidates.stderr
    assert json.loads(intent.stdout)["schema"] == "figure-agent.intent-model.v1"
    assert json.loads(candidates.stdout)["schema"] == "figure-agent.candidate-set.v1"
    after = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    assert after == before


def test_fig_agent_candidates_output_is_fixture_local(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: candidate_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "candidate_demo.tex").write_text("\\node (label-a) at (0,0) {Old Label};\n", encoding="utf-8")

    result = subprocess.run(
        [
            str(FIG_AGENT),
            "candidates",
            "candidate_demo",
            "--json",
            "--output",
            "build/candidates/candidate_set.json",
        ],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    output = fixture / "build" / "candidates" / "candidate_set.json"
    assert result.returncode == 0, result.stderr
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["schema"] == "figure-agent.candidate-set.v1"
```

- [ ] **Step 2: Run test and verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_cli_contract.py
```

Expected: fails with `unknown command 'intent'`.

- [ ] **Step 3: Wire `bin/fig-agent`**

Add imports inside command handlers only:

```python
def _intent(argv: list[str]) -> int:
    import figure_intent_model

    parser = argparse.ArgumentParser(prog="fig-agent intent")
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validated_fixture_name(parser, args.name)
    payload = figure_intent_model.build_intent_model(
        name,
        plugin_root=_paths().plugin_root,
        workspace_root=_paths().workspace_root,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _candidates(argv: list[str]) -> int:
    import candidate_generator
    import candidate_contracts

    parser = argparse.ArgumentParser(prog="fig-agent candidates")
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--scope", choices=("safe-mechanics", "label-offsets"), default="safe-mechanics")
    args = parser.parse_args(argv)
    name = _validated_fixture_name(parser, args.name)
    payload = candidate_generator.build_candidate_set(
        name,
        plugin_root=_paths().plugin_root,
        workspace_root=_paths().workspace_root,
    )
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        output = candidate_contracts.fixture_local_output_path(
            _paths().workspace_root,
            name,
            args.output,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0
```

Route `intent` and `candidates` in `main()`.

- [ ] **Step 4: Run CLI tests**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_cli_contract.py
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/bin/fig-agent plugins/figure-agent/tests/test_candidate_cli_contract.py
git commit -m "Expose candidate intent CLI"
```

## Phase 5: Review and Apply Boundary

### Task 7: Review Packet and Explicit Apply

**Files:**
- Create: `plugins/figure-agent/scripts/candidate_review_packet.py`
- Create: `plugins/figure-agent/scripts/candidate_apply.py`
- Test: `plugins/figure-agent/tests/test_candidate_review_packet.py`
- Test: `plugins/figure-agent/tests/test_candidate_apply.py`

- [ ] **Step 1: Write review/apply tests**

```python
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_apply  # noqa: E402


def test_apply_refuses_human_required_effective_authority(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    (fixture / "candidate_demo.tex").write_text("old\n", encoding="utf-8")
    manifest = {
        "candidate_id": "CAND001",
        "effective_apply_authority": "review_only",
        "operations": [
            {
                "kind": "replace_text",
                "path": "examples/candidate_demo/candidate_demo.tex",
                "original": "old",
                "replacement": "new",
            }
        ],
    }

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        apply=True,
    )

    assert result["applied"] is False
    assert result["error"]["code"] == "not_apply_eligible"
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == "old\n"
```

- [ ] **Step 2: Run test and verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_apply.py
```

Expected: `ModuleNotFoundError: No module named 'candidate_apply'`.

- [ ] **Step 3: Implement refusal-first apply**

Create `candidate_apply.py` with refusal behavior before any source mutation:

```python
"""Explicit candidate apply boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import runtime_paths


def apply_candidate(
    name: str,
    manifest: dict[str, Any],
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    if manifest.get("effective_apply_authority") != "apply_eligible":
        return {
            "schema": "figure-agent.candidate-apply-result.v1",
            "fixture": name,
            "candidate_id": manifest.get("candidate_id"),
            "applied": False,
            "error": {"code": "not_apply_eligible"},
        }
    if not apply:
        return {
            "schema": "figure-agent.candidate-apply-result.v1",
            "fixture": name,
            "candidate_id": manifest.get("candidate_id"),
            "applied": False,
            "dry_run": True,
        }
    return {
        "schema": "figure-agent.candidate-apply-result.v1",
        "fixture": name,
        "candidate_id": manifest.get("candidate_id"),
        "applied": False,
        "error": {"code": "apply_not_implemented_for_non_refusal_path"},
        "workspace_root": str(paths.workspace_root),
    }
```

- [ ] **Step 4: Run test and verify GREEN**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_apply.py
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/candidate_apply.py plugins/figure-agent/tests/test_candidate_apply.py
git commit -m "Guard candidate apply authority"
```

## Phase 6: MCP Facade

### Task 8: MCP Read-Only Candidate Tools

**Files:**
- Modify: `plugins/figure-agent/mcp/figure_agent_server.py`
- Test: `plugins/figure-agent/tests/test_mcp_facade.py`

- [ ] **Step 1: Add failing MCP tool-list test**

In `test_mcp_startup_and_list_tools_are_side_effect_free`, extend `tool_names`
expectation with:

```python
{
    "figure_agent_analyze_figure",
    "figure_agent_propose_improvements",
    "figure_agent_render_candidates",
    "figure_agent_rank_candidates",
    "figure_agent_prepare_human_review",
    "figure_agent_apply_candidate",
}
```

- [ ] **Step 2: Run MCP focused tests and verify RED**

Run:

```bash
PYTHONPATH=/opt/homebrew/lib/python3.14/site-packages:/Users/choemun-yeong/Library/Python/3.14/lib/python/site-packages uv run pytest -q plugins/figure-agent/tests/test_mcp_facade.py
```

Expected: failure showing the new tools missing.

- [ ] **Step 3: Implement read-only MCP wrappers**

Add tools that call public `fig-agent` commands:

- `figure_agent_analyze_figure` -> `fig-agent intent <name> --json`
- `figure_agent_propose_improvements` -> `fig-agent candidates <name> --json`
- `figure_agent_render_candidates` -> `fig-agent render-candidates ...`
- `figure_agent_rank_candidates` -> `fig-agent rank-candidates ...`
- `figure_agent_prepare_human_review` -> `fig-agent review-candidate ...`
- `figure_agent_apply_candidate` -> refusal-only wrapper returning `apply_requires_cli_opt_in`

Do not implement MCP mutation in this task. The MCP apply tool exists only so
callers receive a deterministic refusal instead of a missing-tool ambiguity.

- [ ] **Step 4: Run MCP tests**

Run:

```bash
PYTHONPATH=/opt/homebrew/lib/python3.14/site-packages:/Users/choemun-yeong/Library/Python/3.14/lib/python/site-packages uv run pytest -q plugins/figure-agent/tests/test_mcp_facade.py
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/tests/test_mcp_facade.py
git commit -m "Expose candidate workflow MCP tools"
```

## Phase 7: Release Gate, Docs, Dogfood

### Task 9: Release Gate and Schema Inventory

**Files:**
- Modify: `plugins/figure-agent/scripts/release_gate.py`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md`

- [ ] **Step 1: Add candidate tests to release gate targeted list**

Expected test list includes:

```python
"tests/test_figure_intent_model.py",
"tests/test_candidate_contracts.py",
"tests/test_candidate_generator.py",
"tests/test_candidate_render.py",
"tests/test_candidate_rank.py",
"tests/test_candidate_apply.py",
"tests/test_candidate_cli_contract.py",
```

- [ ] **Step 2: Update schema map**

Add schema rows:

- `figure-agent.intent-model.v1`
- `figure-agent.candidate-set.v1`
- `figure-agent.candidate-manifest.v1`
- `figure-agent.candidate-score.v1`
- `figure-agent.candidate-apply-result.v1`

- [ ] **Step 3: Run focused release gate**

Run:

```bash
cd plugins/figure-agent
python3 scripts/release_gate.py --output dist/cowork --json
```

Expected: success if existing environment dependencies are present. If the full
gate fails because of host dependency visibility, record exact stderr and run the
focused candidate tests with the documented `PYTHONPATH`.

- [ ] **Step 4: Commit**

```bash
git add plugins/figure-agent/scripts/release_gate.py plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md
git commit -m "Add candidate search release contracts"
```

### Task 10: Dogfood on a Synthetic Fixture

**Files:**
- Create: `plugins/figure-agent/docs/milestones/2026-06-08-candidate-search-dogfood.md`

- [ ] **Step 1: Create temp workspace fixture**

Run:

```bash
tmp=$(mktemp -d)
mkdir -p "$tmp/workspace/examples/candidate_demo"
printf 'name: candidate_demo\n' > "$tmp/workspace/examples/candidate_demo/spec.yaml"
printf '# Brief\n' > "$tmp/workspace/examples/candidate_demo/briefing.md"
printf '\\node (label-a) at (0,0) {Old Label};\n' > "$tmp/workspace/examples/candidate_demo/candidate_demo.tex"
```

- [ ] **Step 2: Run public workflow**

Run:

```bash
FIGURE_AGENT_PLUGIN_ROOT=$PWD/plugins/figure-agent FIGURE_AGENT_WORKSPACE=$tmp/workspace plugins/figure-agent/bin/fig-agent intent candidate_demo --json
FIGURE_AGENT_PLUGIN_ROOT=$PWD/plugins/figure-agent FIGURE_AGENT_WORKSPACE=$tmp/workspace plugins/figure-agent/bin/fig-agent candidates candidate_demo --json --output build/candidates/candidate_set.json
FIGURE_AGENT_PLUGIN_ROOT=$PWD/plugins/figure-agent FIGURE_AGENT_WORKSPACE=$tmp/workspace plugins/figure-agent/bin/fig-agent render-candidates candidate_demo --candidate-set build/candidates/candidate_set.json
FIGURE_AGENT_PLUGIN_ROOT=$PWD/plugins/figure-agent FIGURE_AGENT_WORKSPACE=$tmp/workspace plugins/figure-agent/bin/fig-agent rank-candidates candidate_demo --candidate-set build/candidates/candidate_set.json --json
```

Expected:

- intent emits `figure-agent.intent-model.v1`;
- candidates emits `figure-agent.candidate-set.v1`;
- render writes only under `examples/candidate_demo/build/candidates/`;
- ranking emits `effective_apply_authority`.

- [ ] **Step 3: Write milestone evidence**

Create `plugins/figure-agent/docs/milestones/2026-06-08-candidate-search-dogfood.md` summarizing command outputs, pass/fail state, and any host dependency caveats.

- [ ] **Step 4: Commit**

```bash
git add plugins/figure-agent/docs/milestones/2026-06-08-candidate-search-dogfood.md
git commit -m "Record candidate search dogfood"
```

## Final Verification

Run:

```bash
PYTHONPATH=/opt/homebrew/lib/python3.14/site-packages:/Users/choemun-yeong/Library/Python/3.14/lib/python/site-packages uv run pytest -q \
  plugins/figure-agent/tests/test_figure_intent_model.py \
  plugins/figure-agent/tests/test_candidate_contracts.py \
  plugins/figure-agent/tests/test_candidate_generator.py \
  plugins/figure-agent/tests/test_candidate_render.py \
  plugins/figure-agent/tests/test_candidate_rank.py \
  plugins/figure-agent/tests/test_candidate_apply.py \
  plugins/figure-agent/tests/test_candidate_cli_contract.py \
  plugins/figure-agent/tests/test_mcp_facade.py
uv run ruff check \
  plugins/figure-agent/scripts/figure_intent_model.py \
  plugins/figure-agent/scripts/candidate_contracts.py \
  plugins/figure-agent/scripts/candidate_generator.py \
  plugins/figure-agent/scripts/candidate_render.py \
  plugins/figure-agent/scripts/candidate_rank.py \
  plugins/figure-agent/scripts/candidate_apply.py \
  plugins/figure-agent/tests/test_figure_intent_model.py \
  plugins/figure-agent/tests/test_candidate_contracts.py \
  plugins/figure-agent/tests/test_candidate_generator.py \
  plugins/figure-agent/tests/test_candidate_render.py \
  plugins/figure-agent/tests/test_candidate_rank.py \
  plugins/figure-agent/tests/test_candidate_apply.py \
  plugins/figure-agent/tests/test_candidate_cli_contract.py
git diff --check
```

Before claiming the full feature complete, also run:

```bash
cd plugins/figure-agent
python3 scripts/release_gate.py --output dist/cowork --json
```

## Self-Review Checklist

- Spec coverage:
  - Intent model: Task 1.
  - Fixture-local input boundary: Task 1 tests.
  - Candidate schema completeness: Tasks 2 and 3.
  - Render sandbox and manifest provenance: Task 4.
  - `human_required` downgrade and effective authority: Task 5.
  - CLI public surface: Task 6.
  - Explicit apply boundary: Task 7.
  - MCP facade: Task 8.
  - Release/dogfood: Tasks 9 and 10.
- Placeholder scan:
  - No `TODO`, `TBD`, or "implement later" instructions are allowed in the plan.
- Type consistency:
  - Use `apply_authority` only as pre-render ceiling.
  - Use `effective_apply_authority` as the only post-render apply authority.
  - Use hard-gate states exactly: `pass`, `human_required`, `rejected`.
