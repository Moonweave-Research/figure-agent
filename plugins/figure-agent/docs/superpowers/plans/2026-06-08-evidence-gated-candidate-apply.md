# Evidence-Gated Candidate Apply Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an explicit human-accepted candidate apply path that verifies rendered evidence, mutates only fixture source files, records rollback metadata, and keeps MCP non-mutating.

**Architecture:** Add a focused `candidate_acceptance.py` module for acceptance/readiness artifacts, extend `candidate_apply.py` into the gated mutation engine, and wire CLI/MCP/review packet surfaces to the same readiness evaluator. Tests drive every gate before implementation, with source mutation limited to temporary fixtures and real dogfood left as a manually accepted final step. Post-apply compile/export/status is allowed to write the normal fixture `build/` and `exports/` artifacts; candidate sandbox writes remain limited to acceptance, rollback, and apply-result metadata.

**Tech Stack:** Python stdlib, existing `runtime_paths.py`, `fixture_identity.py`, `candidate_contracts.py`, `fig-agent` CLI wrapper, MCP facade JSON-RPC tests, pytest, ruff.

---

## Review-Closed Requirements

The implementation must close these reviewed holes:

- Read render gates from `render_manifest["stages"][stage]["status"]`, not top-level stage keys.
- Treat pre-acceptance `effective_apply_authority: review_only` as expected. The explicit acceptance artifact is the one-time apply permission.
- Block readiness/apply when an operation target lacks a drift hash. Accept either `operation.source_sha256` or exactly one matching `tex_selector.v1.source_hash`.
- Refuse a second apply when `apply_result.json` already records `applied` or `applied_with_failed_verification`.
- Acquire shared `build/.mcp-locks/mutation.lock` and refuse when that lock or `build/.quality-locks/mutation.lock` exists.
- Generate `rollback.patch` before mutation as a fixture-relative unified diff from candidate-applied text back to original text.
- Define MCP readiness schema with required `name`, `candidate_id`, and `candidate_set`.
- Rewrite old refusal-only candidate apply tests instead of preserving `apply_not_implemented_for_non_refusal_path`.

### Task 1: Acceptance Artifact And Readiness Evaluator

**Files:**
- Create: `plugins/figure-agent/scripts/candidate_acceptance.py`
- Test: `plugins/figure-agent/tests/test_candidate_acceptance.py`

- [ ] **Step 1: Write failing tests for acceptance creation and readiness**

Add `plugins/figure-agent/tests/test_candidate_acceptance.py`:

