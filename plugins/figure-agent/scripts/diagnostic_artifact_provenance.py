"""Classify diagnostic images before treating them as figure evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from quality_manifest import file_sha256

SCHEMA = "figure-agent.diagnostic-artifact-provenance.v1"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _rel(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


def _artifact_path(example_dir: Path, artifact_path: Path) -> Path:
    if artifact_path.is_absolute():
        return artifact_path
    cwd_path = Path.cwd() / artifact_path
    if cwd_path.exists():
        return cwd_path
    example_path = example_dir / artifact_path
    if example_path.exists():
        return example_path
    return cwd_path


def _manifest_crops(example_dir: Path) -> dict[Path, dict[str, Any]]:
    manifest = _load_json(example_dir / "build" / "audit_crops" / "manifest.json")
    if manifest is None:
        return {}
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        return {}
    result: dict[Path, dict[str, Any]] = {}
    for crop in crops:
        if not isinstance(crop, dict):
            continue
        raw_path = crop.get("path")
        if not isinstance(raw_path, str):
            continue
        relative = Path(raw_path)
        if relative.is_absolute() or ".." in relative.parts:
            continue
        result[(example_dir / relative).resolve()] = crop
    return result


def _latest_build_render_mtime(example_dir: Path) -> float | None:
    candidates = (
        example_dir / "build" / f"{example_dir.name}.png",
        example_dir / "build" / f"{example_dir.name}.pdf",
    )
    mtimes = [path.stat().st_mtime for path in candidates if path.is_file()]
    return max(mtimes) if mtimes else None


def _is_build_render(example_dir: Path, path: Path) -> bool:
    return path.resolve() in {
        (example_dir / "build" / f"{example_dir.name}.png").resolve(),
        (example_dir / "build" / f"{example_dir.name}.pdf").resolve(),
    }


def classify_artifact(example_dir: Path, artifact_path: Path) -> dict[str, Any]:
    """Return whether a crop/image is authoritative plugin evidence."""

    example_dir = example_dir.resolve()
    path = _artifact_path(example_dir, artifact_path).resolve()
    base_dir = example_dir.parent.parent if example_dir.parent.name == "examples" else example_dir
    record: dict[str, Any] = {
        "path": _rel(path, base_dir),
        "example_relative_path": _rel(path, example_dir),
        "authoritative": False,
    }
    if not path.is_file():
        return {
            **record,
            "classification": "missing",
            "reason": "artifact path does not exist",
        }

    actual_hash = file_sha256(path)
    record["sha256"] = actual_hash

    manifest_crop = _manifest_crops(example_dir).get(path)
    if manifest_crop is not None:
        expected_hash = manifest_crop.get("sha256")
        record["manifest_crop_id"] = manifest_crop.get("id")
        record["manifest_expected_sha256"] = expected_hash
        if expected_hash == actual_hash:
            return {
                **record,
                "classification": "manifest_bound_current",
                "authoritative": True,
                "reason": "path is listed in build/audit_crops/manifest.json and hash matches",
            }
        return {
            **record,
            "classification": "stale_or_mismatched",
            "reason": "path is in audit manifest but file hash differs",
        }

    if _is_build_render(example_dir, path):
        return {
            **record,
            "classification": "build_render_current",
            "authoritative": True,
            "reason": (
                "path is the fixture build render artifact; render freshness still "
                "comes from /fig_status or critique_brief.py"
            ),
        }

    latest_build_mtime = _latest_build_render_mtime(example_dir)
    if latest_build_mtime is not None and path.stat().st_mtime < latest_build_mtime:
        return {
            **record,
            "classification": "stale_or_unbound",
            "reason": "diagnostic artifact is older than current build render",
        }

    return {
        **record,
        "classification": "diagnostic_only",
        "reason": "artifact is not manifest-bound; use only as diagnostic context",
    }


def provenance_report(example_dir: Path, artifact_paths: list[Path]) -> dict[str, Any]:
    artifacts = [classify_artifact(example_dir, path) for path in artifact_paths]
    authoritative_count = sum(1 for item in artifacts if item.get("authoritative") is True)
    diagnostic_count = len(artifacts) - authoritative_count
    return {
        "schema": SCHEMA,
        "fixture": example_dir.name,
        "example_dir": str(example_dir),
        "rule": (
            "Only current build renders and manifest-bound build/audit_crops entries "
            "are authoritative plugin truth. Render freshness still comes from "
            "/fig_status. Scratch or ad hoc crops are diagnostic-only."
        ),
        "authoritative_count": authoritative_count,
        "diagnostic_count": diagnostic_count,
        "artifacts": artifacts,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify diagnostic artifacts before using them as figure evidence."
    )
    parser.add_argument("fixture", help="fixture name or examples/<name> path")
    parser.add_argument("artifacts", nargs="+", help="artifact paths to classify")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="plugin root containing examples/",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    fixture = Path(args.fixture)
    example_dir = fixture if fixture.is_dir() else args.repo_root / "examples" / args.fixture
    report = provenance_report(example_dir, [Path(item) for item in args.artifacts])
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
