from __future__ import annotations

import hashlib
import json
import stat
import subprocess
from pathlib import Path

import pytest
import yaml
from direct_svg_review import DirectSvgReviewError
from direct_svg_stage_review import (
    advance_review_response,
    assert_perceptually_distinct,
    export_public_distribution,
    reveal_blinding_keys,
    stage_review,
)
from PIL import Image

FIXTURE = Path(__file__).parents[1] / "examples" / "fig1_direct_svg_cleanroom_baseline"
PLUGIN_ROOT = FIXTURE.parents[1]


def _head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=PLUGIN_ROOT, text=True
    ).strip()


def _rgb_hash(path: Path) -> str:
    with Image.open(path) as image:
        return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()


def _stage(tmp_path: Path, seed_byte: int = 17, **kwargs: object) -> dict[str, object]:
    return stage_review(
        FIXTURE,
        review_root=tmp_path / "review",
        private_root=tmp_path / ".private",
        private_seed=bytes([seed_byte]) * 32,
        generator_commit=_head(),
        **kwargs,
    )


def test_stage_review_creates_one_three_way_packet_per_panel(tmp_path: Path) -> None:
    result = _stage(tmp_path)
    distribution = Path(result["distribution_path"])
    manifest = yaml.safe_load((distribution / "manifest.yaml").read_text())

    assert manifest["schema"] == "figure-agent.three-way-blind-review.v2"
    assert set(manifest["panels"]) == {"C", "F"}
    decoded_hashes: list[str] = []
    for panel in ("C", "F"):
        panel_dir = distribution / "panels" / panel
        options = sorted(panel_dir.glob("option-?.png"))
        assert len(options) == 3
        assert len({Image.open(path).size for path in options}) == 1
        decoded_hashes.extend(_rgb_hash(path) for path in options)
        assert all(value is None for value in manifest["responses"][panel].values())
    assert len(decoded_hashes) == len(set(decoded_hashes))
    assert not list(distribution.rglob("*private*"))

    private_path = Path(result["private_path"])
    assert stat.S_IMODE(private_path.stat().st_mode) == 0o700
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in private_path.rglob("*"))
    assert manifest["normalization"]["policy"] == "contain_white_pad_authority_size.v1"
    assert manifest["response_schema"] == "figure-agent.three-way-review-response.v2"
    assert manifest["response_contract"] == {
        "additional_fields": False,
        "state_machine": [
            "scientific_gate_pending",
            "primary_scientific_fixed",
            "primary_visual_fixed",
            "second_scientific_fixed",
            "second_visual_fixed",
            "finalized",
        ],
        "scientific_gate_precedes_visual_scoring": True,
        "named_reviewer_and_date_required": True,
        "scientific_evidence_required": True,
        "distinct_second_reviewer_required_when": "borderline_or_disputed",
    }
    assert manifest["perceptual_duplicate_policy"] == {
        "metric": "normalized_rgb_mean_absolute_error.v1",
        "threshold": 0.002,
        "fail_when": "distance_lte_threshold",
        "scope": "within_panel_all_option_pairs",
    }
    assert "upstream_bindings" not in manifest
    assert set(manifest["upstream_commitments"]) == {
        "run_state_1",
        "run_state_2",
        "semantic_packet",
        "authority_C",
        "authority_F",
    }
    assert len(manifest["generator"]["commit"]) == 40
    assert manifest["generator"]["script_blob_sha256"].startswith("sha256:")


def test_fixed_seed_replay_is_deterministic_and_cannot_overwrite(tmp_path: Path) -> None:
    first = _stage(tmp_path)
    with pytest.raises(DirectSvgReviewError, match="review_version_exists"):
        _stage(tmp_path)
    replay = _stage(tmp_path, replay=True)
    comparable = ("version", "public_manifest_sha256")
    assert {key: first[key] for key in comparable} == {
        key: replay[key] for key in comparable
    }


@pytest.mark.parametrize("surface", ["public", "private", "state"])
def test_replay_regenerates_and_rejects_any_bound_tamper(
    tmp_path: Path, surface: str
) -> None:
    result = _stage(tmp_path)
    if surface == "public":
        target = Path(result["distribution_path"]) / "index.html"
    elif surface == "private":
        target = Path(result["private_path"]) / "key.yaml"
    else:
        target = tmp_path / "review" / "review-state.yaml"
    before = target.read_bytes()
    target.write_bytes(before + b"\n# tampered\n")

    with pytest.raises(DirectSvgReviewError, match="replay_byte_mismatch"):
        _stage(tmp_path, replay=True)
    assert target.read_bytes() == before + b"\n# tampered\n"


