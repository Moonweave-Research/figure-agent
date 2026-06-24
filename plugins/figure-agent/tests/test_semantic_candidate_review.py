from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import semantic_candidate_review  # noqa: E402


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _fixture(
    workspace: Path,
    *,
    edit_family: str = "bounded_coordinate_offset",
    semantic_risks: list[str] | None = None,
) -> tuple[Path, Path, Path, dict]:
    name = "semantic_demo"
    fixture = workspace / "examples" / name
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text("source\n", encoding="utf-8")
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "fixture": name,
        "candidate_id": "CAND001",
        "candidate_hash": "sha256:" + "3" * 64,
        "panel": "C",
        "edit_family": edit_family,
        "semantic_risks": semantic_risks or [],
        "operations": [
            {
                "kind": "coordinate_offset",
                "path": f"examples/{name}/{name}.tex",
            }
        ],
        "verification": {"hard_gate_state": "pass"},
        "apply_authority": "apply_eligible",
        "effective_apply_authority": "review_only",
    }
    manifest_path = sandbox / "candidate_manifest.json"
    render_path = sandbox / "render_manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    render_path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.candidate-render-manifest.v1",
                "figure_name": name,
                "candidate_id": "CAND001",
                "candidate_hash": manifest["candidate_hash"],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return fixture, manifest_path, render_path, manifest


def _write_review(
    fixture: Path,
    render_path: Path,
    manifest: dict,
    *,
    candidate_id: str = "CAND001",
    artifact_hash: str | None = None,
    verdict: str = "pass",
    human_required: bool = False,
    extra: dict | None = None,
) -> Path:
    payload = {
        "schema": "figure-agent.semantic-candidate-review.v1",
        "fixture": fixture.name,
        "candidate_id": candidate_id,
        "candidate_hash": manifest["candidate_hash"],
        "reviewed_artifacts": [
            {
                "path": render_path.relative_to(fixture).as_posix(),
                "sha256": artifact_hash or _sha256_file(render_path),
            }
        ],
        "semantic_invariants": [],
        "findings": [],
        "conflicts": [],
        "verdict": verdict,
        "human_required": human_required,
        "reviewed_at": "2026-06-22T00:00:00Z",
        "reviewer": "host",
    }
    if extra:
        payload.update(extra)
    review_path = render_path.parent / "semantic_review.json"
    review_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return review_path


def _state(fixture: Path, manifest_path: Path, manifest: dict) -> dict:
    return semantic_candidate_review.build_semantic_review_state(
        fixture,
        manifest_path,
        manifest,
        spec={},
    )


def test_valid_review_passes_when_candidate_and_artifact_hashes_match(tmp_path: Path) -> None:
    fixture, manifest_path, render_path, manifest = _fixture(tmp_path / "workspace")
    _write_review(fixture, render_path, manifest)

    state = _state(fixture, manifest_path, manifest)

    assert state["status"] == "pass"
    assert state["verdict"] == "pass"
    assert state["blocks_apply"] is False
    assert state["human_required"] is False


def test_optional_semantic_risk_verdict_blocks_apply(tmp_path: Path) -> None:
    fixture, manifest_path, render_path, manifest = _fixture(tmp_path / "workspace")
    _write_review(
        fixture,
        render_path,
        manifest,
        verdict="semantic_risk",
        human_required=True,
    )

    state = _state(fixture, manifest_path, manifest)

    assert state["required_before_apply"] is False
    assert state["status"] == "semantic_risk"
    assert state["human_required"] is True
    assert state["blocks_apply"] is True
    assert "semantic_risk" in state["blocking_reasons"]


def test_stale_reviewed_artifact_hash_produces_invalid_or_stale(tmp_path: Path) -> None:
    fixture, manifest_path, render_path, manifest = _fixture(tmp_path / "workspace")
    _write_review(fixture, render_path, manifest)
    render_path.write_text('{"changed": true}\n', encoding="utf-8")

    state = _state(fixture, manifest_path, manifest)

    assert state["status"] == "invalid_or_stale"
    assert "reviewed_artifact_stale" in state["blocking_reasons"]