```python
from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_acceptance  # noqa: E402


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text("source\n", encoding="utf-8")
    candidate_manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "fixture": name,
        "candidate_id": "CAND001",
        "candidate_hash": "sha256:" + "1" * 64,
        "candidate_set_path": "build/candidates/candidate_set.json",
        "effective_apply_authority": "review_only",
        "verification": {"hard_gate_state": "human_required"},
        "operations": [
            {
                "kind": "replace_text",
                "path": f"examples/{name}/{name}.tex",
                "source_sha256": _sha256_text("source\n"),
                "original": "source",
                "replacement": "candidate",
            }
        ],
        "selectors": [
            {
                "kind": "tex_selector.v1",
                "path": f"examples/{name}/{name}.tex",
                "source_hash": _sha256_text("source\n"),
            }
        ],
    }
    render_manifest = {
        "schema": "figure-agent.candidate-render-manifest.v1",
        "figure_name": name,
        "candidate_id": "CAND001",
        "candidate_hash": "sha256:" + "1" * 64,
        "candidate_set_path": "build/candidates/candidate_set.json",
        "stages": {
            "compile": {"status": "success"},
            "export": {"status": "success"},
            "crop": {"status": "success"},
            "evaluate": {"status": "rendered_needs_human_review"},
        },
    }
    candidate_set = {
        "schema": "figure-agent.candidate-set.v1",
        "candidates": [{"id": "CAND001", "candidate_hash": "sha256:" + "1" * 64}],
    }
    (fixture / "build" / "candidates" / "candidate_set.json").write_text(
        json.dumps(candidate_set, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "candidate_manifest.json").write_text(
        json.dumps(candidate_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "render_manifest.json").write_text(
        json.dumps(render_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return fixture


def test_build_apply_readiness_reports_ready_for_local_acceptance(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    readiness = candidate_acceptance.build_apply_readiness(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    assert readiness["schema"] == "figure-agent.candidate-apply-readiness.v1"
    assert readiness["status"] == "ready_for_local_acceptance"
    assert readiness["blocking_reasons"] == []
    assert readiness["required_commands"][0].startswith("fig-agent accept-candidate")


def test_write_acceptance_artifact_records_manifest_hashes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)

    payload = candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )

    path = fixture / "build" / "candidates" / "CAND001" / "acceptance.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert payload["path"] == "build/candidates/CAND001/acceptance.json"
    assert data["schema"] == "figure-agent.candidate-acceptance.v1"
    assert data["decision"] == "accept"
    assert data["reviewer"] == "local-user"
    assert data["candidate_manifest_sha256"].startswith("sha256:")
    assert data["render_manifest_sha256"].startswith("sha256:")


def test_acceptance_rejects_sandbox_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    acceptance = fixture / "build" / "candidates" / "CAND001" / "acceptance.json"
    acceptance.symlink_to(outside)

    with pytest.raises(candidate_acceptance.CandidateAcceptanceError, match="sandbox_symlink"):
        candidate_acceptance.write_acceptance(
            "candidate_demo",
            "CAND001",
            candidate_set_path=Path("build/candidates/candidate_set.json"),
            decision="accept",
            reviewer="local-user",
            rationale="Rendered evidence reviewed.",
            workspace_root=workspace,
        )


def test_readiness_blocks_missing_source_drift_hash(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["operations"][0].pop("source_sha256")
    manifest["selectors"] = []
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")

    readiness = candidate_acceptance.build_apply_readiness(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        workspace_root=workspace,
    )

    assert readiness["status"] == "blocked"
    assert "source_drift_hash_missing:candidate_demo.tex" in readiness["blocking_reasons"]
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_acceptance.py
```

Expected: FAIL with `ModuleNotFoundError: No module named 'candidate_acceptance'`.

- [ ] **Step 3: Implement `candidate_acceptance.py`**

Create `plugins/figure-agent/scripts/candidate_acceptance.py` with:

