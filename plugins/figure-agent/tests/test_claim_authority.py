from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import authoring_context_pack  # noqa: E402
import claim_authority  # noqa: E402
from status import infer_stage  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_fixture(tmp_path: Path, *, state: str = "unresolved") -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "claim_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        """
name: claim_demo
title: Claim authority demo
style_profile: polymer-paper
authoring_context_pack:
  enabled: true
panels:
  - id: C
    caption: Energy diagram
    semantic_claims:
      - id: trap-shape
        claim: The distribution contains two resolved trap peaks.
    locked_invariants:
      - id: energy-up
        invariant: Energy increases upward.
""".lstrip(),
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text(
        "## Physics invariants\n\n- Energy increases upward.\n",
        encoding="utf-8",
    )
    (fixture / "claim_authority.yaml").write_text(
        f"""
schema: figure-agent.claim-authority.v1
fixture: claim_demo
items:
  - id: trap-shape-not-settled
    panel_id: C
    kind: scientific_claim
    state: {state}
    statement: The available evidence does not uniquely determine a two-peak shape.
    targets: [claim:C:trap-shape]
    evidence_refs: [decision-brief:trap-shape]
""".lstrip(),
        encoding="utf-8",
    )
    return workspace, fixture


def test_claim_authority_blocks_unresolved_target_without_resolving_it(
    tmp_path: Path,
) -> None:
    _, fixture = _write_fixture(tmp_path)

    summary = claim_authority.load_claim_authority(fixture)

    assert summary["state"] == "BLOCKED"
    assert summary["requires_human"] is True
    assert summary["blocking_item_ids"] == ["trap-shape-not-settled"]
    assert summary["items"][0]["targets"] == ["claim:C:trap-shape"]


def test_claim_authority_rejects_a_target_not_declared_by_the_spec(tmp_path: Path) -> None:
    _, fixture = _write_fixture(tmp_path)
    authority = fixture / "claim_authority.yaml"
    authority.write_text(
        authority.read_text(encoding="utf-8").replace(
            "claim:C:trap-shape", "claim:C:invented-claim"
        ),
        encoding="utf-8",
    )

    summary = claim_authority.load_claim_authority(fixture)

    assert summary["state"] == "INVALID"
    assert summary["reason"] == "unknown_target:claim:C:invented-claim"


def test_authoring_context_surfaces_the_claim_stop_before_semantic_instructions(
    tmp_path: Path,
) -> None:
    workspace, _ = _write_fixture(tmp_path)

    payload = authoring_context_pack.build_context_pack(
        "claim_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    rendered = authoring_context_pack.render_text(payload)

    assert payload["authoring_ready"] is False
    assert payload["claim_authority"]["state"] == "BLOCKED"
    assert "AUTHORING STOP" in rendered
    assert rendered.index("## Claim Authority") < rendered.index("## Semantic Contracts")
    assert "Do not assert target [claim:C:trap-shape]" in rendered
    assert "BLOCKED claim C trap-shape" in rendered


def test_status_routes_unresolved_claim_authority_to_a_human_stop(tmp_path: Path) -> None:
    _, fixture = _write_fixture(tmp_path)

    result = infer_stage(fixture)

    assert result["claim_authority"]["state"] == "BLOCKED"
    assert ("claim_authority", "blocked") in result["checks"]
    assert "claim_authority_blocked" in result["notes"]
    assert result["workflow_ready"] is False
    assert result["next_action_summary"]["action"] == "human_gate_stop"
    assert result["next_action_summary"]["blocking_source"] == "claim_authority_unresolved"
    assert result["next_action_summary"]["requires_human"] is True
