from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_evidence_index import _fixture  # noqa: E402


def _run_reject(workspace: Path, exp_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    env["FIG_AGENT_EXPERIENCE_LOG_DIR"] = str(exp_dir)
    return subprocess.run(
        [
            sys.executable,
            str(FIG_AGENT),
            "accept-candidate",
            "candidate_demo",
            "CAND001",
            "--candidate-set",
            "build/candidates/candidate_set.json",
            "--decision",
            "reject",
            "--reviewer",
            "local-user",
            "--rationale",
            "rejected on visual review",
        ],
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _reject_rows(log: Path) -> list[dict]:
    rows = [
        json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    return [row for row in rows if row["outcome"]["human_label"] == "reject"]


def test_accept_candidate_reject_appends_experience_row(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    exp_dir = tmp_path / "exp"
    _fixture(workspace, with_apply=False)  # rendered but never applied

    proc = _run_reject(workspace, exp_dir)
    assert proc.returncode == 0, proc.stderr

    log = exp_dir / "candidate_demo.jsonl"
    reject_rows = _reject_rows(log)
    assert len(reject_rows) == 1
    row = reject_rows[0]
    assert row["action"]["candidate_id"] == "CAND001"
    # No apply ran, so the record must not read as a regression.
    assert row["outcome"]["quality_movement"] is None
    assert row["outcome"]["apply_status"] == "blocked"


def test_repeated_reject_does_not_duplicate_experience_row(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    exp_dir = tmp_path / "exp"
    _fixture(workspace, with_apply=False)

    first = _run_reject(workspace, exp_dir)
    assert first.returncode == 0, first.stderr
    second = _run_reject(workspace, exp_dir)
    assert second.returncode == 0, second.stderr

    log = exp_dir / "candidate_demo.jsonl"
    assert len(_reject_rows(log)) == 1
