from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path

import pytest
import yaml
from direct_svg_review import DirectSvgReviewError
from direct_svg_stage_review import export_public_distribution, stage_review
from PIL import Image

FIXTURE = Path(__file__).parents[1] / "examples" / "fig1_direct_svg_cleanroom_baseline"


def _rgb_hash(path: Path) -> str:
    with Image.open(path) as image:
        return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()


def _stage(tmp_path: Path, seed_byte: int = 17, **kwargs: object) -> dict[str, object]:
    return stage_review(
        FIXTURE,
        review_root=tmp_path / "review",
        private_root=tmp_path / ".private",
        private_seed=bytes([seed_byte]) * 32,
        generator_commit="test-generator-commit",
        **kwargs,
    )


def test_stage_review_creates_one_three_way_packet_per_panel(tmp_path: Path) -> None:
    result = _stage(tmp_path)
    distribution = Path(result["distribution_path"])
    manifest = yaml.safe_load((distribution / "manifest.yaml").read_text())

    assert manifest["schema"] == "figure-agent.three-way-blind-review.v1"
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
    assert manifest["response_schema"] == "figure-agent.three-way-review-response.v1"


def test_fixed_seed_replay_is_deterministic_and_cannot_overwrite(tmp_path: Path) -> None:
    first = _stage(tmp_path)
    with pytest.raises(DirectSvgReviewError, match="review_version_exists"):
        _stage(tmp_path)
    replay = _stage(tmp_path, replay=True)
    comparable = ("version", "public_manifest_sha256")
    assert {key: first[key] for key in comparable} == {
        key: replay[key] for key in comparable
    }


def test_existing_response_fails_closed(tmp_path: Path) -> None:
    result = _stage(tmp_path)
    response_path = Path(result["distribution_path"]) / "response.yaml"
    response = yaml.safe_load(response_path.read_text())
    response["primary_reviewer"]["name"] = "already recorded"
    response_path.write_text(yaml.safe_dump(response, sort_keys=False))

    with pytest.raises(DirectSvgReviewError, match="existing_review_response"):
        _stage(tmp_path, seed_byte=18)


def test_failure_before_publish_preserves_current_version(tmp_path: Path) -> None:
    first = _stage(tmp_path)
    state_path = tmp_path / "review" / "review-state.yaml"
    state_before = state_path.read_bytes()

    with pytest.raises(RuntimeError, match="injected"):
        _stage(tmp_path, seed_byte=19, failure_injection="before_publish")

    assert state_path.read_bytes() == state_before
    assert Path(first["distribution_path"]).is_dir()
    assert len(list((tmp_path / "review" / "distributions").iterdir())) == 1


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
