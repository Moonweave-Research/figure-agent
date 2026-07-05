"""Create candidate sandbox manifests without touching source exports."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from hashlib import sha256
from pathlib import Path
from typing import Any

import candidate_contracts
import candidate_visual_eval
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.candidate-manifest.v1"
RESULT_SCHEMA = "figure-agent.candidate-render-result.v1"
ZERO_HASH = "sha256:" + "0" * 64
RENDER_MANIFEST_SCHEMA = "figure-agent.candidate-render-manifest.v1"


class CandidateRenderError(ValueError):
    """Raised when candidate rendering would escape the manifest sandbox."""


def _which(name: str) -> str | None:
    return shutil.which(name)


def _run_process(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )


def _source_commit(workspace_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=workspace_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _safe_candidate_id(value: Any) -> str:
    candidate_id = str(value)
    if not fixture_identity.is_safe_fixture_name(candidate_id):
        raise CandidateRenderError(f"invalid candidate_id: {candidate_id}")
    return candidate_id


def _safe_panel_id(value: str | None) -> str | None:
    if value is None:
        return None
    if not value or not all(char.isalnum() or char in {"_", "-"} for char in value):
        raise CandidateRenderError(f"invalid crop_panel: {value}")
    return value


def _sandbox_dir(example_dir: Path, candidate_id: str) -> Path:
    build_dir = example_dir / "build"
    if build_dir.is_symlink():
        raise CandidateRenderError("sandbox_symlink_forbidden: build")
    root = example_dir / "build" / "candidates"
    if root.is_symlink():
        raise CandidateRenderError("sandbox_symlink_forbidden: candidates")
    out_dir = root / candidate_id
    if out_dir.is_symlink():
        raise CandidateRenderError(f"sandbox_symlink_forbidden: {candidate_id}")
    try:
        out_dir.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise CandidateRenderError(f"candidate_id path_escape: {candidate_id}") from exc
    return out_dir


def _write_sandbox_file(path: Path, text: str) -> None:
    if path.parent.is_symlink():
        raise CandidateRenderError(f"sandbox_symlink_forbidden: {path.parent.name}")
    if path.is_symlink():
        raise CandidateRenderError(f"sandbox_symlink_forbidden: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sandbox_child_dir(out_dir: Path, name: str) -> Path:
    child = out_dir / name
    if child.is_symlink():
        raise CandidateRenderError(f"sandbox_symlink_forbidden: {name}")
    try:
        child.resolve().relative_to(out_dir.resolve())
    except ValueError as exc:
        raise CandidateRenderError(f"sandbox path_escape: {name}") from exc
    child.mkdir(parents=True, exist_ok=True)
    return child


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError as exc:
        raise CandidateRenderError("candidate artifact path_escape") from exc


def _fixture_path(example_dir: Path, fixture_name: str, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CandidateRenderError("operation path missing")
    path = Path(value)
    examples_prefix = ("examples", fixture_name)
    if path.parts[:2] == examples_prefix:
        path = Path(*path.parts[2:])
    return candidate_contracts.fixture_relative_path(example_dir, path.as_posix())


def _candidate_set_path_value(
    example_dir: Path,
    workspace_root: Path,
    candidate_set_path: Path | None,
) -> str:
    if candidate_set_path is None:
        return "build/candidates/candidate_set.json"
    if candidate_set_path.is_absolute():
        resolved = candidate_set_path.resolve()
    elif candidate_set_path.parts[:2] == (".scratch", "quality-search-runs"):
        resolved = (workspace_root / candidate_set_path).resolve()
    else:
        resolved = (example_dir / candidate_set_path).resolve()
    try:
        return resolved.relative_to(example_dir.resolve()).as_posix()
    except ValueError:
        scratch_root = (workspace_root / ".scratch" / "quality-search-runs").resolve()
        try:
            resolved.relative_to(scratch_root)
        except ValueError as exc:
            raise CandidateRenderError("candidate_set path_escape") from exc
        return resolved.relative_to(workspace_root.resolve()).as_posix()


def _candidate_source_text(
    example_dir: Path,
    fixture_name: str,
    candidate: dict[str, Any],
) -> tuple[str, str] | None:
    operations = candidate.get("operations")
    if not isinstance(operations, list):
        return None

    sources: dict[Path, str] = {}
    for operation in operations:
        if not isinstance(operation, dict) or operation.get("kind") != "replace_text":
            continue
        source_path = _fixture_path(example_dir, fixture_name, operation.get("path"))
        text = sources.get(source_path)
        if text is None:
            text = source_path.read_text(encoding="utf-8")
        original = str(operation.get("original", ""))
        replacement = str(operation.get("replacement", ""))
        try:
            line_start = int(operation["line_start"])
            line_end = int(operation.get("line_end", line_start))
        except (KeyError, TypeError, ValueError):
            line_start = 0
            line_end = 0
        if line_start > 0:
            lines = text.splitlines(keepends=True)
            if line_end < line_start or line_start > len(lines) or line_end > len(lines):
                raise CandidateRenderError(
                    f"operation original not found at lines {line_start}-{line_end}: "
                    f"{source_path.name}"
                )
            if line_end == line_start:
                if original not in lines[line_start - 1]:
                    raise CandidateRenderError(
                        f"operation original not found at line {line_start}: "
                        f"{source_path.name}"
                    )
                lines[line_start - 1] = lines[line_start - 1].replace(
                    original,
                    replacement,
                    1,
                )
            else:
                selected = "".join(lines[line_start - 1 : line_end])
                if selected != original:
                    raise CandidateRenderError(
                        f"operation original not found at lines {line_start}-{line_end}: "
                        f"{source_path.name}"
                    )
                lines[line_start - 1 : line_end] = [replacement]
            sources[source_path] = "".join(lines)
            continue
        if original not in text:
            raise CandidateRenderError(f"operation original not found: {source_path.name}")
        sources[source_path] = text.replace(original, replacement, 1)

    if not sources:
        return None
    if len(sources) > 1:
        raise CandidateRenderError("multiple source copies are not supported")
    source_path, text = next(iter(sources.items()))
    return source_path.name, text


def _operations_with_source_hashes(
    example_dir: Path,
    fixture_name: str,
    candidate: dict[str, Any],
) -> list[Any]:
    operations = candidate.get("operations")
    if not isinstance(operations, list):
        return []
    enriched: list[Any] = []
    for operation in operations:
        if not isinstance(operation, dict):
            enriched.append(operation)
            continue
        copied = dict(operation)
        if copied.get("kind") == "replace_text" and "source_sha256" not in copied:
            source_path = _fixture_path(example_dir, fixture_name, copied.get("path"))
            copied["source_sha256"] = _sha256_file(source_path)
        enriched.append(copied)
    return enriched


def _write_candidate_source_copy(
    *,
    example_dir: Path,
    fixture_name: str,
    candidate: dict[str, Any],
    out_dir: Path,
) -> list[dict[str, str]]:
    source_copy = _candidate_source_text(example_dir, fixture_name, candidate)
    if source_copy is None:
        return []
    filename, text = source_copy
    destination = out_dir / filename
    _write_sandbox_file(destination, text)
    return [{"kind": "candidate_source", "path": destination.name}]


def _renderable_tex_source(text: str) -> str:
    if "\\documentclass" in text or "\\begin{document}" in text:
        return text
    body = (
        text
        if "\\begin{tikzpicture}" in text
        else f"\\begin{{tikzpicture}}\n{text}\\end{{tikzpicture}}\n"
    )
    return (
        "\\documentclass[tikz,border=2pt]{standalone}\n"
        "\\usepackage{tikz}\n"
        "\\begin{document}\n"
        f"{body}"
        "\\end{document}\n"
    )


def _write_render_source_copy(
    *,
    example_dir: Path,
    fixture_name: str,
    candidate: dict[str, Any],
    out_dir: Path,
) -> str | None:
    source_copy = _candidate_source_text(example_dir, fixture_name, candidate)
    if source_copy is None:
        return None
    _filename, text = source_copy
    source_dir = _sandbox_child_dir(out_dir, "source")
    destination = source_dir / "candidate.tex"
    _write_sandbox_file(destination, _renderable_tex_source(text))
    return _fixture_relative(example_dir, destination)


def _render_manifest(
    *,
    example_dir: Path,
    fixture_name: str,
    candidate: dict[str, Any],
    candidate_id: str,
    out_dir: Path,
    candidate_set_path: str,
    source_copy: str | None,
    compile_requested: bool,
    export_requested: bool,
    crop_panel: str | None,
    evaluate_requested: bool,
    plugin_root: Path,
) -> dict[str, Any]:
    diagnostics: list[dict[str, str]] = []
    compile_status = "not_run"
    export_status = "not_run"
    crop_status = "not_run"
    evaluate_status = "not_run"
    tex_engine = "lualatex"
    render_dir = _sandbox_child_dir(out_dir, "render")
    crops_dir = _sandbox_child_dir(out_dir, "crops") if crop_panel else None
    if compile_requested:
        if _which(tex_engine) is None:
            compile_status = "dependency_missing"
            diagnostics.append(
                {
                    "stage": "compile",
                    "category": "dependency_missing",
                    "dependency": tex_engine,
                    "message": f"{tex_engine} not found",
                }
            )
        else:
            env = {
                **os.environ,
                "TEXINPUTS": (
                    f"{plugin_root / 'styles'}:"
                    f"{example_dir}:"
                    f"{out_dir / 'source'}:"
                    f"{os.environ.get('TEXINPUTS', '')}"
                ),
            }
            result = _run_process(
                [
                    tex_engine,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory=render",
                    "source/candidate.tex",
                ],
                cwd=out_dir,
                env=env,
            )
            compile_status = "success" if result.returncode == 0 else "failed"
            if result.returncode != 0:
                diagnostics.append(
                    {
                        "stage": "compile",
                        "category": "failed",
                        "dependency": tex_engine,
                        "message": "candidate TeX compile failed",
                    }
                )
    if export_requested and compile_status == "success":
        if _which("pdftocairo") is None:
            export_status = "dependency_missing"
            diagnostics.append(
                {
                    "stage": "export",
                    "category": "dependency_missing",
                    "dependency": "pdftocairo",
                    "message": "pdftocairo not found",
                }
            )
        else:
            result = _run_process(
                [
                    "pdftocairo",
                    "-png",
                    "-r",
                    "600",
                    "-singlefile",
                    "render/candidate.pdf",
                    "render/candidate",
                ],
                cwd=out_dir,
                env=os.environ.copy(),
            )
            export_status = "success" if result.returncode == 0 else "failed"
            if result.returncode != 0:
                diagnostics.append(
                    {
                        "stage": "export",
                        "category": "failed",
                        "dependency": "pdftocairo",
                        "message": "candidate PNG export failed",
                    }
                )
    if crop_panel and export_status == "success":
        original_png = example_dir / "build" / f"{fixture_name}.png"
        candidate_png = render_dir / "candidate.png"
        if crops_dir is None:
            raise CandidateRenderError("crop sandbox missing")
        before_crop = crops_dir / f"original_panel_{crop_panel}.png"
        after_crop = crops_dir / f"candidate_panel_{crop_panel}.png"
        if not original_png.is_file():
            crop_status = "blocked"
            diagnostics.append(
                {
                    "stage": "crop",
                    "category": "missing_original",
                    "dependency": "build_png",
                    "message": f"build/{fixture_name}.png not found",
                }
            )
        elif not candidate_png.is_file():
            crop_status = "blocked"
            diagnostics.append(
                {
                    "stage": "crop",
                    "category": "missing_candidate",
                    "dependency": "candidate_png",
                    "message": "candidate PNG not found",
                }
            )
        elif before_crop.is_symlink() or after_crop.is_symlink():
            raise CandidateRenderError("sandbox_symlink_forbidden: crop")
        else:
            shutil.copyfile(original_png, before_crop)
            shutil.copyfile(candidate_png, after_crop)
            crop_status = "success"
    visual_deltas: dict[str, Any] = {
        "pixel_diff_mean": None,
        "pixel_diff_max": None,
        "changed_pixel_ratio": None,
        "changed_bbox": None,
    }
    if evaluate_requested:
        if compile_status == "dependency_missing":
            evaluate_status = "dependency_missing"
        elif compile_status in {"failed", "not_run"}:
            evaluate_status = "blocked"
        elif crop_panel and crop_status != "success":
            evaluate_status = "blocked"
        elif crop_panel and crop_status == "success":
            before_crop = out_dir / "crops" / f"original_panel_{crop_panel}.png"
            after_crop = out_dir / "crops" / f"candidate_panel_{crop_panel}.png"
            try:
                comparison = candidate_visual_eval.compare_image_pair(before_crop, after_crop)
            except (OSError, ValueError) as exc:
                evaluate_status = "blocked"
                diagnostics.append(
                    {
                        "stage": "evaluate",
                        "category": "blocked",
                        "dependency": "image_compare",
                        "message": str(exc),
                    }
                )
            else:
                evaluate_status = str(comparison.get("status") or "blocked")
                if isinstance(comparison.get("visual_deltas"), dict):
                    visual_deltas = comparison["visual_deltas"]
                for diagnostic in comparison.get("diagnostics", []):
                    if isinstance(diagnostic, dict):
                        diagnostics.append(
                            {key: str(value) for key, value in diagnostic.items()}
                        )
        else:
            evaluate_status = "rendered_needs_human_review"
    before_crop_path = (
        out_dir / "crops" / f"original_panel_{crop_panel}.png"
        if crop_panel
        else None
    )
    after_crop_path = (
        out_dir / "crops" / f"candidate_panel_{crop_panel}.png"
        if crop_panel
        else None
    )
    artifacts = {
        "source_copy": source_copy,
        "pdf": _fixture_relative(example_dir, render_dir / "candidate.pdf")
        if (render_dir / "candidate.pdf").is_file()
        else None,
        "png": _fixture_relative(example_dir, render_dir / "candidate.png")
        if (render_dir / "candidate.png").is_file()
        else None,
        "before_crop": _fixture_relative(example_dir, before_crop_path)
        if before_crop_path is not None and before_crop_path.is_file()
        else None,
        "after_crop": _fixture_relative(example_dir, after_crop_path)
        if after_crop_path is not None and after_crop_path.is_file()
        else None,
    }
    return {
        "schema": RENDER_MANIFEST_SCHEMA,
        "schema_version": 1,
        "figure_name": fixture_name,
        "candidate_id": candidate_id,
        "candidate_hash": candidate.get("candidate_hash"),
        "candidate_set_path": candidate_set_path,
        "sandbox_path": _fixture_relative(example_dir, out_dir),
        "panel": (
            crop_panel
            or (
                candidate.get("target", {}).get("panel")
                if isinstance(candidate.get("target"), dict)
                else candidate.get("panel")
            )
        ),
        "stages": {
            "prepare": {"status": "success"},
            "compile": {"status": compile_status},
            "export": {"status": export_status},
            "crop": {"status": crop_status},
            "evaluate": {"status": evaluate_status},
        },
        "artifacts": artifacts,
        "visual_deltas": visual_deltas,
        "diagnostics": diagnostics,
        "human_review_required": True,
    }


def render_candidate_set(
    name: str,
    candidate_set: dict[str, Any],
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    candidate_set_path: Path | None = None,
    candidate_id: str | None = None,
    compile: bool = False,
    export: bool = False,
    crop_panel: str | None = None,
    evaluate: bool = False,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    crop_panel = _safe_panel_id(crop_panel)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    source_candidate_set_path = _candidate_set_path_value(
        example_dir,
        paths.workspace_root,
        candidate_set_path,
    )
    rendered: list[dict[str, Any]] = []
    for candidate in candidate_set.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        current_candidate_id = _safe_candidate_id(candidate.get("id"))
        if candidate_id is not None and current_candidate_id != _safe_candidate_id(candidate_id):
            continue
        out_dir = _sandbox_dir(example_dir, current_candidate_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        artifacts = _write_candidate_source_copy(
            example_dir=example_dir,
            fixture_name=name,
            candidate=candidate,
            out_dir=out_dir,
        )
        render_source_copy = None
        if compile or export or crop_panel or evaluate:
            render_source_copy = _write_render_source_copy(
                example_dir=example_dir,
                fixture_name=name,
                candidate=candidate,
                out_dir=out_dir,
            )
        hard_gate_state = "human_required"
        effective = candidate_contracts.effective_apply_authority(
            str(candidate.get("apply_authority")),
            hard_gate_state,
        )
        base = candidate_set.get("base") if isinstance(candidate_set.get("base"), dict) else {}
        operations = _operations_with_source_hashes(example_dir, name, candidate)
        manifest = {
            "schema": SCHEMA,
            "candidate_id": current_candidate_id,
            "candidate_hash": candidate.get("candidate_hash"),
            "fixture": name,
            "candidate_set_path": source_candidate_set_path,
            "edit_class": candidate.get("edit_class"),
            "edit_family": candidate.get("edit_family"),
            "family": candidate.get("family"),
            "operation_scale": candidate.get("operation_scale"),
            "template_id": candidate.get("template_id"),
            "expected_visual_movement": candidate.get("expected_visual_movement"),
            "variant_id": candidate.get("variant_id"),
            "variant": candidate.get("variant"),
            "panel": (
                candidate.get("target", {}).get("panel")
                if isinstance(candidate.get("target"), dict)
                else candidate.get("panel")
            ),
            "selectors": candidate.get("selectors", []),
            "base": {
                "source_commit": _source_commit(paths.workspace_root),
                "tex_hash": base.get("tex_hash", ZERO_HASH),
                "status_hash": base.get("status_hash", ZERO_HASH),
                "render_hash": ZERO_HASH,
            },
            "tool_versions": {
                "fig_agent": "0.11.x",
                "python": platform.python_version(),
                "tex_engine": "not_run",
            },
            "operations": operations,
            "artifacts": artifacts,
            "stages": {
                "prepare": "passed",
                "compile": "not_run",
                "export": "not_run",
                "crop": "not_run",
            },
            "visual_review": candidate.get(
                "visual_review",
                {
                    "status": "missing_render",
                    "reason": "candidate compile/export/crop has not run",
                },
            ),
            "verification": {
                "commands": candidate.get("verification", {}).get(
                    "required_commands",
                    [],
                ),
                "hard_gate_state": hard_gate_state,
            },
            "apply_authority": candidate.get("apply_authority"),
            "effective_apply_authority": effective,
            "risk": candidate.get("risk"),
            "expected_delta": candidate.get("expected_delta", []),
            "protected_labels": candidate.get("protected_labels", []),
            "design_moves": candidate.get("design_moves", []),
            "semantic_risks": candidate.get("semantic_risks", []),
            "boundedness": candidate.get("boundedness", {}),
            "rollback": candidate.get("rollback"),
        }
        if isinstance(candidate.get("source_defect"), dict):
            manifest["source_defect"] = candidate["source_defect"]
        path = out_dir / "candidate_manifest.json"
        _write_sandbox_file(
            path,
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        )
        rendered_item = {
            "candidate_id": current_candidate_id,
            "manifest": _fixture_relative(example_dir, path),
        }
        if compile or export or crop_panel or evaluate:
            render_manifest = _render_manifest(
                example_dir=example_dir,
                fixture_name=name,
                candidate=candidate,
                candidate_id=current_candidate_id,
                out_dir=out_dir,
                candidate_set_path=source_candidate_set_path,
                source_copy=render_source_copy,
                compile_requested=compile,
                export_requested=export,
                crop_panel=crop_panel,
                evaluate_requested=evaluate,
                plugin_root=paths.plugin_root,
            )
            render_manifest_path = out_dir / "render_manifest.json"
            _write_sandbox_file(
                render_manifest_path,
                json.dumps(render_manifest, indent=2, sort_keys=True) + "\n",
            )
            rendered_item["render_manifest"] = _fixture_relative(
                example_dir,
                render_manifest_path,
            )
        rendered.append(rendered_item)
    return {"schema": RESULT_SCHEMA, "fixture": name, "rendered": rendered}