def test_existing_response_fails_closed(tmp_path: Path) -> None:
    result = _stage(tmp_path)
    response_path = Path(result["distribution_path"]) / "response.yaml"
    response = yaml.safe_load(response_path.read_text())
    response["primary_review"]["reviewer"]["name"] = "already recorded"
    response_path.write_text(yaml.safe_dump(response, sort_keys=False))

    with pytest.raises(DirectSvgReviewError, match="existing_review_response"):
        _stage(tmp_path, seed_byte=18)


@pytest.mark.parametrize(
    "failure_step",
    [
        "before_publish",
        "after_private_publish",
        "after_public_publish",
        "after_state_publish",
    ],
)
def test_failure_at_each_publish_step_preserves_current_version(
    tmp_path: Path, failure_step: str
) -> None:
    first = _stage(tmp_path)
    state_path = tmp_path / "review" / "review-state.yaml"
    state_before = state_path.read_bytes()

    with pytest.raises(RuntimeError, match="injected"):
        _stage(tmp_path, seed_byte=19, failure_injection=failure_step)

    assert state_path.read_bytes() == state_before
    assert Path(first["distribution_path"]).is_dir()
    assert len(list((tmp_path / "review" / "distributions").iterdir())) == 1
    assert len(list((tmp_path / ".private").iterdir())) == 1
    assert not (tmp_path / "review" / ".publish-journal.yaml").exists()


def test_export_contains_only_public_distribution(tmp_path: Path) -> None:
    result = _stage(tmp_path)
    export = tmp_path / "export"
    export_public_distribution(Path(result["distribution_path"]), export)

    assert (export / "manifest.yaml").is_file()
    assert not list(export.rglob("*private*"))
    public_files = {
        path.relative_to(Path(result["distribution_path"]))
        for path in Path(result["distribution_path"]).rglob("*")
        if path.is_file()
    }
    exported_files = {
        path.relative_to(export) for path in export.rglob("*") if path.is_file()
    }
    assert exported_files == public_files


def test_project_locked_reproducibility(tmp_path: Path) -> None:
    results = [_stage(tmp_path / name) for name in ("one", "two")]
    comparable = [
        {
            "version": result["version"],
            "manifest": yaml.safe_load(
                (Path(result["distribution_path"]) / "manifest.yaml").read_text()
            ),
        }
        for result in results
    ]
    assert json.dumps(comparable[0], sort_keys=True) == json.dumps(
        comparable[1], sort_keys=True
    )


def test_perceptual_duplicate_policy_rejects_near_duplicate(tmp_path: Path) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGB", (20, 20), "white").save(first)
    near = Image.new("RGB", (20, 20), "white")
    near.putpixel((0, 0), (254, 254, 254))
    near.save(second)

    with pytest.raises(DirectSvgReviewError, match="perceptual_duplicate"):
        assert_perceptually_distinct([first, second])


def test_generator_commit_must_resolve_and_match_script_blob(tmp_path: Path) -> None:
    with pytest.raises(DirectSvgReviewError, match="generator_commit_invalid"):
        stage_review(
            FIXTURE,
            review_root=tmp_path / "review",
            private_root=tmp_path / ".private",
            private_seed=b"x" * 32,
            generator_commit="does-not-exist",
        )
    with pytest.raises(DirectSvgReviewError, match="generator_script_blob_mismatch"):
        stage_review(
            FIXTURE,
            review_root=tmp_path / "review-two",
            private_root=tmp_path / ".private-two",
            private_seed=b"y" * 32,
            generator_commit=_head(),
            generator_script_sha256="sha256:" + "0" * 64,
        )


def _filled_scientific(response: dict[str, object], reviewer: str) -> dict[str, object]:
    response["state"] = "primary_scientific_fixed"
    primary = response["primary_review"]
    assert isinstance(primary, dict)
    primary["reviewer"] = {"name": reviewer, "reviewed_at": "2026-07-12T12:00:00+09:00"}
    panels = primary["panels"]
    assert isinstance(panels, dict)
    for panel in panels.values():
        for option in panel["scientific"].values():
            option.update({"verdict": "pass", "evidence": "named evidence"})
    return response


def _filled_visual(response: dict[str, object], borderline: bool) -> dict[str, object]:
    response["state"] = "primary_visual_fixed"
    panels = response["primary_review"]["panels"]
    for panel in panels.values():
        panel["visual"].update(
            {
                "composition_preference": "A",
                "illustration_quality_preference": "B",
                "typography_preference": "tie",
                "borderline_or_disputed": borderline,
            }
        )
    response["second_review"]["required"] = borderline
    return response


