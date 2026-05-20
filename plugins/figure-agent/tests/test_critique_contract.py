from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_contract import (  # noqa: E402
    CritiqueContractError,
    critique_finding_id,
    critique_findings,
    load_critique_frontmatter,
)


def test_load_critique_frontmatter_and_findings(tmp_path: Path) -> None:
    critique_path = tmp_path / "critique.md"
    critique_path.write_text(
        "---\n"
        "schema: figure-agent.critique.v1\n"
        "fixture: demo_fig\n"
        "panels:\n"
        "  - id: A\n"
        "    findings:\n"
        "      - id: P001\n"
        "        status: open\n"
        "findings:\n"
        "  - id: C001\n"
        "    status: resolved\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )

    frontmatter = load_critique_frontmatter(critique_path)
    findings = critique_findings(frontmatter)

    assert frontmatter["fixture"] == "demo_fig"
    assert [
        critique_finding_id(finding, f"critique finding {index}")
        for index, finding in enumerate(findings)
    ] == ["P001", "C001"]


def test_critique_findings_rejects_malformed_collections() -> None:
    with pytest.raises(CritiqueContractError, match="panels must be a list"):
        critique_findings({"panels": "not-a-list"})

    with pytest.raises(CritiqueContractError, match="findings must be a list"):
        critique_findings({"findings": "not-a-list"})


def test_critique_finding_id_rejects_missing_id() -> None:
    with pytest.raises(CritiqueContractError, match="id must be a non-empty string"):
        critique_finding_id({"status": "open"}, "critique finding 0")
