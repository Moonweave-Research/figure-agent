from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import authoring_execution_input_audit  # noqa: E402


def _write_transcript(path: Path, commands: list[str]) -> None:
    events = [
        {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": command,
                "status": "completed",
            },
        }
        for command in commands
    ]
    path.write_text(
        "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
    )


def test_passes_external_skill_and_allowlisted_repository_reads(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.jsonl"
    _write_transcript(
        transcript,
        [
            "/bin/zsh -lc \"sed -n '1,220p' /Users/test/.codex/skills/tikz/SKILL.md\"",
            "/bin/zsh -lc \"sed -n '1,220p' AGENTS.md\"",
            "/bin/zsh -lc \"rg 'cAmber' styles/polymer-paper-preamble.sty\"",
            "/bin/zsh -lc pwd",
        ],
    )

    audit = authoring_execution_input_audit.audit_authoring_transcript(
        transcript,
        allowed_repository_reads=["AGENTS.md", "styles/polymer-paper-preamble.sty"],
    )

    assert audit["decision"] == "pass"
    assert audit["observed_repository_reads"] == [
        "AGENTS.md",
        "styles/polymer-paper-preamble.sty",
    ]
    assert audit["undeclared_repository_reads"] == []


def test_blocks_undeclared_repository_content_read(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.jsonl"
    _write_transcript(
        transcript,
        [
            "/bin/zsh -lc \"sed -n '1,220p' AGENTS.md\"",
            "/bin/zsh -lc \"sed -n '1,220p' docs/execution-plan.md\"",
        ],
    )

    audit = authoring_execution_input_audit.audit_authoring_transcript(
        transcript,
        allowed_repository_reads=["AGENTS.md"],
    )

    assert audit["decision"] == "blocked"
    assert audit["undeclared_repository_reads"] == ["docs/execution-plan.md"]


def test_tracks_compound_reads_after_cd_from_repository_root(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.jsonl"
    _write_transcript(
        transcript,
        [
            "/bin/zsh -lc \"cd plugins/figure-agent && "
            "sed -n '1,240p' AGENTS.md && "
            "sed -n '1,260p' styles/polymer-paper-preamble.sty\"",
        ],
    )

    audit = authoring_execution_input_audit.audit_authoring_transcript(
        transcript,
        allowed_repository_reads=[
            "plugins/figure-agent/AGENTS.md",
            "plugins/figure-agent/styles/polymer-paper-preamble.sty",
        ],
    )

    assert audit["decision"] == "pass"
    assert audit["observed_repository_reads"] == [
        "plugins/figure-agent/AGENTS.md",
        "plugins/figure-agent/styles/polymer-paper-preamble.sty",
    ]


def test_rejects_malformed_transcript_event(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text("not-json\n", encoding="utf-8")

    with pytest.raises(
        authoring_execution_input_audit.AuthoringExecutionInputAuditError,
        match="invalid transcript JSON",
    ):
        authoring_execution_input_audit.audit_authoring_transcript(
            transcript, allowed_repository_reads=[]
        )
