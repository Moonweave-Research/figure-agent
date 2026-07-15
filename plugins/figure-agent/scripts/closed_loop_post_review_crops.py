"""Deterministic crop-pack publication for closed-loop post-repair review."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

import critique_zoom_crops
from closed_loop_post_review_authority import (
    ClosedLoopPostReviewError,
    assert_render_unchanged,
    load_json,
)


def generate_generic_crop_staging(
    *,
    example_dir: Path,
    render: Path,
    render_bytes: bytes,
    render_sha256: str,
    render_fingerprint: tuple[int, int, int, int, int],
    staging_root: Path,
    review_root: Path,
) -> tuple[Path, list[dict[str, Any]]]:
    if staging_root.is_symlink():
        raise ClosedLoopPostReviewError("post_review_staging_symlink")
    if staging_root.exists():
        shutil.rmtree(staging_root)
    assert_render_unchanged(
        render,
        expected_sha256=render_sha256,
        expected_fingerprint=render_fingerprint,
    )
    staging_root.mkdir()
    render_snapshot = staging_root / "verified-render-snapshot.png"
    render_snapshot.write_bytes(render_bytes)
    staging_crops = staging_root / "crops"
    staging_manifest = staging_crops / "manifest.json"
    try:
        crops = critique_zoom_crops.build_zoom_crop_pack(
            example_dir,
            render_snapshot,
            panel_crop_paths=(),
            output_dir=staging_crops,
            manifest_path=staging_manifest,
            include_detector_crops=False,
        )
        manifest = load_json(staging_manifest, label="staged_crop_manifest")
        old_prefix = staging_crops.relative_to(example_dir).as_posix() + "/"
        new_prefix = (review_root / "crops").relative_to(example_dir).as_posix() + "/"
        for crop in manifest.get("crops", []):
            path = crop.get("path") if isinstance(crop, dict) else None
            if not isinstance(path, str) or not path.startswith(old_prefix):
                raise ClosedLoopPostReviewError("staged_crop_path_invalid")
            crop["path"] = new_prefix + path.removeprefix(old_prefix)
            crop["source_path"] = render.relative_to(example_dir).as_posix()
        manifest["render_path"] = render.relative_to(example_dir).as_posix()
        manifest["render_sha256"] = render_sha256
        staging_manifest.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        assert_render_unchanged(
            render,
            expected_sha256=render_sha256,
            expected_fingerprint=render_fingerprint,
        )
        render_snapshot.unlink()
        return staging_root, crops
    except Exception:
        if staging_root.is_dir() and not staging_root.is_symlink():
            shutil.rmtree(staging_root)
        raise


def publish_generic_crops(
    *,
    example_dir: Path,
    render: Path,
    render_bytes: bytes,
    render_sha256: str,
    render_fingerprint: tuple[int, int, int, int, int],
    attempt_root: Path,
    review_root: Path,
) -> list[dict[str, Any]]:
    staging_root, crops = generate_generic_crop_staging(
        example_dir=example_dir,
        render=render,
        render_bytes=render_bytes,
        render_sha256=render_sha256,
        render_fingerprint=render_fingerprint,
        staging_root=attempt_root / ".post-repair-review-staging",
        review_root=review_root,
    )
    try:
        if review_root.exists() or review_root.is_symlink():
            raise ClosedLoopPostReviewError("post_review_output_conflict")
        os.replace(staging_root, review_root)
        return crops
    except Exception:
        if staging_root.is_dir() and not staging_root.is_symlink():
            shutil.rmtree(staging_root)
        raise


def verify_existing_generic_crop_pack(
    *,
    example_dir: Path,
    render: Path,
    render_bytes: bytes,
    render_sha256: str,
    render_fingerprint: tuple[int, int, int, int, int],
    attempt_root: Path,
    review_root: Path,
) -> list[dict[str, Any]]:
    staging_root, crops = generate_generic_crop_staging(
        example_dir=example_dir,
        render=render,
        render_bytes=render_bytes,
        render_sha256=render_sha256,
        render_fingerprint=render_fingerprint,
        staging_root=attempt_root / ".post-repair-review-verify-staging",
        review_root=review_root,
    )
    expected_root = staging_root / "crops"
    actual_root = review_root / "crops"
    try:
        if actual_root.is_symlink() or not actual_root.is_dir():
            raise ClosedLoopPostReviewError("post_review_crop_pack_mismatch")
        expected_paths = {
            path.relative_to(expected_root)
            for path in expected_root.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        actual_paths = {
            path.relative_to(actual_root)
            for path in actual_root.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        if (
            expected_paths != actual_paths
            or any(path.is_symlink() for path in actual_root.rglob("*"))
            or any(
                (expected_root / relative).read_bytes()
                != (actual_root / relative).read_bytes()
                for relative in expected_paths
            )
        ):
            raise ClosedLoopPostReviewError("post_review_crop_pack_mismatch")
        return crops
    finally:
        if staging_root.is_dir() and not staging_root.is_symlink():
            shutil.rmtree(staging_root)
