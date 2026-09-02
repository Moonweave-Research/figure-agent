import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARCH_DOC = os.path.join(REPO_ROOT, "docs", "architecture-overview.md")
README = os.path.join(REPO_ROOT, "README.md")
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def test_composition_layer_documented() -> None:
    text = _read(ARCH_DOC)
    assert "composition" in text.lower()
    assert "composition_scene" in text


def test_cited_script_paths_exist() -> None:
    text = _read(ARCH_DOC)
    cited = set(re.findall(r"scripts/[\w./-]+\.py", text))
    assert cited, "no scripts/*.py paths cited in architecture doc"
    missing = [path for path in cited if not os.path.exists(os.path.join(REPO_ROOT, path))]
    assert not missing, f"doc-rot: cited paths do not exist: {sorted(missing)}"


def test_svg_polish_row_has_vacuity_caveat() -> None:
    caveat_tokens = ("vacuous", "quarantin", "zero geometry")
    for line in _read(README).splitlines():
        if "SVG polish handoff" in line:
            assert any(token in line.lower() for token in caveat_tokens), (
                "SVG polish handoff row lacks a vacuity/quarantine caveat"
            )
            return
    raise AssertionError("no 'SVG polish handoff' line found in README.md")


def test_architecture_layer_55_names_external_final_artifact_handoff() -> None:
    text = _read(ARCH_DOC)
    layer_model = text.partition("## Layer model")[2].partition("## Layer-by-layer reference")[0]

    assert "Layer 5.5: Final Artifact" in layer_model
    assert "external final-artifact handoff" in layer_model
    assert "polished-SVG contract" not in layer_model


COMPILE_SH = os.path.join(REPO_ROOT, "scripts", "compile.sh")
CLOSEOUT = os.path.join(REPO_ROOT, "scripts", "fig_closeout.py")
CONTRACTS = os.path.join(REPO_ROOT, "scripts", "compatibility_command_contracts.py")


def test_golden_gate_is_attributed_to_its_real_caller() -> None:
    assert "check_golden_artifacts" not in _read(COMPILE_SH)
    assert "check_golden_artifacts" in _read(CLOSEOUT)

    text = _read(ARCH_DOC)
    compile_section = text.partition("## Compile and validation")[2].partition("\n## ")[0]
    lifecycle = text.partition("## Repair and state lifecycle")[2].partition("\n## ")[0]

    assert "check_golden_artifacts.py" not in compile_section
    assert "check_golden_artifacts.py" in lifecycle
    assert "fig_closeout.py" in lifecycle


def test_compatibility_contract_claim_matches_the_registry() -> None:
    import compatibility_command_contracts

    covered = compatibility_command_contracts.command_names()
    text = _read(ARCH_DOC)

    assert covered == {"loop", "improve", "e2e-smoke"}, (
        "registry coverage changed; update the architecture doc's claim"
    )
    assert "Compatibility commands remain callable only where their evidence contract is" \
        not in text
    for command in sorted(covered):
        assert f"`{command}`" in text
    assert "dispatch without one" in text


def test_readme_names_the_hard_gates_that_run_in_default_mode() -> None:
    compile_sh = _read(COMPILE_SH)
    print_size = compile_sh.index("check_print_size_contract.py")
    report_only = compile_sh.index("set +e")
    assert print_size < report_only, (
        "print-size contract is no longer a default-mode hard gate; update README"
    )

    row = next(
        line for line in _read(README).splitlines() if "**Build pipeline**" in line
    )
    assert "Report-only by default" not in row
    assert "check_print_size_contract.py" in row
    assert "hard gate" in row
