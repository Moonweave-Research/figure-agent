"""Evidence-gated candidate source apply."""

from __future__ import annotations

import difflib
import json
import os
import subprocess
import sys
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any

import candidate_contracts
import fixture_identity
import runtime_paths
import semantic_candidate_review

SCHEMA = "figure-agent.candidate-apply-result.v1"
TERMINAL_APPLY_STATUSES = {
    "applied",
    "applied_unverified",
    "applied_with_failed_verification",
}


class CandidateApplyError(ValueError):
    """Raised when candidate apply would escape the fixture boundary."""


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _diagnostic(code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"code": code, "message": message}
    if path is not None:
        payload["path"] = path
    return payload


def _blocked(name: str, candidate_id: str, diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "figure_name": name,
        "candidate_id": candidate_id,
        "status": "blocked",
        "changed_files": [],
        "rollback_patch": None,
        "post_apply": {},
        "diagnostics": diagnostics,
    }


def _candidate_id(manifest: dict[str, Any]) -> str:
    candidate_id = str(manifest.get("candidate_id") or "")
    fixture_identity.validate_fixture_name(candidate_id)
    return candidate_id


def _candidate_sandbox(example_dir: Path, candidate_id: str) -> Path:
    build_dir = example_dir / "build"
    root = build_dir / "candidates"
    sandbox = root / candidate_id
    for label, path in (("build", build_dir), ("candidates", root), (candidate_id, sandbox)):
        if path.is_symlink():
            raise CandidateApplyError(f"sandbox_symlink_forbidden: {label}")
    try:
        sandbox.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise CandidateApplyError("candidate path_escape") from exc
    return sandbox


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise CandidateApplyError(f"sandbox_symlink_forbidden: {path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CandidateApplyError(f"{label}_missing") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidateApplyError(f"{label}_unreadable") from exc
    if not isinstance(payload, dict):
        raise CandidateApplyError(f"{label}_invalid")
    return payload


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError as exc:
        raise CandidateApplyError("path_escape") from exc


def _operation_path(example_dir: Path, fixture_name: str, operation: dict[str, Any]) -> Path:
    value = operation.get("path")
    if not isinstance(value, str) or not value.strip():
        raise CandidateApplyError("operation_path_missing")
    path = Path(value)
    if path.parts[:2] == ("examples", fixture_name):
        path = Path(*path.parts[2:])
    target = example_dir / path
    if target.is_symlink():
        raise CandidateApplyError("source_symlink_forbidden")
    try:
        target.resolve().relative_to(example_dir.resolve())
    except ValueError as exc:
        raise CandidateApplyError("source_path_escape") from exc
    return target


def _drift_hash_for_operation(operation: dict[str, Any], selectors: Any) -> str | None:
    direct = operation.get("source_sha256")
    if isinstance(direct, str) and direct.startswith("sha256:"):
        return direct
    path = operation.get("path")
    if not isinstance(selectors, list):
        return None
    matches = [
        selector
        for selector in selectors
        if isinstance(selector, dict)
        and selector.get("kind") == "tex_selector.v1"
        and selector.get("path") == path
        and isinstance(selector.get("source_hash"), str)
    ]
    if len(matches) == 1:
        return str(matches[0]["source_hash"])
    return None


def _render_gate_failures(render_manifest: dict[str, Any]) -> list[str]:
    stages = (
        render_manifest.get("stages") if isinstance(render_manifest.get("stages"), dict) else {}
    )
    required = {
        "compile": "success",
        "export": "success",
        "crop": "success",
        "evaluate": "rendered_needs_human_review",
    }
    failures: list[str] = []
    for stage, expected in required.items():
        value = stages.get(stage)
        status = value.get("status") if isinstance(value, dict) else None
        if status != expected:
            failures.append(f"{stage}:{status or 'missing'}")
    return failures


def _active_mutation_lock(example_dir: Path) -> Path | None:
    for relative in (Path("build") / ".quality-locks" / "mutation.lock",):
        lock = example_dir / relative
        if lock.exists():
            return lock
    return None


@contextmanager
def _candidate_apply_lock(example_dir: Path) -> Iterator[Path | None]:
    lock_dir = example_dir / "build" / ".mcp-locks"
    if lock_dir.is_symlink():
        raise CandidateApplyError("sandbox_symlink_forbidden: .mcp-locks")
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "mutation.lock"
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        yield lock_path
        return
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write('{"operation":"apply_candidate"}\n')
        yield None
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _acceptance_hash_diagnostics(
    *,
    acceptance: dict[str, Any],
    candidate_id: str,
    manifest_path: Path,
    render_manifest_path: Path,
    manifest: dict[str, Any],
    render_manifest: dict[str, Any],
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if acceptance.get("schema") != "figure-agent.candidate-acceptance.v1":
        diagnostics.append(
            _diagnostic(
                "acceptance_schema_invalid",
                "acceptance schema is not candidate acceptance",
            )
        )
    if acceptance.get("decision") != "accept":
        diagnostics.append(
            _diagnostic("acceptance_not_accepted", "acceptance decision is not accept")
        )
    if acceptance.get("candidate_id") != candidate_id:
        diagnostics.append(_diagnostic("candidate_id_mismatch", "acceptance candidate mismatch"))
    if acceptance.get("candidate_hash") != manifest.get("candidate_hash"):
        diagnostics.append(
            _diagnostic("candidate_hash_mismatch", "acceptance candidate hash mismatch")
        )
    if manifest.get("candidate_hash") != render_manifest.get("candidate_hash"):
        diagnostics.append(
            _diagnostic("render_candidate_hash_mismatch", "render candidate hash mismatch")
        )
    if acceptance.get("candidate_manifest_sha256") != _sha256_file(manifest_path):
        diagnostics.append(
            _diagnostic(
                "candidate_manifest_hash_mismatch",
                "candidate manifest hash mismatch",
            )
        )
    if acceptance.get("render_manifest_sha256") != _sha256_file(render_manifest_path):
        diagnostics.append(
            _diagnostic("render_manifest_hash_mismatch", "render manifest hash mismatch")
        )
    return diagnostics


def _build_changes(
    *,
    example_dir: Path,
    fixture_name: str,
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    operations = manifest.get("operations")
    if not isinstance(operations, list):
        return [], [_diagnostic("operations_missing", "candidate operations are missing")]
    if not operations:
        return [], [_diagnostic("operations_empty", "candidate operations are empty")]
    diagnostics: list[dict[str, str]] = []
    by_path: dict[Path, dict[str, Any]] = {}
    for operation in operations:
        if not isinstance(operation, dict) or operation.get("kind") != "replace_text":
            diagnostics.append(
                _diagnostic("unsupported_operation", "only replace_text is supported")
            )
            continue
        target = _operation_path(example_dir, fixture_name, operation)
        relative = target.relative_to(example_dir).as_posix()
        drift_hash = _drift_hash_for_operation(operation, manifest.get("selectors"))
        if drift_hash is None:
            diagnostics.append(
                _diagnostic("source_drift_hash_missing", "source drift hash missing", relative)
            )
            continue
        if _sha256_file(target) != drift_hash:
            diagnostics.append(
                _diagnostic("source_drift_hash_mismatch", "source drift hash mismatch", relative)
            )
            continue
        text = target.read_text(encoding="utf-8")
        original = str(operation.get("original", ""))
        replacement = str(operation.get("replacement", ""))
        if text.count(original) != 1:
            diagnostics.append(
                _diagnostic(
                    "original_text_count",
                    "original text must appear exactly once",
                    relative,
                )
            )
            continue
        entry = by_path.setdefault(
            target,
            {
                "path": target,
                "relative": relative,
                "before": text,
                "after": text,
            },
        )
        entry["after"] = str(entry["after"]).replace(original, replacement, 1)
    return list(by_path.values()), diagnostics


def _rollback_patch(changes: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for change in changes:
        relative = str(change["relative"])
        chunks.extend(
            difflib.unified_diff(
                str(change["after"]).splitlines(keepends=True),
                str(change["before"]).splitlines(keepends=True),
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
            )
        )
    return "".join(chunks)


def _output_tail(text: str, limit: int = 1200) -> str:
    return text[-limit:] if len(text) > limit else text


def _post_apply_env(paths: runtime_paths.RuntimePaths) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(paths.plugin_root)
    env["FIGURE_AGENT_WORKSPACE"] = str(paths.workspace_root)
    script_import_dirs = (
        paths.scripts_dir,
        paths.scripts_dir / "checks",
        paths.scripts_dir / "candidates",
        paths.scripts_dir / "quality",
        paths.scripts_dir / "loop",
        paths.scripts_dir / "driver",
    )
    import_path = os.pathsep.join(str(path) for path in script_import_dirs)
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{import_path}{os.pathsep}{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = import_path
    return env


def _post_apply_checks(name: str, paths: runtime_paths.RuntimePaths) -> dict[str, dict[str, Any]]:
    env = _post_apply_env(paths)
    commands = {
        "compile": [
            "bash",
            str(paths.scripts_dir / "compile.sh"),
            str(paths.examples_dir / name / f"{name}.tex"),
        ],
        "export": [
            sys.executable,
            str(paths.scripts_dir / "run_export.py"),
            name,
            "--skip-critique",
        ],
        "status": [
            sys.executable,
            str(paths.scripts_dir / "status.py"),
            name,
            "--json",
        ],
    }
    checks: dict[str, dict[str, Any]] = {}
    for stage, command in commands.items():
        completed = subprocess.run(
            command,
            cwd=paths.workspace_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        checks[stage] = {
            "status": "success" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "stdout_tail": _output_tail(completed.stdout),
            "stderr_tail": _output_tail(completed.stderr),
        }
    return checks


def _required_post_apply_commands(name: str) -> list[str]:
    return [
        f"/fig_compile {name}",
        f"/fig_export {name} --skip-critique",
        f"/fig_status {name} --json",
    ]


# Severity ordering for the semantic recheck (lower rank == higher severity).
_SEVERITY_RANK = {"blocker": 0, "major": 1, "action": 2, "info": 3}


def _severity_rank(severity: Any) -> int:
    return _SEVERITY_RANK.get(str(severity or "").lower(), 99)


def _defect_signature(defect: dict[str, Any]) -> tuple[str, str, str]:
    target = defect.get("target") if isinstance(defect.get("target"), dict) else {}
    panel = str(target.get("panel") or "unknown")
    defect_class = str(defect.get("defect_class") or "")
    severity = str(defect.get("severity") or "")
    return (panel, defect_class, severity)


def _defect_anchor(defect: dict[str, Any]) -> str:
    """A stable, nudge-invariant discriminator for a defect's target element: the
    node text from selector_hint. It tells two same-signature labels apart, and a
    coordinate nudge does not change it (unlike the coordinate-derived subregion)."""
    hint = defect.get("selector_hint")
    if isinstance(hint, dict):
        value = hint.get("value")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _defect_identity(defect: dict[str, Any]) -> tuple[str, str, str]:
    """Per-instance identity: (panel, defect_class, anchor). Severity is DELIBERATELY
    excluded so a mere severity downgrade of the same element still matches (it is
    not a resolution), while the anchor tells same-signature instances apart — the
    two ways the old count-only recheck credited an unresolved defect as fixed."""
    target = defect.get("target") if isinstance(defect.get("target"), dict) else {}
    panel = str(target.get("panel") or "unknown")
    defect_class = str(defect.get("defect_class") or "")
    return (panel, defect_class, _defect_anchor(defect))


def _semantic_recheck_verdict(
    source_defect_id: str,
    pre_defects: list[dict[str, Any]],
    post_defects: list[dict[str, Any]],
) -> dict[str, Any]:
    """Semantic recheck: decide whether the applied edit actually resolved the
    target defect WITHOUT introducing an equal-or-higher-severity defect.

    Robust to coordinate nudges: it compares (panel, defect_class, severity)
    multiset counts, never a line-content hash (fingerprint / sel: key), which a
    nudge shifts even when the defect persists — the gap the old fingerprint-
    equality recheck left open.
    """
    source = next(
        (
            defect
            for defect in pre_defects
            if isinstance(defect, dict) and str(defect.get("id") or "") == source_defect_id
        ),
        None,
    )
    if source is None:
        return {
            "status": "failed",
            "reason": "source_defect_absent_pre_apply",
            "source_defect_id": source_defect_id,
        }
    source_sig = _defect_signature(source)
    source_identity = _defect_identity(source)
    source_rank = _severity_rank(source.get("severity"))
    # Is the SPECIFIC target defect still present? Match by per-instance identity
    # (panel, class, anchor) — severity-free — so that resolving a same-signature
    # SIBLING (which only drops the count) or merely DOWNGRADING the target (which
    # only changes its severity) is not miscredited as a resolution.
    pre_identities = Counter(_defect_identity(d) for d in pre_defects if isinstance(d, dict))
    post_identities = Counter(_defect_identity(d) for d in post_defects if isinstance(d, dict))
    if post_identities[source_identity] >= pre_identities[source_identity]:
        return {
            "status": "failed",
            "reason": "source_defect_unresolved",
            "source_defect_id": source_defect_id,
            "identity": list(source_identity),
            "signature": list(source_sig),
        }
    # Did the edit introduce an equal-or-higher-severity defect anywhere?
    pre_counts = Counter(_defect_signature(d) for d in pre_defects if isinstance(d, dict))
    post_counts = Counter(_defect_signature(d) for d in post_defects if isinstance(d, dict))
    for sig, post_n in post_counts.items():
        if _severity_rank(sig[2]) <= source_rank and post_n > pre_counts.get(sig, 0):
            return {
                "status": "failed",
                "reason": "new_defect_introduced",
                "source_defect_id": source_defect_id,
                "introduced_signature": list(sig),
            }
    return {
        "status": "success",
        "reason": "source_defect_resolved",
        "source_defect_id": source_defect_id,
        "identity": list(source_identity),
        "signature": list(source_sig),
    }


def _finding_recheck_verdict(
    target_texts: list[Any],
    post_crossing_texts: list[Any],
    pre_crossing_texts: list[Any] | None = None,
) -> dict[str, Any]:
    """Recheck for a finding-sourced (visual_clash-grounded) fix.

    The quality_defect_ledger is undeclared_geometry-grounded and blind to the
    visual_clash crossings a critique finding catches, so a finding-sourced fix
    cannot be verified by the ledger-based semantic recheck. Instead verify
    against the post-apply crossing texts: the fix is resolved iff none of the
    texts the finding targeted are still flagged as crossings AND it introduced
    no NEW crossing (a destination-unaware move can clear the target yet push the
    label onto another element). New crossings need pre_crossing_texts to tell an
    edit-introduced crossing from a stable baseline false-positive.
    """
    targets = {str(text) for text in target_texts}
    post = {str(text) for text in post_crossing_texts}
    unresolved = sorted(targets & post)
    if unresolved:
        return {
            "status": "failed",
            "reason": "finding_crossing_unresolved",
            "unresolved_texts": unresolved,
        }
    if pre_crossing_texts is not None:
        introduced = sorted(post - {str(text) for text in pre_crossing_texts})
        if introduced:
            return {
                "status": "failed",
                "reason": "finding_new_crossing_introduced",
                "introduced_texts": introduced,
            }
    return {
        "status": "success",
        "reason": "finding_crossing_resolved",
        "resolved_texts": sorted(targets),
    }


def _post_crossing_texts(example_dir: Path) -> list[str]:
    """Texts flagged by the post-apply visual_clash detector — the crossings a
    critique finding is grounded in (the ledger is blind to this defect class)."""
    report = example_dir / "build" / "visual_clash.json"
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        return []
    return [
        str(candidate.get("text"))
        for candidate in candidates
        if isinstance(candidate, dict) and candidate.get("text")
    ]


def _post_apply_semantic_recheck(
    name: str,
    paths: runtime_paths.RuntimePaths,
    manifest: dict[str, Any],
    pre_defects: list[dict[str, Any]],
    pre_crossing_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    source_defect = manifest.get("source_defect")
    if not isinstance(source_defect, dict):
        return None
    source_defect_id = source_defect.get("id")
    if not isinstance(source_defect_id, str) or not source_defect_id.strip():
        return None
    if source_defect.get("source") == "adjudicated_finding":
        # Finding-sourced fixes are visual_clash-grounded; the ledger (and the
        # ledger-based recheck) is blind to them. Verify against the post-apply
        # crossing texts instead. No target_texts => cannot verify => fail-safe.
        target_texts = source_defect.get("target_texts")
        if not isinstance(target_texts, list) or not target_texts:
            return {
                "status": "failed",
                "reason": "finding_target_texts_missing",
                "source_defect_id": source_defect_id,
            }
        return _finding_recheck_verdict(
            target_texts,
            _post_crossing_texts(paths.examples_dir / name),
            pre_crossing_texts=pre_crossing_texts,
        )
    import quality_defect_ledger

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        name,
        plugin_root=paths.plugin_root,
        workspace_root=paths.workspace_root,
    )
    post_defects = ledger.get("defects")
    if not isinstance(post_defects, list):
        return {
            "status": "failed",
            "reason": "quality_defect_ledger_missing",
            "source_defect_id": source_defect_id,
        }
    return _semantic_recheck_verdict(source_defect_id, pre_defects, post_defects)


def _pre_apply_defects(name: str, paths: runtime_paths.RuntimePaths) -> list[dict[str, Any]]:
    """Snapshot the ledger defects BEFORE mutation so the post-apply semantic
    recheck can diff against them. Returns [] if the ledger is unavailable (the
    recheck then reports source_defect_absent_pre_apply = failed verification)."""
    import quality_defect_ledger

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        name,
        plugin_root=paths.plugin_root,
        workspace_root=paths.workspace_root,
    )
    defects = ledger.get("defects")
    return defects if isinstance(defects, list) else []


def _pdf_words(pdf_path: Path) -> Counter:
    if not pdf_path.is_file():
        return Counter()
    completed = subprocess.run(
        ["pdftotext", "-q", str(pdf_path), "-"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return Counter()
    return Counter(completed.stdout.split())


def _compile_current_source(
    name: str,
    paths: runtime_paths.RuntimePaths,
) -> subprocess.CompletedProcess[str]:
    """Force a compile of the CURRENT (unmutated) source to (re)create
    build/<name>.pdf, so the value-preservation gate has a pre-mutation label
    baseline. Best-effort: if it fails, the baseline stays absent and the gate
    fails closed (M3)."""
    return subprocess.run(
        [
            "bash",
            str(paths.scripts_dir / "compile.sh"),
            str(paths.examples_dir / name / f"{name}.tex"),
        ],
        cwd=paths.workspace_root,
        env=_post_apply_env(paths),
        text=True,
        capture_output=True,
        check=False,
    )


def _rollback_compile_status(
    name: str,
    paths: runtime_paths.RuntimePaths,
    build_pdf: Path,
) -> dict[str, Any]:
    try:
        completed = _compile_current_source(name, paths)
    except Exception as exc:
        if build_pdf.exists():
            build_pdf.unlink()
        return {"status": "failed", "reason": str(exc)}

    returncode = getattr(completed, "returncode", 0)
    if returncode != 0 or not build_pdf.is_file():
        if build_pdf.exists():
            build_pdf.unlink()
        return {
            "status": "failed",
            "returncode": returncode,
            "stdout_tail": _output_tail(getattr(completed, "stdout", "") or ""),
            "stderr_tail": _output_tail(getattr(completed, "stderr", "") or ""),
        }
    return {
        "status": "success",
        "returncode": returncode,
        "stdout_tail": _output_tail(getattr(completed, "stdout", "") or ""),
        "stderr_tail": _output_tail(getattr(completed, "stderr", "") or ""),
    }


def _verify_labels_unchanged(pre_words: Counter, post_words: Counter) -> tuple[bool, str]:
    # No baseline (pre-mutation PDF absent / unreadable) => value-preservation is
    # unverifiable, so FAIL CLOSED (M3). The caller forces a pre-mutation compile
    # before snapshotting so a legitimate apply is not blocked for a missing render.
    if not pre_words:
        return (False, "no_label_baseline")
    if pre_words == post_words:
        return (True, "labels_unchanged")
    return (False, "labels_changed")


def _verify_palette_locked(tex_path: Path) -> tuple[bool, str]:
    import lint_tex

    blockers = [v for v in lint_tex.lint(tex_path) if v.severity == "blocker"]
    if not blockers:
        return (True, "palette_locked")
    return (False, f"palette_violation:{blockers[0].category}")


# Value-preservation verifiers every applied edit must pass, by edit class.
# A value-preserving edit may change a presentation attribute (a coordinate, a
# stroke width, a fill style) but must NOT change the rendered science text
# (labels_unchanged) or break Style-Lock palette/font discipline (palette_locked).
CLASS_VERIFIERS: dict[str, tuple[str, ...]] = {
    "_default": ("labels_unchanged", "palette_locked"),
}


def _verifier_keys(edit_class: str) -> tuple[str, ...]:
    return CLASS_VERIFIERS.get(edit_class, CLASS_VERIFIERS["_default"])


def _run_class_verifiers(
    changes: list[dict[str, Any]],
    pre_words: Counter,
    post_words: Counter,
) -> dict[str, Any]:
    results: list[dict[str, str]] = []
    ok_all = True
    for key in CLASS_VERIFIERS["_default"]:
        if key == "labels_unchanged":
            ok, reason = _verify_labels_unchanged(pre_words, post_words)
        elif key == "palette_locked":
            ok, reason = (True, "palette_locked")
            for change in changes:
                change_ok, change_reason = _verify_palette_locked(change["path"])
                if not change_ok:
                    ok, reason = (change_ok, change_reason)
                    break
        else:  # pragma: no cover - guard for an unknown verifier key
            ok, reason = (True, key)
        results.append({"verifier": key, "status": "success" if ok else "failed", "reason": reason})
        ok_all = ok_all and ok
    return {"status": "success" if ok_all else "failed", "verifiers": results}


def apply_candidate(
    name: str,
    manifest: dict[str, Any],
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    candidate_set_path: Path | None = None,
    acceptance_path: Path | None = None,
    apply: bool = False,
    post_apply: bool = True,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    candidate_id = _candidate_id(manifest)
    sandbox = _candidate_sandbox(example_dir, candidate_id)
    candidate_manifest_path = sandbox / "candidate_manifest.json"
    manifest = _load_json(candidate_manifest_path, "candidate_manifest")
    if _candidate_id(manifest) != candidate_id:
        return _blocked(
            name,
            candidate_id,
            [_diagnostic("candidate_id_mismatch", "candidate manifest id mismatch")],
        )
    diagnostics: list[dict[str, str]] = []
    candidate_set_path = candidate_set_path or Path(str(manifest.get("candidate_set_path", "")))
    acceptance_path = acceptance_path or Path(f"build/candidates/{candidate_id}/acceptance.json")

    candidate_set_file = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        candidate_set_path.as_posix(),
    )
    candidate_set = _load_json(candidate_set_file, "candidate_set")
    candidate = None
    for item in candidate_set.get("candidates", []):
        if isinstance(item, dict) and item.get("id") == candidate_id:
            candidate = item
            break
    if candidate is None:
        diagnostics.append(_diagnostic("candidate_set_missing_candidate", "candidate not in set"))
    elif candidate.get("candidate_hash") != manifest.get("candidate_hash"):
        diagnostics.append(_diagnostic("candidate_hash_mismatch", "candidate hash mismatch"))

    render_manifest_path = sandbox / "render_manifest.json"
    render_manifest = _load_json(render_manifest_path, "render_manifest")
    for failure in _render_gate_failures(render_manifest):
        diagnostics.append(_diagnostic("render_gate_failed", failure))
    resolved_acceptance_path = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        acceptance_path.as_posix(),
    )
    try:
        resolved_acceptance_path.resolve().relative_to(sandbox.resolve())
    except ValueError:
        diagnostics.append(_diagnostic("acceptance_path_escape", "acceptance path escapes sandbox"))
    if not resolved_acceptance_path.is_file():
        diagnostics.append(_diagnostic("acceptance_missing", "acceptance artifact missing"))
    else:
        acceptance = _load_json(resolved_acceptance_path, "acceptance")
        diagnostics.extend(
            _acceptance_hash_diagnostics(
                acceptance=acceptance,
                candidate_id=candidate_id,
                manifest_path=candidate_manifest_path,
                render_manifest_path=render_manifest_path,
                manifest=manifest,
                render_manifest=render_manifest,
            )
        )

    apply_result_path = sandbox / "apply_result.json"
    if apply_result_path.is_file():
        apply_result = _load_json(apply_result_path, "apply_result")
        if apply_result.get("status") in TERMINAL_APPLY_STATUSES:
            diagnostics.append(_diagnostic("already_applied", "candidate is already applied"))

    active_lock = _active_mutation_lock(example_dir)
    if active_lock is not None:
        diagnostics.append(
            _diagnostic(
                "mutation_lock_active",
                "another mutation lock is active",
                _fixture_relative(example_dir, active_lock),
            )
        )

    changes, change_diagnostics = _build_changes(
        example_dir=example_dir,
        fixture_name=name,
        manifest=manifest,
    )
    diagnostics.extend(change_diagnostics)
    semantic_state = semantic_candidate_review.build_semantic_review_state(
        example_dir,
        candidate_manifest_path,
        manifest,
        spec=semantic_candidate_review.load_spec(example_dir),
    )
    for reason in semantic_candidate_review.semantic_blocking_reasons(semantic_state):
        diagnostics.append(_diagnostic("semantic_review", reason))
    if diagnostics:
        return _blocked(name, candidate_id, diagnostics)
    if not apply:
        return {
            "schema": SCHEMA,
            "figure_name": name,
            "candidate_id": candidate_id,
            "status": "ready",
            "changed_files": [],
            "rollback_patch": None,
            "post_apply": {},
            "diagnostics": [],
        }

    with _candidate_apply_lock(example_dir) as lock:
        if lock is not None:
            return _blocked(
                name,
                candidate_id,
                [_diagnostic("mutation_lock_active", "candidate apply lock is active")],
            )
        rollback_path = sandbox / "rollback.patch"
        if rollback_path.is_symlink():
            raise CandidateApplyError("sandbox_symlink_forbidden: rollback.patch")
        rollback_path.write_text(_rollback_patch(changes), encoding="utf-8")
        # Snapshot the ledger BEFORE mutation for the semantic recheck (CORR-2):
        # the post-apply recheck diffs (panel, defect_class, severity) counts
        # against this baseline, robust to coordinate-nudge fingerprint shifts.
        pre_defects = _pre_apply_defects(name, paths) if post_apply else []
        # Snapshot pre-apply visual_clash crossings so a finding-sourced recheck
        # can tell an edit-introduced NEW crossing from a stable baseline.
        pre_crossing = _post_crossing_texts(example_dir) if post_apply else []
        # Snapshot rendered labels BEFORE mutation for the value-preservation gate.
        # M3: if the baseline PDF is absent (e.g. git clean dropped build/), force a
        # pre-mutation compile of the CURRENT source so the gate has a real baseline
        # instead of silently skipping. If it still cannot be produced, the gate
        # fails closed downstream (_verify_labels_unchanged blocks on empty words).
        build_pdf = example_dir / "build" / f"{name}.pdf"
        if post_apply and not build_pdf.is_file():
            _compile_current_source(name, paths)
        pre_words = _pdf_words(build_pdf) if post_apply else Counter()
        changed_files: list[dict[str, str]] = []
        for change in changes:
            target = change["path"]
            before_hash = _sha256_file(target)
            target.write_text(str(change["after"]), encoding="utf-8")
            changed_files.append(
                {
                    "path": str(change["relative"]),
                    "before_sha256": before_hash,
                    "after_sha256": _sha256_file(target),
                }
            )
        post_apply_result = _post_apply_checks(name, paths) if post_apply else {}
        detector_recheck = (
            _post_apply_semantic_recheck(name, paths, manifest, pre_defects, pre_crossing)
            if post_apply
            else None
        )
        if detector_recheck is not None:
            post_apply_result["detector_recheck"] = detector_recheck
        if post_apply:
            # Value-preservation gate (CORR-3): the applied edit must not change
            # rendered labels or break palette discipline. AUTO-ROLLBACK the .tex
            # to its pre-mutation content on any violation. Autonomy safety: also
            # roll back when the efficacy recheck (detector_recheck) failed — the
            # verifier replaces the human gate, so a known-ineffective fix must be
            # UNDONE, never left applied and merely flagged.
            post_words = _pdf_words(build_pdf)
            class_verifiers = _run_class_verifiers(changes, pre_words, post_words)
            recheck_failed = (
                isinstance(detector_recheck, dict) and detector_recheck.get("status") != "success"
            )
            rolled_back = class_verifiers["status"] != "success" or recheck_failed
            if rolled_back:
                for change in changes:
                    change["path"].write_text(str(change["before"]), encoding="utf-8")
                post_apply_result["rollback_compile"] = _rollback_compile_status(
                    name,
                    paths,
                    build_pdf,
                )
            class_verifiers["rolled_back"] = rolled_back
            post_apply_result["class_verifiers"] = class_verifiers
            if rolled_back:
                result_status = "rolled_back"
            elif any(item.get("status") != "success" for item in post_apply_result.values()):
                result_status = "applied_with_failed_verification"
            else:
                result_status = "applied"
            required_commands = []
        else:
            result_status = "applied_unverified"
            required_commands = _required_post_apply_commands(name)
        result = {
            "schema": SCHEMA,
            "figure_name": name,
            "candidate_id": candidate_id,
            "status": result_status,
            "changed_files": changed_files,
            "rollback_patch": _fixture_relative(example_dir, rollback_path),
            "post_apply": post_apply_result,
            "required_commands": required_commands,
            "diagnostics": [],
        }
        if apply_result_path.is_symlink():
            raise CandidateApplyError("sandbox_symlink_forbidden: apply_result.json")
        apply_result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return result
