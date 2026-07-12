from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "figure-agent.llm-failure-corpus.v1"
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
OBSERVATION_SCALES = {"whole", "panel", "object_relation", "zoom"}
REVIEW_OUTCOMES = {"confirmed_defect", "accepted_false_positive"}
ATTRIBUTION_STATES = {"exact", "ambiguous", "unbound"}


class FailureCorpusError(ValueError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_source(root: Path, value: object) -> Path:
    relative = Path(str(value or ""))
    candidate = (root / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts:
        raise FailureCorpusError("source_path_invalid")
    if not candidate.is_relative_to(root.resolve()):
        raise FailureCorpusError("source_path_invalid")
    if candidate.is_symlink() or not candidate.is_file():
        raise FailureCorpusError("source_missing")
    return candidate


def load_failure_corpus(
    path: Path,
    *,
    source_root: Path | None = None,
) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise FailureCorpusError("schema_invalid")
    if payload.get("authority") != "reviewed_evidence_only":
        raise FailureCorpusError("authority_invalid")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise FailureCorpusError("cases_missing")

    root_kind = payload.get("source_root")
    if source_root is None:
        if root_kind == "corpus_parent":
            source_root = path.parent
        elif root_kind == "plugin_root" and path.parent.name == "benchmarks":
            source_root = path.parent.parent
        else:
            raise FailureCorpusError("source_root_invalid")

    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for raw in cases:
        if not isinstance(raw, dict):
            raise FailureCorpusError("case_invalid")
        case_id = str(raw.get("id") or "")
        if not case_id or case_id in seen:
            raise FailureCorpusError("case_id_invalid")
        seen.add(case_id)
        if raw.get("failure_class") not in FAILURE_CLASSES:
            raise FailureCorpusError("failure_class_invalid")
        if raw.get("observation_scale") not in OBSERVATION_SCALES:
            raise FailureCorpusError("observation_scale_invalid")
        if raw.get("review_outcome") not in REVIEW_OUTCOMES:
            raise FailureCorpusError("review_outcome_invalid")
        if raw.get("attribution_state") not in ATTRIBUTION_STATES:
            raise FailureCorpusError("attribution_state_invalid")
        source = _safe_source(source_root, raw.get("source_path"))
        if _sha256(source) != raw.get("source_sha256"):
            raise FailureCorpusError("source_hash_mismatch")
        normalized.append(dict(raw))

    class_counts = Counter(item["failure_class"] for item in normalized)
    scale_counts = Counter(item["observation_scale"] for item in normalized)
    return {
        **payload,
        "cases": normalized,
        "summary": {
            "case_count": len(normalized),
            "confirmed_defect_count": sum(
                item["review_outcome"] == "confirmed_defect" for item in normalized
            ),
            "failure_class_counts": dict(sorted(class_counts.items())),
            "observation_scale_counts": dict(sorted(scale_counts.items())),
        },
    }
