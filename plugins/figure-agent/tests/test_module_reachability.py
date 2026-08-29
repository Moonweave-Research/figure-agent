"""Ratchet on modules that no entry point reaches.

Unreachable code accumulated to 22.4k lines because nothing ever asked. The
bundles are gone; this keeps the next one from arriving unannounced. A module
that becomes unreachable fails here until someone either wires it up or adds
it below with the reason it is kept.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "checks"))

import check_module_reachability  # noqa: E402

# Kept deliberately, with the reason. Operator CLIs are invoked by a person,
# not by the runtime, so the import graph cannot see them.
KNOWN_DORMANT = {
    "attempt_local_repair_binding": "exercised by the R4.13 attempt-local suite",
    "build_codex_marketplace": "release packaging, run by hand",
    "check_module_reachability": "this checker; reached from its own test",
    "check_panel_boundary_coverage": "operator CLI",
    "check_paper_artifact_registry": "external-workspace CLI (--root/--registry)",
    "compile_failure_corpus": "corpus builder, run by hand",
    "dogfood_metrics": "dogfood reporting, run by hand",
    "handcrafted_finish_benchmark": "benchmark named in docs/paper_figure_map.yaml",
    "match_snippet": "authoring aid, run by hand",
    "panel_f_transfer_receipt": "fig1 Panel-F campaign receipt",
    "prospective_evidence_receipt": "named in docs/execution-plan.md",
    "recover_experience_records": "operator recovery CLI",
    "semantic_legibility_evidence": "operator CLI",
    "structural_collision_gate": "operator CLI",
}


def test_no_module_becomes_unreachable_without_being_declared() -> None:
    dormant = set(check_module_reachability.dormant_modules(PLUGIN_ROOT))

    undeclared = sorted(dormant - set(KNOWN_DORMANT))
    assert not undeclared, (
        "these modules are no longer reachable from any entry point; wire them "
        f"up or declare them in KNOWN_DORMANT with a reason: {undeclared}"
    )


def test_declared_dormant_modules_that_became_reachable_are_removed() -> None:
    """The allowlist is a ledger, not a place to leave stale entries."""
    dormant = set(check_module_reachability.dormant_modules(PLUGIN_ROOT))

    stale = sorted(set(KNOWN_DORMANT) - dormant)
    assert not stale, f"these are reachable now and should leave KNOWN_DORMANT: {stale}"


def test_the_walk_fails_loudly_when_it_cannot_see_entry_points(tmp_path: Path) -> None:
    """A broken walk reports everything as reachable, which reads clean. The
    controls have to turn that into an error."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "status.py").write_text("x = 1\n", encoding="utf-8")

    with pytest.raises(
        check_module_reachability.ModuleReachabilityError,
        match="reachability controls unreachable",
    ):
        check_module_reachability.dormant_modules(tmp_path)
