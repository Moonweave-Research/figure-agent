from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "quality"))

from failure_corpus import FailureCorpusError, load_failure_corpus

FAILURE_CLASSES = {
    "semantic",
    "relation",
    "geometry",
    "composition",
    "typography",
    "style",
    "finish",
    "reproducibility",
}
SCALES = {"whole", "panel", "object_relation", "zoom"}


def write_source(root: Path) -> tuple[Path, str]:
    source = root / "review.yaml"
    source.write_text("verdict: confirmed\n", encoding="utf-8")
    return source, hashlib.sha256(source.read_bytes()).hexdigest()


def write_corpus(root: Path) -> Path:
    source, digest = write_source(root)
    payload = {
        "schema": "figure-agent.llm-failure-corpus.v1",
        "authority": "reviewed_evidence_only",
        "source_root": "corpus_parent",
        "cases": [
            {
                "id": "reviewed-finish-001",
                "figure_family": "synthetic-a",
                "failure_class": "finish",
                "observation_scale": "zoom",
                "review_outcome": "confirmed_defect",
                "source_path": source.name,
                "source_sha256": digest,
                "source_locator": "verdict",
                "semantic_target": "panel_f.contact",
                "attribution_state": "exact",
                "repair_family": "align_or_simplify_contact",
                "human_correction_minutes": 3.0,
            }
        ],
    }
    path = root / "corpus.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_loads_closed_reviewed_failure_taxonomy(tmp_path: Path) -> None:
    corpus = load_failure_corpus(write_corpus(tmp_path))
    assert corpus["schema"] == "figure-agent.llm-failure-corpus.v1"
    assert set(corpus["summary"]["failure_class_counts"]) <= FAILURE_CLASSES
    assert set(corpus["summary"]["observation_scale_counts"]) <= SCALES
    assert corpus["summary"]["confirmed_defect_count"] == 1


def test_rejects_unknown_failure_class(tmp_path: Path) -> None:
    path = write_corpus(tmp_path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["cases"][0]["failure_class"] = "looks_bad"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(FailureCorpusError, match="failure_class_invalid"):
        load_failure_corpus(path)


def test_rejects_unreviewed_or_hash_drifted_evidence(tmp_path: Path) -> None:
    path = write_corpus(tmp_path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["cases"][0]["review_outcome"] = "model_guess"
    payload["cases"][0]["source_sha256"] = "0" * 64
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(
        FailureCorpusError,
        match="review_outcome_invalid|source_hash_mismatch",
    ):
        load_failure_corpus(path)
