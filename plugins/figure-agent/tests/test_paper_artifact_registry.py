from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

CHECKS_DIR = Path(__file__).resolve().parents[1] / "scripts" / "checks"
sys.path.insert(0, str(CHECKS_DIR))
import check_paper_artifact_registry as registry_check  # noqa: E402

sys.path.remove(str(CHECKS_DIR))


def _write_registry(root: Path, figures: dict[str, object]) -> Path:
    path = root / "FIGURE_REGISTRY.yaml"
    path.write_text(
        yaml.safe_dump(
            {"schema": "researchos.figure-registry.v1", "figures": figures},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_registry_accepts_pinned_canonical_and_partial_artifacts(tmp_path: Path) -> None:
    canonical = tmp_path / "F01_overview.png"
    canonical.write_bytes(b"canonical")
    component = tmp_path / "F05_schematic.png"
    component.write_bytes(b"partial")
    registry = _write_registry(
        tmp_path,
        {
            "F01": {
                "lifecycle": "canonical",
                "paper_artifact": {
                    "png": {
                        "path": canonical.name,
                        "sha256": hashlib.sha256(canonical.read_bytes()).hexdigest(),
                    }
                },
            },
            "F05": {
                "lifecycle": "paper_partial",
                "paper_components": [
                    {
                        "id": "schematic",
                        "path": component.name,
                        "sha256": hashlib.sha256(component.read_bytes()).hexdigest(),
                    }
                ],
                "candidate_links": [{"fixture": "fig5", "lifecycle": "candidate"}],
            },
        },
    )

    report = registry_check.build_report(tmp_path, registry)

    assert report["state"] == "PASSED"
    assert len(report["verified"]) == 2


def test_registry_rejects_stale_hash_and_unbounded_candidate_link(tmp_path: Path) -> None:
    artifact = tmp_path / "F01_overview.png"
    artifact.write_bytes(b"canonical")
    registry = _write_registry(
        tmp_path,
        {
            "F01": {
                "lifecycle": "canonical",
                "paper_artifact": {"png": {"path": artifact.name, "sha256": "0" * 64}},
                "candidate_links": [{"fixture": "fig1", "lifecycle": "canonical"}],
            }
        },
    )

    report = registry_check.build_report(tmp_path, registry)

    assert report["state"] == "FAILED"
    assert {finding["code"] for finding in report["errors"]} == {
        "artifact_hash_mismatch",
        "invalid_candidate_link",
    }