```python
"""Acceptance and readiness gates for rendered candidates."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths

READINESS_SCHEMA = "figure-agent.candidate-apply-readiness.v1"
ACCEPTANCE_SCHEMA = "figure-agent.candidate-acceptance.v1"


class CandidateAcceptanceError(ValueError):
    """Raised when acceptance/readiness would escape the candidate sandbox."""


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _candidate_id(value: str) -> str:
    fixture_identity.validate_fixture_name(value)
    return value


def _candidate_sandbox(example_dir: Path, candidate_id: str) -> Path:
    build_dir = example_dir / "build"
    root = build_dir / "candidates"
    sandbox = root / candidate_id
    for label, path in (("build", build_dir), ("candidates", root), (candidate_id, sandbox)):
        if path.is_symlink():
            raise CandidateAcceptanceError(f"sandbox_symlink_forbidden: {label}")
    try:
        sandbox.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise CandidateAcceptanceError("candidate path_escape") from exc
    return sandbox


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise CandidateAcceptanceError(f"sandbox_symlink_forbidden: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateAcceptanceError(f"{label}_unreadable") from exc
    if not isinstance(payload, dict):
        raise CandidateAcceptanceError(f"{label}_invalid")
    return payload


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError as exc:
        raise CandidateAcceptanceError("path_escape") from exc


def _candidate_set_candidate(candidate_set: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
    candidates = candidate_set.get("candidates")
    if not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("id") == candidate_id:
            return candidate
    return None


def _render_gates(render_manifest: dict[str, Any]) -> list[str]:
    stages = render_manifest.get("stages") if isinstance(render_manifest.get("stages"), dict) else {}
    required = {
        "compile": "success",
        "export": "success",
        "crop": "success",
        "evaluate": "rendered_needs_human_review",
    }
    failures: list[str] = []
    for stage, expected in required.items():
        value = stages.get(stage)
        status = value.get("status") if isinstance(value, dict) else None
        if status != expected:
            failures.append(f"{stage}:{status or 'missing'}")
    return failures


def _operation_path(example_dir: Path, fixture_name: str, operation: dict[str, Any]) -> Path:
    value = operation.get("path")
    if not isinstance(value, str) or not value.strip():
        raise CandidateAcceptanceError("operation_path_missing")
    path = Path(value)
    if path.parts[:2] == ("examples", fixture_name):
        path = Path(*path.parts[2:])
    target = example_dir / path
    if target.is_symlink():
        raise CandidateAcceptanceError("source_symlink_forbidden")
    try:
        target.resolve().relative_to(example_dir.resolve())
    except ValueError as exc:
        raise CandidateAcceptanceError("source_path_escape") from exc
    return target


def _drift_hash_for_operation(operation: dict[str, Any], selectors: Any) -> str | None:
    direct = operation.get("source_sha256")
    if isinstance(direct, str) and direct.startswith("sha256:"):
        return direct
    path = operation.get("path")
    matches = [
        selector
        for selector in selectors
        if isinstance(selector, dict)
        and selector.get("kind") == "tex_selector.v1"
        and selector.get("path") == path
        and isinstance(selector.get("source_hash"), str)
    ] if isinstance(selectors, list) else []
    if len(matches) == 1:
        return str(matches[0]["source_hash"])
    return None


def _load_gate_inputs(
    name: str,
    candidate_id: str,
    *,
    candidate_set_path: Path,
    workspace_root: Path | None,
    plugin_root: Path | None,
) -> tuple[runtime_paths.RuntimePaths, Path, Path, dict[str, Any], Path, dict[str, Any], Path, dict[str, Any]]:
    fixture_identity.validate_fixture_name(name)
    safe_candidate_id = _candidate_id(candidate_id)
    paths = runtime_paths.resolve_runtime_paths(plugin_root=plugin_root, workspace_root=workspace_root)
    example_dir = paths.examples_dir / name
    sandbox = _candidate_sandbox(example_dir, safe_candidate_id)
    candidate_set_file = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        candidate_set_path.as_posix(),
    )
    candidate_set = _load_json(candidate_set_file, "candidate_set")
    manifest_path = sandbox / "candidate_manifest.json"
    render_manifest_path = sandbox / "render_manifest.json"
    manifest = _load_json(manifest_path, "candidate_manifest")
    render_manifest = _load_json(render_manifest_path, "render_manifest")
    return (
        paths,
        candidate_set_file,
        candidate_set,
        manifest_path,
        manifest,
        render_manifest_path,
        render_manifest,
        example_dir,
    )


def build_apply_readiness(
    name: str,
    candidate_id: str,
    *,
    candidate_set_path: Path,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    (
        _paths,
        candidate_set_file,
        candidate_set,
        _manifest_path,
        manifest,
        _render_manifest_path,
        render_manifest,
        example_dir,
    ) = _load_gate_inputs(
        name,
        candidate_id,
        candidate_set_path=candidate_set_path,
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    safe_candidate_id = _candidate_id(candidate_id)
    blocking: list[str] = []
    candidate = _candidate_set_candidate(candidate_set, safe_candidate_id)
    if candidate is None:
        blocking.append("candidate_set_missing_candidate")
    elif candidate.get("candidate_hash") != manifest.get("candidate_hash"):
        blocking.append("candidate_hash_mismatch")
    if manifest.get("candidate_hash") != render_manifest.get("candidate_hash"):
        blocking.append("render_candidate_hash_mismatch")
    effective = manifest.get("effective_apply_authority")
    if effective != "review_only":
        blocking.append(f"effective_apply_authority:{effective}")
    blocking.extend(_render_gates(render_manifest))
    operations = manifest.get("operations")
    if not isinstance(operations, list):
        blocking.append("operations_missing")
    else:
        for operation in operations:
            if not isinstance(operation, dict):
                blocking.append("operation_invalid")
                continue
            target = _operation_path(example_dir, name, operation)
            drift_hash = _drift_hash_for_operation(operation, manifest.get("selectors"))
            if drift_hash is None:
                blocking.append(f"source_drift_hash_missing:{target.relative_to(example_dir).as_posix()}")
            elif _sha256_file(target) != drift_hash:
                blocking.append(f"source_drift_hash_mismatch:{target.relative_to(example_dir).as_posix()}")
    apply_result_path = example_dir / "build" / "candidates" / safe_candidate_id / "apply_result.json"
    if apply_result_path.is_file():
        apply_result = _load_json(apply_result_path, "apply_result")
        if apply_result.get("status") in {"applied", "applied_with_failed_verification"}:
            blocking.append("already_applied")
    status = "ready_for_local_acceptance" if not blocking else "blocked"
    return {
        "schema": READINESS_SCHEMA,
        "figure_name": name,
        "candidate_id": safe_candidate_id,
        "candidate_set_path": _fixture_relative(example_dir, candidate_set_file),
        "status": status,
        "blocking_reasons": blocking,
        "required_commands": []
        if blocking
        else [
            (
                f"fig-agent accept-candidate {name} {safe_candidate_id} "
                f"--candidate-set {_fixture_relative(example_dir, candidate_set_file)} "
                "--decision accept --reviewer <name> --rationale <text> --json"
            ),
            (
                f"fig-agent apply-candidate {name} {safe_candidate_id} "
                f"--candidate-set {_fixture_relative(example_dir, candidate_set_file)} "
                f"--acceptance build/candidates/{safe_candidate_id}/acceptance.json --json"
            ),
        ],
    }


def write_acceptance(
    name: str,
    candidate_id: str,
    *,
    candidate_set_path: Path,
    decision: str,
    reviewer: str,
    rationale: str,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    if decision != "accept":
        raise CandidateAcceptanceError("decision must be accept")
    if not reviewer.strip() or not rationale.strip():
        raise CandidateAcceptanceError("reviewer and rationale are required")
    (
        _paths,
        candidate_set_file,
        _candidate_set,
        manifest_path,
        manifest,
        render_manifest_path,
        _render_manifest,
        example_dir,
    ) = _load_gate_inputs(
        name,
        candidate_id,
        candidate_set_path=candidate_set_path,
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    readiness = build_apply_readiness(
        name,
        candidate_id,
        candidate_set_path=candidate_set_path,
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    if readiness["status"] != "ready_for_local_acceptance":
        raise CandidateAcceptanceError("candidate is not ready for local acceptance")
    acceptance_path = manifest_path.parent / "acceptance.json"
    if acceptance_path.is_symlink():
        raise CandidateAcceptanceError("sandbox_symlink_forbidden: acceptance.json")
    payload = {
        "schema": ACCEPTANCE_SCHEMA,
        "figure_name": name,
        "candidate_id": candidate_id,
        "candidate_hash": manifest.get("candidate_hash"),
        "candidate_set_path": _fixture_relative(example_dir, candidate_set_file),
        "candidate_manifest_path": _fixture_relative(example_dir, manifest_path),
        "candidate_manifest_sha256": _sha256_file(manifest_path),
        "render_manifest_path": _fixture_relative(example_dir, render_manifest_path),
        "render_manifest_sha256": _sha256_file(render_manifest_path),
        "decision": decision,
        "reviewer": reviewer,
        "reviewed_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "rationale": rationale,
        "human_review_required": True,
    }
    acceptance_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "schema": "figure-agent.candidate-acceptance-write-result.v1",
        "figure_name": name,
        "candidate_id": candidate_id,
        "path": _fixture_relative(example_dir, acceptance_path),
    }
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_acceptance.py
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/candidate_acceptance.py plugins/figure-agent/tests/test_candidate_acceptance.py
git commit -m "Add candidate acceptance readiness"
```

