from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
SCRIPT_IMPORT_DIRS = (
    SCRIPTS_DIR,
    SCRIPTS_DIR / "checks",
    SCRIPTS_DIR / "candidates",
    SCRIPTS_DIR / "quality",
    SCRIPTS_DIR / "loop",
    SCRIPTS_DIR / "driver",
    SCRIPTS_DIR / "svg_polish",
)

for script_dir in reversed(SCRIPT_IMPORT_DIRS):
    sys.path.insert(0, str(script_dir))


# New tests needing the plain `<workspace>/examples/<name>/` scaffold should call
# `fixture_scaffold.make_example_fixture` rather than add another local `_fixture`.


@pytest.fixture(autouse=True)
def _isolate_experience_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIG_AGENT_EXPERIENCE_LOG_DIR", str(tmp_path / "experience-log"))
