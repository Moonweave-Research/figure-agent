from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_next_experiment  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def test_quality_next_experiment_returns_preview_allowlist_command() -> None:
    payload = quality_next_experiment.build_next_experiment(plugin_root=PLUGIN_ROOT)

    assert payload["schema"] == "figure-agent.quality-next-experiment.v1"
    assert payload["recommendation"]["command"] == "fig-agent benchmark-run --suite smoke --json"
    assert payload["recommendation"]["allowed"] is True
    command = payload["recommendation"]["command"]
    for forbidden in ("--write", "--apply", "--accept", "--overwrite", "--force"):
        assert forbidden not in command


def test_fig_agent_quality_next_experiment_cli(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(tmp_path / "workspace")

    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(FIG_AGENT),
            "quality-next-experiment",
            "--json",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.quality-next-experiment.v1"
    assert payload["recommendation"]["reason_codes"]