### Task 2: CLI Readiness And Acceptance Commands

**Files:**
- Modify: `plugins/figure-agent/bin/fig-agent`
- Test: `plugins/figure-agent/tests/test_candidate_cli_contract.py`

- [ ] **Step 1: Write failing CLI contract test**

Append to `plugins/figure-agent/tests/test_candidate_cli_contract.py`:

```python
def test_fig_agent_acceptance_readiness_and_acceptance_cli(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidates = _run(
        workspace,
        "candidates",
        "candidate_demo",
        "--json",
        "--output",
        "build/candidates/candidate_set.json",
    )
    render = _run(
        workspace,
        "render-candidates",
        "candidate_demo",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--candidate-id",
        "CAND001",
        "--compile",
        "--export",
        "--evaluate",
        "--json",
    )
    ready = _run(
        workspace,
        "apply-candidate-ready",
        "candidate_demo",
        "CAND001",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--json",
    )
    accept = _run(
        workspace,
        "accept-candidate",
        "candidate_demo",
        "CAND001",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--decision",
        "accept",
        "--reviewer",
        "local-user",
        "--rationale",
        "Rendered evidence reviewed.",
        "--json",
    )

    assert candidates.returncode == 0, candidates.stderr
    assert render.returncode == 0, render.stderr
    assert ready.returncode == 0, ready.stderr
    assert accept.returncode == 0, accept.stderr
    assert json.loads(ready.stdout)["status"] == "ready_for_local_acceptance"
    assert json.loads(accept.stdout)["path"] == "build/candidates/CAND001/acceptance.json"
    assert (fixture / "build" / "candidates" / "CAND001" / "acceptance.json").is_file()
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_cli_contract.py::test_fig_agent_acceptance_readiness_and_acceptance_cli
```

