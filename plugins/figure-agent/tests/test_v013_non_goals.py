from __future__ import annotations

import ast
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DECISION_PATHS = [
    PLUGIN_ROOT / "scripts" / "quality",
    PLUGIN_ROOT / "scripts" / "candidates",
    PLUGIN_ROOT / "scripts" / "loop",
    PLUGIN_ROOT / "scripts" / "fig_loop.py",
    PLUGIN_ROOT / "scripts" / "experience_log.py",
]
FORBIDDEN_MODEL_IMPORT_ROOTS = {
    "anthropic",
    "google",
    "joblib",
    "openai",
    "pickle",
    "sklearn",
    "tensorflow",
    "torch",
    "xgboost",
}
FORBIDDEN_MEASUREMENT_IMPORT_ROOTS = {
    "PIL",
    "candidate_render",
    "candidate_visual_eval",
    "detector_feedback_ledger",
    "detector_log",
    "numpy",
    "pdfplumber",
    "quality_benchmark",
    "scipy",
    "subprocess",
}
FORBIDDEN_MEASUREMENT_TOKENS = (
    "subprocess.",
    "os.system(",
    "candidate_render.",
    "candidate_visual_eval.",
    "quality_benchmark.",
    "detector_log.",
    "detector_feedback_ledger.",
)
FORBIDDEN_REWARD_TEXT_TOKENS = (
    "human_note",
    "llm",
    "note",
    "prose",
    "rationale",
    "summary",
)


def _decision_path_python_files() -> list[Path]:
    paths: list[Path] = []
    for path in DECISION_PATHS:
        if path.is_file():
            paths.append(path)
        else:
            paths.extend(sorted(path.rglob("*.py")))
    return paths


def _import_roots(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            roots.add((node.module or "").split(".", maxsplit=1)[0])
    return roots


def test_v013_decision_path_does_not_revive_ml_advisory_or_opaque_models() -> None:
    offenders: list[str] = []
    for path in _decision_path_python_files():
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name.split(".", maxsplit=1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [(node.module or "").split(".", maxsplit=1)[0]]
            else:
                continue
            forbidden = sorted(FORBIDDEN_MODEL_IMPORT_ROOTS.intersection(imported))
            if forbidden:
                rel = path.relative_to(PLUGIN_ROOT)
                offenders.append(f"{rel}: {', '.join(forbidden)}")
        if "ml_advisory" in source or "ml-advisory" in source:
            offenders.append(f"{path.relative_to(PLUGIN_ROOT)}: ml_advisory")

    assert offenders == []


def test_v013_loop_metrics_uses_persisted_logs_without_new_measurement() -> None:
    path = PLUGIN_ROOT / "scripts" / "quality" / "quality_loop_metrics.py"
    imported_roots = _import_roots(path)
    source = path.read_text(encoding="utf-8")

    assert FORBIDDEN_MEASUREMENT_IMPORT_ROOTS.isdisjoint(imported_roots)
    assert not any(token in source for token in FORBIDDEN_MEASUREMENT_TOKENS)


def test_v013_reward_gate_code_does_not_read_text_annotations() -> None:
    path = PLUGIN_ROOT / "scripts" / "experience_log.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    guarded_functions = {"_post_apply_pipeline_ok", "_quality_movement"}
    guarded_source = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in guarded_functions:
            segment = ast.get_source_segment(source, node)
            assert segment is not None
            guarded_source.append(segment.lower())

    assert len(guarded_source) == len(guarded_functions)
    joined = "\n".join(guarded_source)
    assert not any(token in joined for token in FORBIDDEN_REWARD_TEXT_TOKENS)
