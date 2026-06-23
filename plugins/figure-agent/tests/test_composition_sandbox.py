from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

SOURCE_TEXT = (
    "% fig-agent:start object=carrier_walk\n"
    "old walk\n"
    "% fig-agent:end object=carrier_walk\n"
)


def _future_api(module_name: str, attribute: str):
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def _fixture(tmp_path: Path, name: str = "fig3_resistance_mechanism") -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / name
    sandbox = fixture / "build" / "candidates" / "CCAND001"
    sandbox.mkdir(parents=True)
    source = fixture / f"{name}.tex"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    (sandbox / "source").mkdir()
    (sandbox / "render").mkdir()
    return workspace, fixture, source


@pytest.mark.parametrize(
    ("candidate_path", "diagnostic_code"),
    [
        (Path("/etc/passwd"), "absolute_path_forbidden"),
        (Path("../outside.tex"), "path_escape_forbidden"),
        (Path("build/candidates/CCAND001/source/outside.tex"), "sandbox_symlink_forbidden"),
    ],
)
def test_tex_sandbox_rejects_path_escape_variants(
    tmp_path: Path,
    candidate_path: Path,
    diagnostic_code: str,
) -> None:
    workspace, fixture, source = _fixture(tmp_path)
    if candidate_path.name == "outside.tex":
        outside = tmp_path / "outside.tex"
        outside.write_text("outside\n", encoding="utf-8")
        symlink = fixture / "build" / "candidates" / "CCAND001" / "source" / "outside.tex"
        symlink.symlink_to(outside)

    validate_sandbox = _future_api("composition_sandbox", "validate_tex_sandbox_policy")
    result = validate_sandbox(
        "fig3_resistance_mechanism",
        candidate_source_path=candidate_path,
        workspace_root=workspace,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == diagnostic_code
    assert result["diagnostics"][0]["stage"] == "pre_tex"


@pytest.mark.parametrize(
    ("tex_source", "diagnostic_code"),
    [
        (r"\input{/etc/passwd}", "forbidden_input_directive"),
        (r"\input{../outside.tex}", "forbidden_input_directive"),
        (r"\immediate\write18{touch /tmp/pwned}", "write_escape_forbidden"),
    ],
)
def test_tex_sandbox_rejects_forbidden_tex_primitives_before_execution(
    tmp_path: Path,
    tex_source: str,
    diagnostic_code: str,
) -> None:
    workspace, fixture, source = _fixture(tmp_path)
    source.write_text(tex_source + "\n", encoding="utf-8")

    validate_sandbox = _future_api("composition_sandbox", "validate_tex_sandbox_policy")
    result = validate_sandbox(
        "fig3_resistance_mechanism",
        candidate_source_path=source,
        workspace_root=workspace,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == diagnostic_code
    assert result["diagnostics"][0]["stage"] == "pre_tex"


@pytest.mark.parametrize(
    "tex_command",
    [
        ["lualatex", "--shell-escape", "candidate.tex"],
        ["lualatex", "-shell-escape", "candidate.tex"],
        ["lualatex", "-enable-write18", "candidate.tex"],
    ],
)
def test_tex_sandbox_rejects_shell_escape_command_tokens_before_tex_execution(
    tmp_path: Path,
    tex_command: list[str],
) -> None:
    workspace, fixture, source = _fixture(tmp_path)
    command_path = fixture / "command.json"
    command_path.write_text(
        json.dumps({"command": tex_command}, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    validate_command = _future_api("composition_sandbox", "validate_tex_compile_command")
    result = validate_command(
        "fig3_resistance_mechanism",
        compile_command=tex_command,
        workspace_root=workspace,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "shell_escape_forbidden"
    assert result["diagnostics"][0]["stage"] == "pre_tex"
    assert command_path.is_file()