Expected: FAIL because `apply-candidate-ready` and `accept-candidate` are unknown commands.

- [ ] **Step 3: Implement CLI commands**

In `plugins/figure-agent/bin/fig-agent`, import `candidate_acceptance` inside new handlers:

```python
def _apply_candidate_ready(argv: list[str]) -> int:
    import candidate_acceptance

    parser = argparse.ArgumentParser(prog="fig-agent apply-candidate-ready")
    parser.add_argument("name")
    parser.add_argument("candidate_id")
    parser.add_argument("--candidate-set", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validated_fixture_name(parser, args.name)
    try:
        payload = candidate_acceptance.build_apply_readiness(
            name,
            args.candidate_id,
            candidate_set_path=Path(args.candidate_set),
            plugin_root=_paths().plugin_root,
            workspace_root=_paths().workspace_root,
        )
    except (ValueError, candidate_acceptance.CandidateAcceptanceError) as exc:
        print(f"fig-agent apply-candidate-ready: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _accept_candidate(argv: list[str]) -> int:
    import candidate_acceptance

    parser = argparse.ArgumentParser(prog="fig-agent accept-candidate")
    parser.add_argument("name")
    parser.add_argument("candidate_id")
    parser.add_argument("--candidate-set", required=True)
    parser.add_argument("--decision", choices=("accept",), required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--rationale", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validated_fixture_name(parser, args.name)
    try:
        payload = candidate_acceptance.write_acceptance(
            name,
            args.candidate_id,
            candidate_set_path=Path(args.candidate_set),
            decision=args.decision,
            reviewer=args.reviewer,
            rationale=args.rationale,
            plugin_root=_paths().plugin_root,
            workspace_root=_paths().workspace_root,
        )
    except (ValueError, candidate_acceptance.CandidateAcceptanceError) as exc:
        print(f"fig-agent accept-candidate: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
```

Add dispatch:

