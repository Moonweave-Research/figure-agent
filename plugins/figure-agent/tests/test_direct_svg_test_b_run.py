from __future__ import annotations

import hashlib
import importlib.util
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig1_direct_svg_cleanroom_baseline"
RUN_ROOT = FIXTURE / "runs" / "test-b"
REPLAY_PATH = RUN_ROOT / "replay.py"

spec = importlib.util.spec_from_file_location("direct_svg_test_b_replay", REPLAY_PATH)
assert spec and spec.loader
test_b_replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_b_replay)


def _load(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _copy_fixture(tmp_path: Path) -> tuple[Path, Path]:
    plugin_root = tmp_path / "plugin"
    fixture = plugin_root / "examples" / "fig1_direct_svg_cleanroom_baseline"
    (fixture / "packets").mkdir(parents=True)
    (fixture / "contract" / "fonts").mkdir(parents=True)
    (fixture / "contract" / "licenses").mkdir(parents=True)
    shutil.copy2(FIXTURE / "packets" / "test-b-synthesis.yaml", fixture / "packets")
    for relative in (
        "semantic-packet.yaml",
        "fontconfig.xml",
        "font-receipt.yaml",
        "fonts/lmsans10-regular.otf",
        "licenses/GUST-FONT-LICENSE.TXT",
    ):
        shutil.copy2(FIXTURE / "contract" / relative, fixture / "contract" / relative)
    shutil.copytree(RUN_ROOT, fixture / "runs" / "test-b")
    return plugin_root, fixture


def _update_bound_file_hash(state: dict[str, Any], run_root: Path, key: str) -> None:
    binding = state[key]
    binding["sha256"] = _sha256(run_root / binding["path"])


def _update_ledger_hash(state: dict[str, Any], run_root: Path, panel: str) -> None:
    artifact = next(item for item in state["candidate_artifacts"] if item["panel"] == panel)
    artifact["ledger_sha256"] = _sha256(run_root / artifact["ledger_path"])


def _mutate_semantic_contract(fixture: Path) -> tuple[str, str]:
    semantic_path = fixture / "contract" / "semantic-packet.yaml"
    semantic = _load(semantic_path)
    semantic["scientific_objects"]["panel_c"].append(
        {"id": "c_review_added_object", "kind": "review mutation object"}
    )
    semantic["text_content"]["panel_c"].append("review-added-live-text")
    semantic["visual_roles"]["panel_c"]["c_review_added_object"] = "review_mutation_role"
    _write(semantic_path, semantic)
    semantic_hash = _sha256(semantic_path)

    packet_path = fixture / "packets" / "test-b-synthesis.yaml"
    packet = _load(packet_path)
    semantic_input = next(
        item for item in packet["allowed_inputs"] if item["role"] == "semantic_packet"
    )
    semantic_input["sha256"] = semantic_hash
    _write(packet_path, packet)
    return semantic_hash, _sha256(packet_path)


def _rebind_semantic_and_packet(
    fixture: Path,
    *,
    semantic_hash: str,
    packet_hash: str,
) -> None:
    run_root = fixture / "runs" / "test-b"
    state_path = run_root / "run-state.yaml"
    state = _load(state_path)
    state["semantic_packet"]["sha256"] = semantic_hash
    state["synthesis_packet"]["sha256"] = packet_hash

    environment_path = run_root / state["environment_receipt"]["path"]
    environment = _load(environment_path)
    environment["semantic_packet"]["sha256"] = semantic_hash
    environment["synthesis_packet"]["sha256"] = packet_hash
    _write(environment_path, environment)
    _update_bound_file_hash(state, run_root, "environment_receipt")

    for panel in ("C", "F"):
        ledger_path = run_root / f"panel-{panel.lower()}" / "ledger.yaml"
        ledger = _load(ledger_path)
        ledger["semantic_packet"]["sha256"] = semantic_hash
        ledger["synthesis_packet"]["sha256"] = packet_hash
        for receipt in ledger["iterations"]:
            tool = receipt["tool_model_receipt"]
            tool["semantic_packet_sha256"] = semantic_hash
            tool["synthesis_packet_sha256"] = packet_hash
        _write(ledger_path, ledger)
        _update_ledger_hash(state, run_root, panel)
    _write(state_path, state)


def test_test_b_run_is_packet_derived_reproducible_and_machine_review_ready() -> None:
    report = test_b_replay.validate_run(plugin_root=PLUGIN_ROOT, fixture_root=FIXTURE)
    semantic = _load(FIXTURE / "contract" / "semantic-packet.yaml")
    state = _load(RUN_ROOT / "run-state.yaml")

    assert report["cycles_validated"] == 6
    assert report["relation_metadata_complete"] is True
    assert report["spatial_scientific_verification"] == "pending_human_review"
    for panel in ("c", "f"):
        derived_ids = sorted(
            item["id"] for item in semantic["scientific_objects"][f"panel_{panel}"]
        )
        assert report["panels"][panel]["required_ids"] == derived_ids
        assert (
            report["panels"][panel]["required_text"] == semantic["text_content"][f"panel_{panel}"]
        )
    assert state["state"] == "machine_review_ready"
    assert state["machine_validation"]["relation_metadata_complete"] == ("passed_all_6_cycles")
    assert state["machine_validation"]["spatial_scientific_verification"] == (
        "pending_human_review"
    )
    assert state["human_scientific_acceptance"] == "pending"
    assert state["human_visual_acceptance"] == "pending"
    assert state["publication_acceptance"] == "not_claimed"

    replay = subprocess.run(
        ["uv", "run", "python", str(REPLAY_PATH), "--verify"],
        cwd=PLUGIN_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert "replay verified: 6/6 deterministic renders" in replay.stdout


@pytest.mark.parametrize("surface", ["environment", "ledger", "cycle"])
@pytest.mark.parametrize("digit", ["0", "1"])
def test_zero_or_one_semantic_hash_mutation_is_rejected(
    tmp_path: Path,
    digit: str,
    surface: str,
) -> None:
    plugin_root, fixture = _copy_fixture(tmp_path)
    run_root = fixture / "runs" / "test-b"
    state_path = run_root / "run-state.yaml"
    state = _load(state_path)
    invalid_hash = f"sha256:{digit * 64}"
    if surface == "environment":
        environment_path = run_root / state["environment_receipt"]["path"]
        environment = _load(environment_path)
        environment["semantic_packet"]["sha256"] = invalid_hash
        _write(environment_path, environment)
        _update_bound_file_hash(state, run_root, "environment_receipt")
    else:
        ledger_path = run_root / "panel-c" / "ledger.yaml"
        ledger = _load(ledger_path)
        if surface == "ledger":
            ledger["semantic_packet"]["sha256"] = invalid_hash
        else:
            ledger["iterations"][0]["tool_model_receipt"]["semantic_packet_sha256"] = invalid_hash
        _write(ledger_path, ledger)
        _update_ledger_hash(state, run_root, "C")
    _write(state_path, state)

    with pytest.raises(test_b_replay.TestBRunError, match="semantic_binding_mismatch"):
        test_b_replay.validate_run(plugin_root=plugin_root, fixture_root=fixture)


def test_cycle_synthesis_hash_mutation_is_rejected(tmp_path: Path) -> None:
    plugin_root, fixture = _copy_fixture(tmp_path)
    run_root = fixture / "runs" / "test-b"
    ledger_path = run_root / "panel-c" / "ledger.yaml"
    ledger = _load(ledger_path)
    ledger["iterations"][0]["tool_model_receipt"]["synthesis_packet_sha256"] = "sha256:" + "0" * 64
    _write(ledger_path, ledger)
    state_path = run_root / "run-state.yaml"
    state = _load(state_path)
    _update_ledger_hash(state, run_root, "C")
    _write(state_path, state)

    with pytest.raises(test_b_replay.TestBRunError, match="synthesis_binding_mismatch"):
        test_b_replay.validate_run(plugin_root=plugin_root, fixture_root=fixture)


@pytest.mark.parametrize("mutation", ["nonsense", "missing", "duplicate"])
def test_recorded_command_mutations_are_rejected(
    tmp_path: Path,
    mutation: str,
) -> None:
    plugin_root, fixture = _copy_fixture(tmp_path)
    run_root = fixture / "runs" / "test-b"
    ledger_path = run_root / "panel-c" / "ledger.yaml"
    ledger = _load(ledger_path)
    command = ledger["iterations"][0]["command"]
    if mutation == "nonsense":
        command.extend(["--banana", "yes"])
    elif mutation == "missing":
        index = command.index("--panel")
        del command[index : index + 2]
    else:
        command.extend(["--width", "960"])
    _write(ledger_path, ledger)
    state_path = run_root / "run-state.yaml"
    state = _load(state_path)
    _update_ledger_hash(state, run_root, "C")
    _write(state_path, state)

    with pytest.raises(test_b_replay.TestBRunError, match="recorded_command_invalid"):
        test_b_replay.validate_run(plugin_root=plugin_root, fixture_root=fixture)


def test_semantic_packet_growth_rejects_stale_state_and_receipts(tmp_path: Path) -> None:
    plugin_root, fixture = _copy_fixture(tmp_path)
    _mutate_semantic_contract(fixture)

    with pytest.raises(test_b_replay.TestBRunError, match="input_binding_mismatch"):
        test_b_replay.validate_run(plugin_root=plugin_root, fixture_root=fixture)


def test_semantic_packet_growth_rejects_rebound_but_stale_svgs(tmp_path: Path) -> None:
    plugin_root, fixture = _copy_fixture(tmp_path)
    semantic_hash, packet_hash = _mutate_semantic_contract(fixture)
    _rebind_semantic_and_packet(
        fixture,
        semantic_hash=semantic_hash,
        packet_hash=packet_hash,
    )

    with pytest.raises(test_b_replay.TestBRunError, match="semantic_svg_incomplete"):
        test_b_replay.validate_run(plugin_root=plugin_root, fixture_root=fixture)


def test_elapsed_minutes_are_self_attested_monotonic_and_bounded() -> None:
    for panel in ("c", "f"):
        ledger = _load(RUN_ROOT / f"panel-{panel}" / "ledger.yaml")
        assert ledger["elapsed_provenance"] == "self_reported_during_authoring"
        assert ledger["timestamp_reconstruction"] == (
            "not_available_and_not_reconstructable_from_git_timestamps"
        )
        assert "started_at" not in ledger
        elapsed = [receipt["elapsed_minutes"] for receipt in ledger["iterations"]]
        assert elapsed == sorted(elapsed)
        assert elapsed[-1] <= ledger["budget"]["wall_minutes_per_panel"]


def test_nonmonotonic_elapsed_minutes_are_rejected(tmp_path: Path) -> None:
    plugin_root, fixture = _copy_fixture(tmp_path)
    run_root = fixture / "runs" / "test-b"
    ledger_path = run_root / "panel-c" / "ledger.yaml"
    ledger = _load(ledger_path)
    ledger["iterations"][1]["elapsed_minutes"] = 0.1
    _write(ledger_path, ledger)
    state_path = run_root / "run-state.yaml"
    state = _load(state_path)
    _update_ledger_hash(state, run_root, "C")
    _write(state_path, state)

    with pytest.raises(test_b_replay.TestBRunError, match="elapsed_minutes_invalid"):
        test_b_replay.validate_run(plugin_root=plugin_root, fixture_root=fixture)


@pytest.mark.parametrize(
    ("svg", "png"),
    [
        (
            "examples/fig1_direct_svg_cleanroom_baseline/runs/test-b/panel-c/cycles/cycle-01.svg",
            "tests/arbitrary-output.png",
        ),
        (
            "examples/fig1_direct_svg_cleanroom_baseline/runs/test-b/panel-c/cycles/../../../../escape.svg",
            "examples/fig1_direct_svg_cleanroom_baseline/runs/test-b/panel-c/cycles/out.png",
        ),
        (
            "examples/fig1_direct_svg_cleanroom_baseline/runs/test-b/panel-c/cycles/cycle-01.png",
            "examples/fig1_direct_svg_cleanroom_baseline/runs/test-b/panel-c/cycles/out.png",
        ),
        (
            "examples/fig1_direct_svg_cleanroom_baseline/runs/test-b/panel-c/cycles/cycle-01.svg",
            "examples/fig1_direct_svg_cleanroom_baseline/runs/test-b/panel-c/cycles/out.svg",
        ),
        (
            "examples/fig1_direct_svg_cleanroom_baseline/runs/test-b/panel-c/cycles/cycle-01.svg",
            "examples/fig1_direct_svg_cleanroom_baseline/runs/test-b/panel-c/cycles/cycle-01.svg",
        ),
    ],
)
def test_render_paths_are_confined_to_test_b(svg: str, png: str) -> None:
    with pytest.raises(test_b_replay.TestBRunError, match="render_path_invalid"):
        test_b_replay.resolve_render_paths(
            plugin_root=PLUGIN_ROOT,
            run_root=RUN_ROOT,
            svg=svg,
            png=png,
        )
