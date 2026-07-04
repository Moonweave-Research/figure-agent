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


def _decision_path_python_files() -> list[Path]:
    paths: list[Path] = []
    for path in DECISION_PATHS:
        if path.is_file():
            paths.append(path)
        else:
            paths.extend(sorted(path.rglob("*.py")))
    return paths


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
