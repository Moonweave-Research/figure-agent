from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _module():
    return importlib.import_module("visual_finding_artifacts")


def _fixture(tmp_path: Path, candidates: list[dict]) -> Path:
    fixture = tmp_path / "demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    Image.new("RGB", (100, 100), "white").save(build / "demo.png")
    (build / "visual_clash.json").write_text(
        json.dumps({"fixture": "demo", "candidates": candidates, "total": len(candidates)}),
        encoding="utf-8",
    )
    return fixture


def _candidate(candidate_id: str, state: str, bbox: list[int]) -> dict:
    return {
        "id": candidate_id,
        "kind": "near_miss",
        "text": candidate_id,
        "bbox_px": bbox,
        "attribution": {
            "state": state,
            "detector_bbox_px": [float(value) for value in bbox],
            "detector_confidence": None,
            "bbox_pdf_cm": [value / 10 for value in bbox],
            "panel_candidates": [],
            "region_candidates": [],
        },
    }


def test_emits_overlay_crop_and_hash_manifest_for_every_finding(tmp_path: Path) -> None:
    module = _module()
    fixture = _fixture(
        tmp_path,
        [
            _candidate("VC001", "exact", [10, 10, 30, 30]),
            _candidate("VC002", "ambiguous", [35, 35, 55, 55]),
            _candidate("VC003", "unbound", [60, 60, 80, 80]),
        ],
    )

    manifest = module.build_visual_finding_artifacts(fixture)

    assert manifest["schema"] == "figure-agent.visual-finding-artifacts.v1"
    assert manifest["finding_count"] == 3
    assert manifest["input_render_sha256"].startswith("sha256:")
    assert [item["finding_id"] for item in manifest["findings"]] == [
        "VC001",
        "VC002",
        "VC003",
    ]
    assert {item["attribution_state"] for item in manifest["findings"]} == {
        "exact",
        "ambiguous",
        "unbound",
    }
    for item in manifest["findings"]:
        assert item["bbox_px"]
        assert item["bbox_pdf_cm"]
        assert item["overlay_sha256"].startswith("sha256:")
        assert item["crop_sha256"].startswith("sha256:")
        assert (fixture / "build" / "perception" / item["overlay_path"]).is_file()
        assert (fixture / "build" / "perception" / item["crop_path"]).is_file()

    overlay_hashes = {item["overlay_sha256"] for item in manifest["findings"]}
    assert len(overlay_hashes) == 3
    on_disk = json.loads(
        (
            fixture
            / "build"
            / "perception"
            / "visual_findings"
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert on_disk == manifest


def test_no_finding_report_emits_empty_manifest_without_fake_images(tmp_path: Path) -> None:
    module = _module()
    fixture = _fixture(tmp_path, [])

    manifest = module.build_visual_finding_artifacts(fixture)

    artifact_dir = fixture / "build" / "perception" / "visual_findings"
    assert manifest["finding_count"] == 0
    assert manifest["findings"] == []
    assert (artifact_dir / "manifest.json").is_file()
    assert list((artifact_dir / "overlays").iterdir()) == []
    assert list((artifact_dir / "crops").iterdir()) == []


def test_fallback_pdf_bbox_uses_installed_pdfinfo_without_pdfplumber(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _module()

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="Pages: 1\nPage size: 200 x 100 pts\n",
            stderr="",
        ),
    )

    assert module._fallback_pdf_bbox(
        Path("render.pdf"), [0, 0, 100, 50], (100, 100)
    ) == [0.0, 1.763889, 7.055556, 3.527778]


def test_explicit_artifact_base_supports_multiple_tex_variants_in_one_fixture(
    tmp_path: Path,
) -> None:
    module = _module()
    fixture = _fixture(tmp_path, [])
    build = fixture / "build"
    Image.new("RGB", (100, 100), "white").save(build / "variant_a.png")

    manifest = module.build_visual_finding_artifacts(
        fixture,
        artifact_base="variant_a",
    )

    assert manifest["fixture"] == "demo"
    assert manifest["artifact_base"] == "variant_a"


def test_explicit_artifact_base_accepts_compile_macro_variants(tmp_path: Path) -> None:
    module = _module()
    fixture = _fixture(tmp_path, [])
    build = fixture / "build"
    Image.new("RGB", (100, 100), "white").save(build / "_macro_smoke.png")

    manifest = module.build_visual_finding_artifacts(
        fixture,
        artifact_base="_macro_smoke",
    )

    assert manifest["artifact_base"] == "_macro_smoke"


def test_rejects_unsafe_finding_id_before_writing_images(tmp_path: Path) -> None:
    module = _module()
    fixture = _fixture(
        tmp_path,
        [_candidate("../escape", "unbound", [10, 10, 30, 30])],
    )

    with pytest.raises(module.VisualFindingArtifactError, match="finding_id_invalid"):
        module.build_visual_finding_artifacts(fixture)

    assert not (fixture / "build" / "perception" / "escape.png").exists()


def test_compile_generates_artifacts_before_deferred_strict_exit() -> None:
    compile_sh = (REPO_ROOT / "scripts" / "compile.sh").read_text(encoding="utf-8")

    perception_call = compile_sh.index('python3 "$WORKFLOW_DIR/scripts/perception_pack.py"')
    artifact_call = compile_sh.index(
        'python3 "$WORKFLOW_DIR/scripts/visual_finding_artifacts.py"'
    )
    deferred_exit = compile_sh.index("STRICT_CHECK_FAILURE")
    assert perception_call < artifact_call
    assert deferred_exit < artifact_call
    assert "exit 1" in compile_sh[artifact_call:]
    assert '--artifact-base "$BASE"' in compile_sh[artifact_call:]


def test_perception_extract_declares_visual_finding_manifest_path() -> None:
    source = (REPO_ROOT / "scripts" / "perception_pack.py").read_text(encoding="utf-8")

    assert "visual_findings/manifest.json" in source
