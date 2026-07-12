from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import yaml
from failure_corpus import load_failure_corpus

SOURCES_SCHEMA = "figure-agent.llm-failure-sources.v1"
CORPUS_SCHEMA = "figure-agent.llm-failure-corpus.v1"


class FailureCorpusCompileError(ValueError):
    pass


def compile_failure_corpus(source_index: Path, output_path: Path) -> dict[str, Any]:
    plugin_root = source_index.resolve().parents[1]
    index = yaml.safe_load(source_index.read_text(encoding="utf-8"))
    if not isinstance(index, dict) or index.get("schema") != SOURCES_SCHEMA:
        raise FailureCorpusCompileError("source_schema_invalid")
    if index.get("authority") != "reviewed_evidence_only":
        raise FailureCorpusCompileError("source_authority_invalid")
    raw_sources = index.get("sources")
    raw_cases = index.get("cases")
    if not isinstance(raw_sources, list) or not isinstance(raw_cases, list):
        raise FailureCorpusCompileError("source_index_invalid")

    sources: dict[str, Path] = {}
    for item in raw_sources:
        if not isinstance(item, dict):
            raise FailureCorpusCompileError("source_index_invalid")
        source_id = str(item.get("id") or "")
        relative = Path(str(item.get("path") or ""))
        unresolved = plugin_root / relative
        candidate = unresolved.resolve()
        if (
            not source_id
            or source_id in sources
            or relative.is_absolute()
            or ".." in relative.parts
            or not candidate.is_relative_to(plugin_root)
            or unresolved.is_symlink()
            or not candidate.is_file()
        ):
            raise FailureCorpusCompileError("source_path_invalid")
        sources[source_id] = candidate

    cases: list[dict[str, Any]] = []
    for raw in raw_cases:
        if not isinstance(raw, dict):
            raise FailureCorpusCompileError("source_index_invalid")
        source_id = str(raw.get("source_id") or "")
        locator = str(raw.get("source_locator") or "")
        if source_id not in sources or not locator:
            raise FailureCorpusCompileError("source_locator_invalid")
        source = sources[source_id]
        cases.append(
            {
                "id": str(raw["id"]),
                "figure_family": str(raw["figure_family"]),
                "failure_class": str(raw["failure_class"]),
                "observation_scale": str(raw["observation_scale"]),
                "review_outcome": str(raw["review_outcome"]),
                "source_path": source.relative_to(plugin_root).as_posix(),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "source_locator": locator,
                "semantic_target": raw.get("semantic_target"),
                "attribution_state": str(raw["attribution_state"]),
                "repair_family": raw.get("repair_family"),
                "human_correction_minutes": raw.get("human_correction_minutes"),
            }
        )

    payload = {
        "schema": CORPUS_SCHEMA,
        "authority": "reviewed_evidence_only",
        "source_root": "plugin_root",
        "cases": sorted(cases, key=lambda item: item["id"]),
    }
    output_path.write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    return load_failure_corpus(output_path, source_root=plugin_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_index", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()
    compile_failure_corpus(args.source_index, args.output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
