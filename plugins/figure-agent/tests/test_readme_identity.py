from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_readmes_state_constrained_figure_agent_identity() -> None:
    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    plugin_readme = (ROOT / "plugins" / "figure-agent" / "README.md").read_text(
        encoding="utf-8"
    )
    combined = f"{root_readme}\n{plugin_readme}"

    assert "not a graph plotting library" in combined
    assert "not a matplotlib wrapper" in combined
    assert "not a one-shot image generator" in combined
    assert "Journal rules are hard constraints" in combined
    assert "beauty is optimized only within those constraints" in combined
