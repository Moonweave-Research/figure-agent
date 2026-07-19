"""Read-only per-step artifact evidence for ``figure-agent.run.v1``."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import fixture_identity

SCHEMA = "figure-agent.step-execution-evidence.v1"

_COMPILE_REPORT_NAMES = frozenset(
    {
        "collisions.json",
        "convention_receipt.json",
        "convention_receipt.md",
        "label_hyphenation.json",
        "label_path_proximity.json",
        "layout_lanes.json",
        "physics_grounding.json",
        "semantic_assertions.json",
        "state_field_geometry.json",
        "strict_status.json",
        "text_boundary_clash.json",
        "tex_assertions.json",
        "undeclared_geometry.json",
        "vector_clearance.json",
        "visual_clash.json",
    }
)
_EXPORT_SUFFIX_ROLES = {
    ".pdf": "export_pdf",
    ".png": "export_png",
    ".svg": "export_svg",
    ".tif": "export_tiff",
}


@dataclass(frozen=True)
class _ArtifactSpec:
    role: str
    path: Path
    required_on_success: bool = False


@dataclass(frozen=True)
class StepCapture:
    repo_root: Path
    fixture: str
    action: str
    before: dict[str, tuple[int, str]]
    diagnostics: tuple[str, ...]
    loop_run_names: frozenset[str]


def begin_step_capture(
    repo_root: Path,
    *,
    fixture: str,
    action: str,
) -> StepCapture:
    """Capture allowlisted pre-step content fingerprints."""
    fixture_identity.validate_fixture_name(fixture)
    root = repo_root.resolve()
    diagnostics: list[str] = []
    before = (
        {}
        if action == "run_fig_loop"
        else _fingerprints(
            root,
            _artifact_specs(
                root,
                fixture=fixture,
                action=action,
                diagnostics=diagnostics,
            ),
            diagnostics=diagnostics,
        )
    )
    loop_run_names: frozenset[str] = frozenset()
    if action == "run_fig_loop":
        loop_run_names = _immediate_child_names(
            root / ".scratch" / "fig-loop-runs",
            root=root,
            diagnostics=diagnostics,
        )
    return StepCapture(
        repo_root=root,
        fixture=fixture,
        action=action,
        before=before,
        diagnostics=tuple(sorted(set(diagnostics))),
        loop_run_names=loop_run_names,
    )


def capture_internal_error_evidence(
    *,
    fixture: str,
    action: str,
    error_type: str,
) -> dict[str, object]:
    """Return a sanitized evidence envelope for a capture-boundary failure."""
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "action": action,
        "state": "captured_with_diagnostics",
        "artifacts": [],
        "diagnostics": [f"capture_internal_error:{error_type}"],
    }


def finish_step_capture(
    capture: StepCapture,
    *,
    returncode: int,
    loop_run_dir: Path | None = None,
) -> dict[str, object]:
    """Capture post-step evidence without changing the command result."""
    diagnostics = list(capture.diagnostics)
    specs = _artifact_specs(
        capture.repo_root,
        fixture=capture.fixture,
        action=capture.action,
        loop_run_dir=loop_run_dir,
        before_loop_run_names=capture.loop_run_names,
        diagnostics=diagnostics,
    )
    after = _fingerprints(
        capture.repo_root,
        specs,
        diagnostics=diagnostics,
    )
    artifacts = []
    roles = {_relative_path(capture.repo_root, spec.path): spec.role for spec in specs}
    required_paths = {
        _relative_path(capture.repo_root, spec.path)
        for spec in specs
        if spec.required_on_success
    }
    for path, (size_bytes, sha256) in after.items():
        before = capture.before.get(path)
        change = (
            "created"
            if before is None
            else ("unchanged" if before == (size_bytes, sha256) else "modified")
        )
        artifacts.append(
            {
                "role": roles[path],
                "path": path,
                "change": change,
                "size_bytes": size_bytes,
                "sha256": sha256,
            }
        )
    if returncode == 0:
        for path in sorted(required_paths - after.keys()):
            diagnostics.append(f"required_artifact_missing:{path}")
    normalized_diagnostics = sorted(set(diagnostics))
    return {
        "schema": SCHEMA,
        "fixture": capture.fixture,
        "action": capture.action,
        "state": (
            "captured_with_diagnostics" if normalized_diagnostics else "captured"
        ),
        "artifacts": sorted(artifacts, key=lambda item: (item["path"], item["role"])),
        "diagnostics": normalized_diagnostics,
    }


def _artifact_specs(
    root: Path,
    *,
    fixture: str,
    action: str,
    loop_run_dir: Path | None = None,
    before_loop_run_names: frozenset[str] = frozenset(),
    diagnostics: list[str] | None = None,
) -> list[_ArtifactSpec]:
    fixture_dir = root / "examples" / fixture
    if action == "run_compile":
        build_dir = fixture_dir / "build"
        specs = [
            _ArtifactSpec("render_pdf", build_dir / f"{fixture}.pdf", True),
            _ArtifactSpec("render_png", build_dir / f"{fixture}.png", True),
        ]
        specs.extend(
            _ArtifactSpec("compile_report", build_dir / name)
            for name in sorted(_COMPILE_REPORT_NAMES)
        )
        specs.extend(
            _compile_perception_specs(
                root,
                build_dir,
                diagnostics=diagnostics if diagnostics is not None else [],
            )
        )
        return specs
    if action == "run_adjudicate":
        return [
            _ArtifactSpec(
                "critique_adjudication",
                fixture_dir / "critique_adjudication.yaml",
                True,
            )
        ]
    if action == "run_export":
        return [
            _ArtifactSpec(
                role,
                fixture_dir / "exports" / f"{fixture}{suffix}",
                True,
            )
            for suffix, role in sorted(_EXPORT_SUFFIX_ROLES.items())
        ]
    if action == "run_fig_loop":
        run_dir = _resolve_loop_run_dir(
            root,
            fixture=fixture,
            supplied=loop_run_dir,
            before_names=before_loop_run_names,
            diagnostics=diagnostics if diagnostics is not None else [],
        )
        return (
            []
            if run_dir is None
            else _loop_run_specs(
                root,
                run_dir,
                diagnostics=diagnostics if diagnostics is not None else [],
            )
        )
    return []


def _compile_perception_specs(
    root: Path,
    build_dir: Path,
    *,
    diagnostics: list[str],
) -> list[_ArtifactSpec]:
    perception_dir = build_dir / "perception"
    specs = [
        _ArtifactSpec("perception_extract", perception_dir / "extract.yaml"),
        _ArtifactSpec("perception_overlay", perception_dir / "overlay.png"),
    ]
    specs.extend(
        _ArtifactSpec("visual_finding_artifact", path)
        for path in _walk_regular_candidates(
            perception_dir / "visual_findings",
            root=root,
            allowed_suffixes=frozenset({".json", ".png"}),
            diagnostics=diagnostics,
        )
    )
    return specs


def _loop_run_specs(
    root: Path,
    run_dir: Path,
    *,
    diagnostics: list[str],
) -> list[_ArtifactSpec]:
    specs = [
        _ArtifactSpec("fig_loop_decision", run_dir / "decision.md", True),
        _ArtifactSpec("fig_loop_iteration", run_dir / "iteration_001.json", True),
        _ArtifactSpec("fig_loop_manifest", run_dir / "run_manifest.json", True),
        _ArtifactSpec("fig_loop_stop_report", run_dir / "stop_report.json", True),
    ]
    for path in _walk_regular_candidates(
        run_dir,
        root=root,
        allowed_suffixes=frozenset({".json", ".log", ".md", ".txt"}),
        diagnostics=diagnostics,
    ):
        if path in {spec.path for spec in specs}:
            continue
        relative = path.relative_to(run_dir)
        if (
            len(relative.parts) == 1
            and relative.name.startswith("iteration_")
            and relative.suffix == ".json"
        ):
            role = "fig_loop_iteration"
        elif (
            len(relative.parts) == 1
            and relative.name.startswith("patch_apply_")
            and relative.suffix == ".json"
        ):
            role = "fig_loop_patch_record"
        elif relative.parts[0] == "command_logs" and relative.suffix == ".log":
            role = "fig_loop_command_log"
        else:
            continue
        specs.append(_ArtifactSpec(role, path))
    return specs


def _resolve_loop_run_dir(
    root: Path,
    *,
    fixture: str,
    supplied: Path | None,
    before_names: frozenset[str],
    diagnostics: list[str],
) -> Path | None:
    runs_root = root / ".scratch" / "fig-loop-runs"
    candidates: list[Path]
    if supplied is not None:
        try:
            supplied_relative = supplied.relative_to(runs_root)
        except ValueError:
            diagnostics.append("fig_loop_run_outside_allowlist")
            return None
        if (
            not supplied_relative.parts
            or any(part in {".", ".."} for part in supplied_relative.parts)
            or supplied.parent != runs_root
            or not _safe_loop_run_basename(supplied.name)
        ):
            diagnostics.append("fig_loop_run_not_immediate_child")
            return None
        candidates = [supplied]
    else:
        after_names = _immediate_child_names(
            runs_root,
            root=root,
            diagnostics=diagnostics,
        )
        candidates = [runs_root / name for name in sorted(after_names - before_names)]
    matching = [
        path
        for path in candidates
        if _valid_loop_run_dir(root, runs_root, path, fixture=fixture, diagnostics=diagnostics)
    ]
    if len(matching) == 1:
        return matching[0]
    diagnostics.append(
        "fig_loop_run_missing" if not matching else "fig_loop_run_ambiguous"
    )
    return None


def _valid_loop_run_dir(
    root: Path,
    runs_root: Path,
    path: Path,
    *,
    fixture: str,
    diagnostics: list[str],
) -> bool:
    try:
        relative = path.relative_to(runs_root)
    except ValueError:
        diagnostics.append("fig_loop_run_outside_allowlist")
        return False
    if len(relative.parts) != 1:
        diagnostics.append("fig_loop_run_not_immediate_child")
        return False
    if not _safe_path_components(
        root,
        path,
        include_path=False,
        diagnostics=diagnostics,
    ):
        return False
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return False
    except OSError:
        diagnostics.append(
            f"artifact_lstat_failed:{_relative_path(root, path)}"
        )
        return False
    if stat.S_ISLNK(mode):
        diagnostics.append(f"artifact_symlink_ignored:{_relative_path(root, path)}")
        return False
    if not stat.S_ISDIR(mode):
        return False
    manifest = path / "run_manifest.json"
    try:
        manifest_mode = manifest.lstat().st_mode
        if not stat.S_ISREG(manifest_mode):
            return False
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        diagnostics.append(
            f"fig_loop_manifest_unreadable:{_relative_path(root, manifest)}"
        )
        return False
    return isinstance(payload, dict) and payload.get("fixture") == fixture


def _immediate_child_names(
    directory: Path,
    *,
    root: Path,
    diagnostics: list[str],
) -> frozenset[str]:
    if not _safe_path_components(
        root,
        directory,
        include_path=True,
        diagnostics=diagnostics,
    ):
        return frozenset()
    try:
        with os.scandir(directory) as entries:
            return frozenset(entry.name for entry in entries)
    except FileNotFoundError:
        return frozenset()
    except OSError:
        diagnostics.append(
            f"artifact_directory_scan_failed:{_relative_path(root, directory)}"
        )
        return frozenset()


def _walk_regular_candidates(
    directory: Path,
    *,
    root: Path,
    allowed_suffixes: frozenset[str],
    diagnostics: list[str],
) -> list[Path]:
    found: list[Path] = []
    pending = [directory]
    while pending:
        current = pending.pop()
        if not _safe_path_components(
            root,
            current,
            include_path=True,
            diagnostics=diagnostics,
        ):
            continue
        try:
            with os.scandir(current) as entries:
                children = sorted(entries, key=lambda entry: entry.name, reverse=True)
        except (FileNotFoundError, NotADirectoryError):
            continue
        except OSError:
            diagnostics.append(
                f"artifact_directory_scan_failed:{_relative_path(root, current)}"
            )
            continue
        for entry in children:
            path = Path(entry.path)
            try:
                is_symlink = entry.is_symlink()
                is_directory = entry.is_dir(follow_symlinks=False)
                is_file = entry.is_file(follow_symlinks=False)
            except OSError:
                diagnostics.append(
                    f"artifact_lstat_failed:{_relative_path(root, path)}"
                )
                continue
            if is_symlink:
                diagnostics.append(
                    f"artifact_symlink_ignored:{_relative_path(root, path)}"
                )
                continue
            if is_directory:
                pending.append(path)
            elif (
                is_file
                and path.suffix in allowed_suffixes
                and _is_within(root, path)
            ):
                found.append(path)
    return sorted(found)


def _fingerprints(
    root: Path,
    specs: Iterable[_ArtifactSpec],
    *,
    diagnostics: list[str],
) -> dict[str, tuple[int, str]]:
    fingerprints: dict[str, tuple[int, str]] = {}
    for spec in specs:
        relative = _relative_path(root, spec.path)
        if not _safe_path_components(
            root,
            spec.path,
            include_path=False,
            diagnostics=diagnostics,
        ):
            continue
        try:
            mode = spec.path.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError:
            diagnostics.append(f"artifact_lstat_failed:{relative}")
            continue
        if stat.S_ISLNK(mode):
            diagnostics.append(f"artifact_symlink_ignored:{relative}")
            continue
        if not stat.S_ISREG(mode):
            continue
        try:
            digest = hashlib.sha256()
            size_bytes = 0
            with spec.path.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    size_bytes += len(chunk)
                    digest.update(chunk)
        except OSError:
            diagnostics.append(f"artifact_read_failed:{relative}")
            continue
        fingerprints[relative] = (size_bytes, digest.hexdigest())
    return fingerprints


def _relative_path(root: Path, path: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError("execution evidence path is outside repository") from exc
    if ".." in relative.parts:
        raise ValueError("execution evidence path contains parent traversal")
    return relative.as_posix()


def _safe_loop_run_basename(name: str) -> bool:
    return (
        bool(name)
        and bool(name.strip())
        and name not in {".", ".."}
        and "/" not in name
        and "\\" not in name
    )


def _safe_path_components(
    root: Path,
    path: Path,
    *,
    include_path: bool,
    diagnostics: list[str],
) -> bool:
    relative = Path(_relative_path(root, path))
    parts = relative.parts if include_path else relative.parts[:-1]
    current = root
    for part in parts:
        current /= part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return True
        except OSError:
            diagnostics.append(
                f"artifact_lstat_failed:{_relative_path(root, current)}"
            )
            return False
        if stat.S_ISLNK(mode):
            diagnostics.append(
                f"artifact_symlink_ignored:{_relative_path(root, current)}"
            )
            return False
    return True


def _is_within(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
