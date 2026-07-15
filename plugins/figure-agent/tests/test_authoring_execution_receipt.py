from __future__ import annotations

import json
import shutil
from pathlib import Path

import authoring_execution_packet
import authoring_execution_receipt
import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _evidence(tmp_path: Path, *, with_visual_asset: bool = False) -> dict[str, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples/context_demo"
    review = fixture / "review"
    attempt = review / "failure-first/execution-binding-v1"
    attempt.mkdir(parents=True)
    visual_asset_config = (
        "authoring_context_pack:\n"
        "  enabled: true\n"
        "  visual_asset_ids: [panel_f_floating_cantilever]\n"
        if with_visual_asset
        else ""
    )
    (fixture / "spec.yaml").write_text(
        "name: context_demo\ntitle: Demo\nstyle_profile: polymer-paper\n"
        + visual_asset_config
        + "panels: []\n",
        encoding="utf-8",
    )
    (review / "budget.yaml").write_text("max_attempts: 1\n", encoding="utf-8")
    (review / "blank.txt").write_text("", encoding="utf-8")
    output_rel = (
        "examples/context_demo/review/failure-first/execution-binding-v1/"
        "control_generated.tex"
    )
    plugin_root = PLUGIN_ROOT
    if with_visual_asset:
        plugin_root = tmp_path / "plugin"
        shutil.copytree(PLUGIN_ROOT / "styles", plugin_root / "styles")
    packet, prompt = authoring_execution_packet.compile_authoring_execution_packet(
        "context_demo",
        plugin_root=plugin_root,
        workspace_root=workspace,
        model_id="gpt-5.5",
        budget_contract="examples/context_demo/review/budget.yaml",
        blank_start="examples/context_demo/review/blank.txt",
        output_path=output_rel,
    )
    packet_path = attempt / "control_packet.json"
    prompt_path = attempt / "control_prompt.md"
    authoring_execution_packet.write_authoring_execution_packet(
        packet_path,
        prompt_path,
        packet=packet,
        prompt=prompt,
    )
    source_path = workspace / output_rel
    source_path.write_text(
        "\\documentclass[tikz,border=4pt]{standalone}\n"
        "\\usepackage{tikz}\n"
        "\\usepackage{polymer-paper-preamble}\n"
        "\\begin{document}\\begin{tikzpicture}\\end{tikzpicture}\\end{document}\n",
        encoding="utf-8",
    )
    transcript_path = attempt / "control.transcript.jsonl"
    transcript_path.write_text('{"event":"completed"}\n', encoding="utf-8")
    touched_files_path = attempt / "control.touched-files.json"
    touched_files_path.write_text(json.dumps([output_rel]) + "\n", encoding="utf-8")
    paths = {
        "workspace": workspace,
        "packet": packet_path,
        "prompt": prompt_path,
        "source": source_path,
        "transcript": transcript_path,
        "touched": touched_files_path,
        "receipt": attempt / "control_receipt.json",
    }
    if with_visual_asset:
        paths["asset"] = (
            plugin_root / "styles/snippets/panel-f-floating-cantilever.tex"
        )
    return paths


def _record(paths: dict[str, Path], **overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "workspace_root": paths["workspace"],
        "packet_path": paths["packet"],
        "prompt_path": paths["prompt"],
        "transcript_path": paths["transcript"],
        "generated_source_path": paths["source"],
        "touched_files_path": paths["touched"],
        "receipt_path": paths["receipt"],
        "actual_model_id": "gpt-5.5",
        "actual_token_usage": None,
        "token_usage_unavailable_reason": "adapter_did_not_report_usage",
        "forbidden_input_audit": "no_forbidden_path_observed_in_transcript",
    }
    kwargs.update(overrides)
    return authoring_execution_receipt.record_authoring_execution_receipt(**kwargs)


def test_records_bound_runtime_evidence(tmp_path: Path) -> None:
    paths = _evidence(tmp_path)

    receipt = _record(paths)

    assert receipt["schema"] == "figure-agent.authoring-execution-receipt.v1"
    assert receipt["packet_sha256"].startswith("sha256:")
    assert receipt["prompt_sha256"].startswith("sha256:")
    assert receipt["transcript_sha256"].startswith("sha256:")
    assert receipt["generated_source_sha256"].startswith("sha256:")
    assert receipt["touched_files"] == [
        "examples/context_demo/review/failure-first/execution-binding-v1/"
        "control_generated.tex"
    ]
    assert receipt["feedback_rounds"] == 0
    assert receipt["manual_repairs"] == 0
    assert receipt["filesystem_read_isolation"] == "unavailable"
    assert receipt["publication_acceptance"] == "not_claimed"
    assert json.loads(paths["receipt"].read_text(encoding="utf-8")) == receipt


def test_receipt_rejects_visual_asset_byte_drift(tmp_path: Path) -> None:
    paths = _evidence(tmp_path, with_visual_asset=True)
    paths["asset"].write_text(
        paths["asset"].read_text(encoding="utf-8") + "% drift\n",
        encoding="utf-8",
    )

    with pytest.raises(
        authoring_execution_receipt.AuthoringExecutionReceiptError,
        match="visual asset byte drift",
    ):
        _record(paths)


def test_records_transcript_from_ancestor_repository_root(tmp_path: Path) -> None:
    paths = _evidence(tmp_path)
    repository_root = tmp_path / "repository"
    workspace = repository_root / "plugins/figure-agent"
    workspace.parent.mkdir(parents=True)
    paths["workspace"].rename(workspace)
    for key in ("packet", "prompt", "source", "transcript", "touched", "receipt"):
        paths[key] = workspace / paths[key].relative_to(paths["workspace"])
    paths["workspace"] = workspace
    transcript = repository_root / ".witnessd/runs/control/adapter-transcript.txt"
    transcript.parent.mkdir(parents=True)
    transcript.write_text('{"event":"completed"}\n', encoding="utf-8")
    paths["transcript"] = transcript

    receipt = _record(paths, repository_root=repository_root)

    assert receipt["transcript_root"] == "repository"
    assert receipt["transcript_path"] == (
        ".witnessd/runs/control/adapter-transcript.txt"
    )


def test_rejects_repository_root_that_does_not_contain_workspace(tmp_path: Path) -> None:
    paths = _evidence(tmp_path)

    with pytest.raises(
        authoring_execution_receipt.AuthoringExecutionReceiptError,
        match="repository root",
    ):
        _record(paths, repository_root=tmp_path / "other-repository")


def test_touched_scope_is_repository_relative_when_execution_cwd_is_nested() -> None:
    packet = {
        "execution_cwd": "plugins/figure-agent",
        "output_path": "examples/demo/review/failure-first/execution-binding-v1/out.tex",
    }

    assert authoring_execution_receipt._expected_touched_files(packet) == [
        "plugins/figure-agent/examples/demo/review/failure-first/"
        "execution-binding-v1/out.tex"
    ]


def test_rejects_model_mismatch(tmp_path: Path) -> None:
    paths = _evidence(tmp_path)
    with pytest.raises(
        authoring_execution_receipt.AuthoringExecutionReceiptError,
        match="model mismatch",
    ):
        _record(paths, actual_model_id="other-model")


def test_rejects_extra_touched_file(tmp_path: Path) -> None:
    paths = _evidence(tmp_path)
    paths["touched"].write_text(
        json.dumps(
            [
                "examples/context_demo/review/failure-first/execution-binding-v1/"
                "control_generated.tex",
                "README.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        authoring_execution_receipt.AuthoringExecutionReceiptError,
        match="touched files differ",
    ):
        _record(paths)


def test_rejects_ambiguous_token_usage(tmp_path: Path) -> None:
    paths = _evidence(tmp_path)
    with pytest.raises(
        authoring_execution_receipt.AuthoringExecutionReceiptError,
        match="token usage",
    ):
        _record(
            paths,
            actual_token_usage=123,
            token_usage_unavailable_reason="also unavailable",
        )