def test_unknown_candidate_id_is_invalid(tmp_path: Path) -> None:
    fixture, manifest_path, render_path, manifest = _fixture(tmp_path / "workspace")
    _write_review(fixture, render_path, manifest, candidate_id="CAND999")

    state = _state(fixture, manifest_path, manifest)

    assert state["status"] == "invalid_or_stale"
    assert "candidate_id_mismatch" in state["blocking_reasons"]


def test_semantic_risk_requires_human_review(tmp_path: Path) -> None:
    fixture, manifest_path, _render_path, manifest = _fixture(
        tmp_path / "workspace",
        semantic_risks=["candidate changes a semantic claim"],
    )

    state = _state(fixture, manifest_path, manifest)

    assert state["required_before_apply"] is True
    assert state["blocks_apply"] is True
    assert state["human_required"] is True
    assert "semantic_risk" in state["blocking_reasons"]


def test_missing_review_is_non_blocking_for_pure_mechanical_candidate_without_locked_invariants(
    tmp_path: Path,
) -> None:
    fixture, manifest_path, _render_path, manifest = _fixture(tmp_path / "workspace")

    state = _state(fixture, manifest_path, manifest)

    assert state["status"] == "missing"
    assert state["required_before_apply"] is False
    assert state["blocks_apply"] is False
    assert state["human_required"] is False


def test_replace_text_with_explicit_mechanical_kind_does_not_require_review(
    tmp_path: Path,
) -> None:
    fixture, manifest_path, _render_path, manifest = _fixture(tmp_path / "workspace")
    manifest["operations"] = [
        {
            "kind": "replace_text",
            "semantic_kind": "bounded_coordinate_offset",
            "path": "examples/semantic_demo/semantic_demo.tex",
        }
    ]

    state = _state(fixture, manifest_path, manifest)

    assert state["status"] == "missing"
    assert state["required_before_apply"] is False
    assert state["blocks_apply"] is False


def test_stale_review_blocks_only_candidates_that_require_semantic_review(
    tmp_path: Path,
) -> None:
    fixture, manifest_path, render_path, manifest = _fixture(tmp_path / "workspace")
    _write_review(fixture, render_path, manifest)
    render_path.write_text('{"changed": true}\n', encoding="utf-8")

    optional_state = _state(fixture, manifest_path, manifest)
    required_manifest = {**manifest, "semantic_risks": ["semantic change"]}
    required_state = _state(fixture, manifest_path, required_manifest)

    assert optional_state["status"] == "invalid_or_stale"
    assert optional_state["blocks_apply"] is False
    assert required_state["status"] == "invalid_or_stale"
    assert required_state["blocks_apply"] is True


def test_semantic_review_required_config_requires_review(tmp_path: Path) -> None:
    fixture, manifest_path, _render_path, manifest = _fixture(tmp_path / "workspace")

    state = semantic_candidate_review.build_semantic_review_state(
        fixture,
        manifest_path,
        manifest,
        spec={"semantic_review_required": True},
    )

    assert state["required_before_apply"] is True
    assert state["blocks_apply"] is True
    assert "semantic_review_required" in state["blocking_reasons"]


def test_locked_invariants_require_review(tmp_path: Path) -> None:
    fixture, manifest_path, _render_path, manifest = _fixture(tmp_path / "workspace")

    state = semantic_candidate_review.build_semantic_review_state(
        fixture,
        manifest_path,
        manifest,
        spec={
            "authoring_context_pack": {"enabled": True},
            "panels": [
                {
                    "id": "C",
                    "locked_invariants": ["Energy increases upward."],
                }
            ],
        },
    )

    assert state["required_before_apply"] is True
    assert state["blocks_apply"] is True
    assert "locked_invariants" in state["blocking_reasons"]


def test_review_artifact_cannot_grant_apply_authority_or_operations(tmp_path: Path) -> None:
    fixture, manifest_path, render_path, manifest = _fixture(tmp_path / "workspace")
    _write_review(
        fixture,
        render_path,
        manifest,
        extra={
            "apply_authority": "apply_eligible",
            "operations": [{"kind": "replace_text"}],
        },
    )

    state = _state(fixture, manifest_path, manifest)

    assert state["status"] == "invalid_or_stale"
    assert "authority_field_forbidden" in state["blocking_reasons"]