```python
if command == "apply-candidate-ready":
    return _apply_candidate_ready(rest)
if command == "accept-candidate":
    return _accept_candidate(rest)
```

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_cli_contract.py::test_fig_agent_acceptance_readiness_and_acceptance_cli
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/bin/fig-agent plugins/figure-agent/tests/test_candidate_cli_contract.py
git commit -m "Expose candidate acceptance CLI"
```

### Task 3: Gated Source Apply Engine

**Files:**
- Modify: `plugins/figure-agent/scripts/candidate_apply.py`
- Test: `plugins/figure-agent/tests/test_candidate_apply.py`

- [ ] **Step 1: Write failing apply engine tests**

Append to `plugins/figure-agent/tests/test_candidate_apply.py`:

```python
from hashlib import sha256

import candidate_acceptance


def test_apply_candidate_requires_acceptance_artifact(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    manifest = _rendered_candidate_fixture(workspace)

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "acceptance_missing"


def test_apply_candidate_exact_replace_writes_source_and_result(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
    )

    assert result["status"] in {"applied", "applied_with_failed_verification"}
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == "candidate\n"
    assert result["changed_files"][0]["path"] == "candidate_demo.tex"
    assert (fixture / "build" / "candidates" / "CAND001" / "rollback.patch").is_file()
    assert (fixture / "build" / "candidates" / "CAND001" / "apply_result.json").is_file()
```

Define helper fixtures in the same test file:

```python
def _rendered_candidate_fixture(workspace: Path) -> dict:
    fixture = workspace / "examples" / "candidate_demo"
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (fixture / "candidate_demo.tex").write_text("source\n", encoding="utf-8")
    candidate_set = {
        "schema": "figure-agent.candidate-set.v1",
        "candidates": [{"id": "CAND001", "candidate_hash": "sha256:" + "1" * 64}],
    }
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "fixture": "candidate_demo",
        "candidate_id": "CAND001",
        "candidate_hash": "sha256:" + "1" * 64,
        "candidate_set_path": "build/candidates/candidate_set.json",
        "effective_apply_authority": "review_only",
        "verification": {"hard_gate_state": "human_required"},
        "operations": [
            {
                "kind": "replace_text",
                "path": "examples/candidate_demo/candidate_demo.tex",
                "source_sha256": "sha256:" + sha256("source\n".encode("utf-8")).hexdigest(),
                "original": "source\n",
                "replacement": "candidate\n",
            }
        ],
        "selectors": [
            {
                "kind": "tex_selector.v1",
                "path": "examples/candidate_demo/candidate_demo.tex",
                "source_hash": "sha256:" + sha256("source\n".encode("utf-8")).hexdigest(),
            }
        ],
    }
    render_manifest = {
        "schema": "figure-agent.candidate-render-manifest.v1",
        "figure_name": "candidate_demo",
        "candidate_id": "CAND001",
        "candidate_hash": "sha256:" + "1" * 64,
        "candidate_set_path": "build/candidates/candidate_set.json",
        "stages": {
            "compile": {"status": "success"},
            "export": {"status": "success"},
            "crop": {"status": "success"},
            "evaluate": {"status": "rendered_needs_human_review"},
        },
    }
    (fixture / "build" / "candidates" / "candidate_set.json").write_text(
        json.dumps(candidate_set, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "candidate_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "render_manifest.json").write_text(
        json.dumps(render_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _accepted_candidate_fixture(workspace: Path) -> tuple[Path, dict]:
    manifest = _rendered_candidate_fixture(workspace)
    fixture = workspace / "examples" / "candidate_demo"
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )
    return fixture, manifest


def test_apply_candidate_refuses_already_applied_result(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    apply_result = fixture / "build" / "candidates" / "CAND001" / "apply_result.json"
    apply_result.write_text(
        json.dumps({"schema": "figure-agent.candidate-apply-result.v1", "status": "applied"})
        + "\n",
        encoding="utf-8",
    )

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "already_applied"


def test_apply_candidate_refuses_existing_mcp_or_quality_lock(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    lock = fixture / "build" / ".mcp-locks" / "mutation.lock"
    lock.parent.mkdir()
    lock.write_text("{}", encoding="utf-8")

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "mutation_lock_active"
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_apply.py
```

Expected: FAIL because `candidate_apply.apply_candidate()` does not accept `candidate_set_path` or `acceptance_path`.

- [ ] **Step 3: Implement minimal gated apply**

Modify `plugins/figure-agent/scripts/candidate_apply.py`:

- Add `candidate_set_path: Path | None = None` and `acceptance_path: Path | None = None` keyword arguments.
- Load candidate set, candidate manifest, render manifest, and acceptance.
- Read render gates from `render_manifest["stages"][stage]["status"]`.
- Return `status: blocked` with fixture-relative diagnostics when any gate fails.
- Treat `effective_apply_authority: review_only` as expected before acceptance.
- Require per-operation drift hash through `operation.source_sha256` or a matching
  `tex_selector.v1.source_hash`.
- Refuse if `apply_result.json` already records `applied` or
  `applied_with_failed_verification`.
- Refuse if `.mcp-locks/mutation.lock` or `.quality-locks/mutation.lock` exists.
- Acquire `.mcp-locks/mutation.lock` before writing rollback/source/apply result.
- Before source mutation, write `rollback.patch` with unified diff content using `difflib.unified_diff`.
- Apply exact `replace_text` operations only when `original` appears exactly once.
- Write `apply_result.json` under `build/candidates/<candidate_id>/`.

Use this implementation shape:

```python
def apply_candidate(..., candidate_set_path: Path | None = None, acceptance_path: Path | None = None, apply: bool = False) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(plugin_root=plugin_root, workspace_root=workspace_root)
    example_dir = paths.examples_dir / name
    candidate_id = str(manifest.get("candidate_id"))
    fixture_identity.validate_fixture_name(candidate_id)
    sandbox = example_dir / "build" / "candidates" / candidate_id
    # reject build/candidates/sandbox symlinks
    # load and verify render_manifest + acceptance
    # verify render_manifest["stages"][stage]["status"]
    # verify acceptance manifest hashes
    # verify source drift hash and exact original count
    # verify no existing applied apply_result
    # verify no MCP/quality lock, then acquire candidate apply lock
    # if not apply, return dry_run readiness result
    # write rollback.patch from candidate-applied text back to original text
    # apply exact replace_text operations
    # write rollback.patch and apply_result.json
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_apply.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/candidate_apply.py plugins/figure-agent/tests/test_candidate_apply.py
git commit -m "Add gated candidate source apply"
```

### Task 4: Apply CLI, Review Packet Readiness, MCP Readiness

**Files:**
- Modify: `plugins/figure-agent/bin/fig-agent`
- Modify: `plugins/figure-agent/scripts/candidate_review_packet.py`
- Modify: `plugins/figure-agent/mcp/figure_agent_server.py`
- Test: `plugins/figure-agent/tests/test_candidate_cli_contract.py`
- Test: `plugins/figure-agent/tests/test_candidate_review_packet.py`
- Test: `plugins/figure-agent/tests/test_mcp_facade.py`

- [ ] **Step 1: Write failing CLI/MCP/review tests**

Add tests that assert:

```python
assert review_packet["apply_readiness"]["status"] in {
    "ready_for_local_acceptance",
    "accepted_ready_to_apply",
    "applied",
    "blocked",
}
```

Add MCP schema test:

```python
assert "figure_agent_candidate_apply_readiness" in tool_names
```

Add CLI apply test:

```python
apply = _run(
    workspace,
    "apply-candidate",
    "candidate_demo",
    "CAND001",
    "--candidate-set",
    "build/candidates/candidate_set.json",
    "--acceptance",
    "build/candidates/CAND001/acceptance.json",
    "--json",
)
assert apply.returncode == 0, apply.stderr
assert json.loads(apply.stdout)["schema"] == "figure-agent.candidate-apply-result.v1"
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_cli_contract.py plugins/figure-agent/tests/test_candidate_review_packet.py plugins/figure-agent/tests/test_mcp_facade.py
```

Expected: FAIL for missing apply CLI/readiness fields/MCP tool.

- [ ] **Step 3: Implement surfaces**

In `bin/fig-agent`:

- Replace the current `_apply_candidate` refusal-only handler with explicit CLI apply.
- Keep MCP refusal separate in `figure_agent_server.py`.

In `candidate_review_packet.py`:

- Import `candidate_acceptance`.
- Add `apply_readiness` from `build_apply_readiness()` when candidate set path exists.
- If acceptance exists, set `accepted_ready_to_apply`.
- If apply result exists, set `applied` or the apply result status.

In `figure_agent_server.py`:

- Add `figure_agent_candidate_apply_readiness` schema and handler.
- Keep `figure_agent_apply_candidate` returning `apply_requires_cli_opt_in`.
- Extend compare result pass-through only; do not write acceptance.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_cli_contract.py plugins/figure-agent/tests/test_candidate_review_packet.py plugins/figure-agent/tests/test_mcp_facade.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/bin/fig-agent plugins/figure-agent/scripts/candidate_review_packet.py plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/tests/test_candidate_cli_contract.py plugins/figure-agent/tests/test_candidate_review_packet.py plugins/figure-agent/tests/test_mcp_facade.py
git commit -m "Expose evidence gated apply surfaces"
```

### Task 5: Verification, Dogfood, Final Review

**Files:**
- No new production files expected.
- Use existing tests and local dogfood fixture.

- [ ] **Step 1: Run focused test suite**

Run:

```bash
uv run ruff check plugins/figure-agent/scripts/candidate_acceptance.py plugins/figure-agent/scripts/candidate_apply.py plugins/figure-agent/scripts/candidate_review_packet.py plugins/figure-agent/bin/fig-agent plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/tests/test_candidate_acceptance.py plugins/figure-agent/tests/test_candidate_apply.py plugins/figure-agent/tests/test_candidate_cli_contract.py plugins/figure-agent/tests/test_candidate_review_packet.py plugins/figure-agent/tests/test_mcp_facade.py
uv run pytest -q plugins/figure-agent/tests/test_candidate_acceptance.py plugins/figure-agent/tests/test_candidate_apply.py plugins/figure-agent/tests/test_candidate_cli_contract.py plugins/figure-agent/tests/test_candidate_review_packet.py plugins/figure-agent/tests/test_mcp_facade.py
```

Expected: ruff passes and pytest passes.

- [ ] **Step 2: Run local-only dogfood readiness**

Run:

```bash
FIGURE_AGENT_PLUGIN_ROOT="$PWD/plugins/figure-agent" \
FIGURE_AGENT_WORKSPACE="$PWD/plugins/figure-agent" \
"$PWD/plugins/figure-agent/bin/fig-agent" apply-candidate-ready \
fig1_overview_v2_pair_001_vault CAND001 \
--candidate-set build/candidates/panel_C_candidate_set.json \
--json
```

Expected: `status` is `ready_for_local_acceptance` or a precise `blocked`
diagnostic. Do not run `apply-candidate` on the real fixture unless the user
explicitly approves applying the candidate source change.

- [ ] **Step 3: Request final review**

Dispatch a read-only reviewer with:

```text
Review the evidence-gated candidate apply diff. Findings first. Focus on source mutation safety, acceptance hash gates, rollback patch creation before mutation, MCP non-mutating boundary, path sandboxing, and test gaps.
```

- [ ] **Step 4: Fix review findings**

For every reviewer finding:

- Add or update a failing test that reproduces it.
- Implement the smallest fix.
- Run the focused tests.

- [ ] **Step 5: Commit final fixes**

```bash
git add <changed files>
git commit -m "Harden evidence gated candidate apply"
```

- [ ] **Step 6: Report final status**

Report:

- commit hashes
- verification commands and pass/fail
- whether real fixture source was left unchanged
- remaining dirty files excluded from this workflow
