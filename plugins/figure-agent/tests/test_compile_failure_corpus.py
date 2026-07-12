from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "quality"))

from compile_failure_corpus import FailureCorpusCompileError, compile_failure_corpus
from failure_corpus import load_failure_corpus

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def test_compiles_real_reviewed_sources_deterministically(tmp_path: Path) -> None:
    source_index = PLUGIN_ROOT / "benchmarks" / "llm_failure_sources.yaml"
    first = compile_failure_corpus(source_index, tmp_path / "first.yaml")
    second = compile_failure_corpus(source_index, tmp_path / "second.yaml")
    assert first == second
    assert {case["failure_class"] for case in first["cases"]} >= {
        "typography",
        "geometry",
        "finish",
        "style",
    }
    assert all(len(case["source_sha256"]) == 64 for case in first["cases"])
    assert (
        load_failure_corpus(tmp_path / "first.yaml", source_root=PLUGIN_ROOT)[
            "summary"
        ]["case_count"]
        == 5
    )


def test_installed_corpus_matches_compiled_bytes(tmp_path: Path) -> None:
    expected = compile_failure_corpus(
        PLUGIN_ROOT / "benchmarks" / "llm_failure_sources.yaml",
        tmp_path / "expected.yaml",
    )
    installed = load_failure_corpus(
        PLUGIN_ROOT / "benchmarks" / "llm_failure_corpus.yaml"
    )
    assert installed["cases"] == expected["cases"]


def write_index(root: Path, source_path: str, locator: str = "verdict") -> Path:
    benchmarks = root / "benchmarks"
    benchmarks.mkdir(parents=True)
    index = {
        "schema": "figure-agent.llm-failure-sources.v1",
        "authority": "reviewed_evidence_only",
        "sources": [{"id": "review", "path": source_path}],
        "cases": [
            {
                "id": "case-1",
                "source_id": "review",
                "source_locator": locator,
                "figure_family": "synthetic",
                "failure_class": "finish",
                "observation_scale": "zoom",
                "review_outcome": "confirmed_defect",
                "semantic_target": "panel.contact",
                "attribution_state": "exact",
                "repair_family": "align_contact",
            }
        ],
    }
    path = benchmarks / "sources.yaml"
    path.write_text(yaml.safe_dump(index, sort_keys=False), encoding="utf-8")
    return path


@pytest.mark.parametrize("source_path", ["../outside.yaml", "/tmp/review.yaml"])
def test_rejects_sources_outside_plugin_root(
    tmp_path: Path, source_path: str
) -> None:
    index = write_index(tmp_path / "plugin", source_path)
    with pytest.raises(FailureCorpusCompileError, match="source_path_invalid"):
        compile_failure_corpus(index, tmp_path / "out.yaml")


def test_rejects_symlinked_source(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin"
    source = plugin / "review.yaml"
    source.parent.mkdir(parents=True)
    source.write_text("verdict: confirmed\n", encoding="utf-8")
    link = plugin / "linked-review.yaml"
    link.symlink_to(source)
    index = write_index(plugin, link.name)
    with pytest.raises(FailureCorpusCompileError, match="source_path_invalid"):
        compile_failure_corpus(index, tmp_path / "out.yaml")


def test_rejects_empty_source_locator(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin"
    source = plugin / "review.yaml"
    source.parent.mkdir(parents=True)
    source.write_text("verdict: confirmed\n", encoding="utf-8")
    index = write_index(plugin, source.name, locator="")
    with pytest.raises(FailureCorpusCompileError, match="source_locator_invalid"):
        compile_failure_corpus(index, tmp_path / "out.yaml")
