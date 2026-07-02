import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARCH_DOC = os.path.join(REPO_ROOT, "docs", "architecture-overview.md")
README = os.path.join(REPO_ROOT, "README.md")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def test_composition_layer_documented() -> None:
    text = _read(ARCH_DOC)
    assert "composition" in text.lower()
    assert "composition_families" in text


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