def test_response_state_machine_rejects_visual_scores_before_scientific_gate(
    tmp_path: Path,
) -> None:
    result = _stage(tmp_path)
    response_path = Path(result["distribution_path"]) / "response.yaml"
    proposed = yaml.safe_load(response_path.read_text())
    proposed = _filled_visual(proposed, False)

    with pytest.raises(DirectSvgReviewError, match="review_transition_invalid"):
        advance_review_response(tmp_path / "review", tmp_path / ".private", proposed)


def test_response_state_machine_requires_distinct_second_reviewer_and_fixed_hash(
    tmp_path: Path,
) -> None:
    result = _stage(tmp_path)
    response_path = Path(result["distribution_path"]) / "response.yaml"
    proposed = _filled_scientific(yaml.safe_load(response_path.read_text()), "Reviewer One")
    advance_review_response(tmp_path / "review", tmp_path / ".private", proposed)
    proposed = _filled_visual(proposed, True)
    advance_review_response(tmp_path / "review", tmp_path / ".private", proposed)

    proposed["state"] = "second_scientific_fixed"
    proposed["second_review"]["reviewer"] = proposed["primary_review"]["reviewer"]
    for panel in proposed["second_review"]["panels"].values():
        for option in panel["scientific"].values():
            option.update({"verdict": "pass", "evidence": "second evidence"})
    with pytest.raises(DirectSvgReviewError, match="second_reviewer_must_be_distinct"):
        advance_review_response(tmp_path / "review", tmp_path / ".private", proposed)

    proposed["second_review"]["reviewer"] = {
        "name": "Reviewer Two",
        "reviewed_at": "2026-07-12T13:00:00+09:00",
    }
    advance_review_response(tmp_path / "review", tmp_path / ".private", proposed)
    proposed["state"] = "second_visual_fixed"
    for panel in proposed["second_review"]["panels"].values():
        panel["visual"].update(
            {
                "composition_preference": "A",
                "illustration_quality_preference": "B",
                "typography_preference": "tie",
                "borderline_or_disputed": False,
            }
        )
    advance_review_response(tmp_path / "review", tmp_path / ".private", proposed)
    proposed["state"] = "finalized"
    advance_review_response(tmp_path / "review", tmp_path / ".private", proposed)

    state = yaml.safe_load((tmp_path / "review" / "review-state.yaml").read_text())
    assert state["response_state"] == "finalized"
    assert state["finalized_response_sha256"].startswith("sha256:")
    assert (Path(result["private_path"]) / "final-response.yaml").is_file()


def test_unblind_rejects_nonfinal_or_tampered_response(tmp_path: Path) -> None:
    result = _stage(tmp_path)
    with pytest.raises(DirectSvgReviewError, match="response_not_finalized"):
        reveal_blinding_keys(tmp_path / "review", tmp_path / ".private")

    response_path = Path(result["distribution_path"]) / "response.yaml"
    proposed = _filled_scientific(yaml.safe_load(response_path.read_text()), "Reviewer One")
    advance_review_response(tmp_path / "review", tmp_path / ".private", proposed)
    proposed = _filled_visual(proposed, False)
    advance_review_response(tmp_path / "review", tmp_path / ".private", proposed)
    proposed["state"] = "finalized"
    advance_review_response(tmp_path / "review", tmp_path / ".private", proposed)
    response_path.write_bytes(response_path.read_bytes() + b"\n# tampered\n")
    with pytest.raises(DirectSvgReviewError, match="finalized_response_hash_mismatch"):
        reveal_blinding_keys(tmp_path / "review", tmp_path / ".private")


def test_public_tree_contains_no_known_raw_input_hash(tmp_path: Path) -> None:
    result = _stage(tmp_path)
    distribution = Path(result["distribution_path"])
    public_bytes = b"\n".join(
        path.read_bytes() for path in distribution.rglob("*") if path.is_file()
    )
    raw_paths = [
        FIXTURE / "runs/test-a/run-state.yaml",
        FIXTURE / "runs/test-b/run-state.yaml",
        FIXTURE / "contract/semantic-packet.yaml",
        FIXTURE / "reference/crops/panel-c.png",
        FIXTURE / "reference/crops/panel-f.png",
    ]
    for path in raw_paths:
        assert hashlib.sha256(path.read_bytes()).hexdigest().encode() not in public_bytes
