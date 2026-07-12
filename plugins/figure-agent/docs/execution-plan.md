<!-- FIGURE_AGENT:EXECUTION_AUTHORITY -->
# Figure Agent Failure-First Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Prove that Figure Agent reduces recurrent scientific-figure failures produced by the same LLM by adding reviewed failure evidence, multi-scale attribution, and bounded repair without expanding fixture-specific drawing logic.

**Architecture:** Keep LLM authoring freeform and renderer-neutral. Add a small reviewed failure-corpus layer, an A/B/C evaluator for raw versus verified versus repaired runs, and stricter bounded-repair contracts around the existing quality ledger and patch pipeline. Do not add behavior to the 9,849-line quality_search.py; new logic lives in focused modules and reuses existing attribution, benchmark, provenance, and human-gate surfaces.

**Tech Stack:** Python 3.11+, pytest, PyYAML, existing Figure Agent CLI and quality modules, TikZ/LuaLaTeX and deterministic SVG/PNG evidence. Add no dependency.

---

## 0. Execution rules

This file is the single active forward plan. docs/product-spec.md is the single product authority. Historical architecture notes, milestones, fixture plans, and the prior TikZ/SVG/illustration-grammar task list remain evidence in Git history and decision records; they do not reorder this plan.

For every task:

1. work in a clean dedicated worktree and codex/ branch based on commit 8fdc110f or its integrated descendant;
2. preserve accepted, historical, and user-owned artifacts;
3. write the smallest failing test first;
4. implement only enough general behavior to pass it;
5. run focused tests before affected-suite tests;
6. run git diff --check and Ruff on changed Python;
7. commit one reviewable task at a time;
8. never equate machine-valid or review-ready with human-accepted; and
9. do not modify scripts/quality/quality_search.py or scripts/quality/panel_block_edits.yaml in this plan.

All commands run from plugins/figure-agent unless explicitly stated otherwise.

## 1. File ownership map

| File | Responsibility |
| --- | --- |
| docs/product-spec.md | Product identity, boundaries, promotion rules |
| docs/execution-plan.md | This task sequence and completion boundary |
| scripts/quality/failure_corpus.py | Validate reviewed failure classes and provenance |
| benchmarks/llm_failure_sources.yaml | Human-authored index of reviewed evidence to compile |
| benchmarks/llm_failure_corpus.yaml | Hash-bound normalized failure corpus |
| scripts/quality/compile_failure_corpus.py | Compile only declared reviewed evidence into the corpus |
| scripts/quality/failure_ablation.py | Validate and compare raw, verified, and repaired run manifests |
| scripts/quality/quality_patch_policy.py | Decide whether a normalized defect may produce a bounded repair candidate |
| scripts/quality/quality_patch_plan.py | Build a repair operation with selectors, invariants, budgets, and rollback |
| scripts/quality/quality_patch_apply.py | Fail closed before mutation and record a rollback/result receipt |
| bin/fig-agent | Expose read-only corpus and ablation commands |
| tests/test_failure_corpus.py | Corpus schema, provenance, taxonomy, and fixture-independence tests |
| tests/test_compile_failure_corpus.py | Deterministic real-evidence compilation tests |
| tests/test_failure_ablation.py | A/B/C comparability and non-compensating evaluation tests |
| tests/test_quality_patch_policy.py | Patchability boundary tests |
| tests/test_quality_patch_plan.py | Bounded repair-plan contract tests |
| tests/test_quality_patch_apply.py | Apply/rollback and protected-invariant tests |
| tests/test_failure_first_cli.py | CLI read-only and JSON contract tests |
| tests/test_document_authority.py | Guard the new product and plan language |

## Task 0: Lock the failure-first authority boundary

**Files:**

- Modify: tests/test_document_authority.py
- Verify: docs/product-spec.md
- Verify: docs/execution-plan.md

- [ ] **Step 1: Write the failing authority test**

Add:

~~~python
def test_canonical_docs_define_failure_first_llm_control() -> None:
    product = _read(PLUGIN_ROOT / PRODUCT_DOC)
    execution = _read(PLUGIN_ROOT / EXECUTION_DOC)

    for required in (
        "Let the LLM propose freely",
        "Failure ontology",
        "Bounded repair contract",
        "Figure production is not Figure Agent product development.",
        "A: raw LLM authoring",
        "B: the same LLM plus Figure Agent contracts and verification",
        "C: the same LLM plus contracts, verification, and bounded repair",
    ):
        assert required in product

    for required in (
        "Failure-First Implementation Plan",
        "failure_corpus.py",
        "failure_ablation.py",
        "quality_search.py or scripts/quality/panel_block_edits.yaml",
    ):
        assert required in execution

    assert "determine whether an LLM can directly author SVG" not in product
~~~

- [ ] **Step 2: Run the test and verify RED**

Run:

~~~bash
uv run pytest tests/test_document_authority.py::test_canonical_docs_define_failure_first_llm_control -q
~~~

Expected: FAIL because the product specification does not yet contain the exact
figure-production boundary sentence.

- [ ] **Step 3: Make the authority wording exact**

Add this sentence at the end of Section 3.3 of docs/product-spec.md:

> Figure production is not Figure Agent product development.

Do not change the meaning of docs/product-spec.md merely to satisfy the test.

- [ ] **Step 4: Run authority and release-contract tests**

Run:

~~~bash
uv run pytest tests/test_document_authority.py tests/test_release_contract.py -q
uv run ruff check tests/test_document_authority.py
git diff --check
~~~

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add tests/test_document_authority.py docs/product-spec.md
git commit -m "test: lock failure-first product authority"
~~~

## Task 1: Define the reviewed failure-corpus contract

**Files:**

- Create: scripts/quality/failure_corpus.py
- Create: tests/test_failure_corpus.py

- [ ] **Step 1: Write RED tests for the closed taxonomy**

Create tests/test_failure_corpus.py:

~~~python
from __future__ import annotations

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
    import hashlib

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
~~~

- [ ] **Step 2: Run the tests and verify RED**

Run:

~~~bash
uv run pytest tests/test_failure_corpus.py -q
~~~

Expected: FAIL because failure_corpus.py does not exist.

- [ ] **Step 3: Implement the minimal loader**

Create scripts/quality/failure_corpus.py with these public contracts:

~~~python
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
~~~

- [ ] **Step 4: Run focused verification**

~~~bash
uv run pytest tests/test_failure_corpus.py -q
uv run ruff check scripts/quality/failure_corpus.py tests/test_failure_corpus.py
git diff --check
~~~

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add scripts/quality/failure_corpus.py tests/test_failure_corpus.py
git commit -m "feat: define reviewed LLM failure corpus"
~~~

## Task 2: Compile the first real reviewed corpus without inventing labels

**Files:**

- Create: benchmarks/llm_failure_sources.yaml
- Create: benchmarks/llm_failure_corpus.yaml
- Create: scripts/quality/compile_failure_corpus.py
- Create: tests/test_compile_failure_corpus.py
- Modify: tests/test_failure_corpus.py

The first corpus is intentionally small. It compiles only already-reviewed evidence from:

- examples/fig1_direct_svg_cleanroom_baseline/review/distributions/review-v3-08cc4280c1e69e77/response.yaml
- benchmarks/visual_attribution_suite.yaml

It must include at least one confirmed case in typography, geometry, finish, and style, plus one accepted false positive. It must not manufacture a scientific verdict from comments that explicitly say no definite scientific error was identified.

- [ ] **Step 1: Write the source-index file**

Create benchmarks/llm_failure_sources.yaml:

~~~yaml
schema: figure-agent.llm-failure-sources.v1
authority: reviewed_evidence_only
sources:
  - id: fig1-direct-svg-primary-review
    path: examples/fig1_direct_svg_cleanroom_baseline/review/distributions/review-v3-08cc4280c1e69e77/response.yaml
    reviewer: moon
  - id: visual-attribution-reviewed-ledger
    path: benchmarks/visual_attribution_suite.yaml
    reviewer: repository_review_records
cases:
  - id: fig1-c-trap-band-overlap
    source_id: fig1-direct-svg-primary-review
    source_locator: primary_review.panels.C.scientific.B.evidence
    figure_family: fig1_direct_svg
    failure_class: geometry
    observation_scale: object_relation
    review_outcome: confirmed_defect
    semantic_target: panel_c.trap_bands
    attribution_state: exact
    repair_family: restore_declared_relation
  - id: fig1-f-equipment-label-overlap
    source_id: fig1-direct-svg-primary-review
    source_locator: primary_review.panels.F.scientific.A.evidence
    figure_family: fig1_direct_svg
    failure_class: typography
    observation_scale: panel
    review_outcome: confirmed_defect
    semantic_target: panel_f.equipment_labels
    attribution_state: exact
    repair_family: label_reflow
  - id: fig1-f-cantilever-shape
    source_id: fig1-direct-svg-primary-review
    source_locator: primary_review.panels.F.scientific.B.evidence
    figure_family: fig1_direct_svg
    failure_class: finish
    observation_scale: object_relation
    review_outcome: confirmed_defect
    semantic_target: panel_f.cantilever
    attribution_state: exact
    repair_family: close_or_complete_contour
  - id: fig1-c-visual-language
    source_id: fig1-direct-svg-primary-review
    source_locator: primary_review.panels.C.scientific.A.evidence
    figure_family: fig1_direct_svg
    failure_class: style
    observation_scale: panel
    review_outcome: confirmed_defect
    semantic_target: panel_c
    attribution_state: exact
    repair_family: normalize_stroke_and_color_roles
  - id: fig1-v2-vc009
    source_id: visual-attribution-reviewed-ledger
    source_locator: reviewed_evidence[id=fig1-v2-vc009-reviewed-false-positive]
    figure_family: fig1_tikz
    failure_class: typography
    observation_scale: zoom
    review_outcome: accepted_false_positive
    semantic_target: null
    attribution_state: unbound
    repair_family: null
~~~

- [ ] **Step 2: Write the failing compiler test**

Create tests/test_compile_failure_corpus.py:

~~~python
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "quality"))

from compile_failure_corpus import compile_failure_corpus
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
    assert load_failure_corpus(
        tmp_path / "first.yaml", source_root=PLUGIN_ROOT
    )["summary"]["case_count"] == 5


def test_installed_corpus_matches_compiled_bytes(tmp_path: Path) -> None:
    expected = compile_failure_corpus(
        PLUGIN_ROOT / "benchmarks" / "llm_failure_sources.yaml",
        tmp_path / "expected.yaml",
    )
    installed = load_failure_corpus(
        PLUGIN_ROOT / "benchmarks" / "llm_failure_corpus.yaml"
    )
    assert installed["cases"] == expected["cases"]
~~~

- [ ] **Step 3: Run the compiler test and verify RED**

~~~bash
uv run pytest tests/test_compile_failure_corpus.py -q
~~~

Expected: FAIL because compile_failure_corpus.py and the installed corpus do not exist.

- [ ] **Step 4: Implement deterministic compilation**

Create scripts/quality/compile_failure_corpus.py. It must:

- require schema figure-agent.llm-failure-sources.v1;
- resolve every source beneath the plugin root;
- reject symlinks, absolute paths, parent traversal, and an empty source_locator field;
- calculate source_sha256 from actual bytes;
- copy only declared case metadata;
- sort cases by ID;
- write via yaml.safe_dump(payload, sort_keys=False);
- validate the emitted file with load_failure_corpus before returning.

The public signature is:

~~~python
def compile_failure_corpus(source_index: Path, output_path: Path) -> dict[str, Any]:
    plugin_root = source_index.resolve().parents[1]
    index = yaml.safe_load(source_index.read_text(encoding="utf-8"))
    if not isinstance(index, dict) or index.get("schema") != SOURCES_SCHEMA:
        raise FailureCorpusCompileError("source_schema_invalid")
    raw_sources = index.get("sources")
    raw_cases = index.get("cases")
    if not isinstance(raw_sources, list) or not isinstance(raw_cases, list):
        raise FailureCorpusCompileError("source_index_invalid")

    sources: dict[str, Path] = {}
    for item in raw_sources:
        source_id = str(item.get("id") or "")
        relative = Path(str(item.get("path") or ""))
        candidate = (plugin_root / relative).resolve()
        if (
            not source_id
            or relative.is_absolute()
            or ".." in relative.parts
            or not candidate.is_relative_to(plugin_root)
            or candidate.is_symlink()
            or not candidate.is_file()
        ):
            raise FailureCorpusCompileError("source_path_invalid")
        sources[source_id] = candidate

    cases: list[dict[str, Any]] = []
    for raw in raw_cases:
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
        "schema": "figure-agent.llm-failure-corpus.v1",
        "authority": "reviewed_evidence_only",
        "source_root": "plugin_root",
        "cases": sorted(cases, key=lambda item: item["id"]),
    }
    output_path.write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    return load_failure_corpus(output_path, source_root=plugin_root)
~~~

Locator validation is conservative: require a non-empty locator bound to the
full source hash. The compiler does not interpret free-form review text, resolve
an ad hoc query language, or generate failure classes with an LLM.

- [ ] **Step 5: Materialize and verify the installed corpus**

Run:

~~~bash
uv run python scripts/quality/compile_failure_corpus.py   benchmarks/llm_failure_sources.yaml   benchmarks/llm_failure_corpus.yaml
uv run pytest tests/test_failure_corpus.py tests/test_compile_failure_corpus.py -q
uv run ruff check scripts/quality/failure_corpus.py   scripts/quality/compile_failure_corpus.py   tests/test_failure_corpus.py tests/test_compile_failure_corpus.py
git diff --check
~~~

Expected: five hash-bound cases, tests PASS.

- [ ] **Step 6: Commit**

~~~bash
git add benchmarks/llm_failure_sources.yaml benchmarks/llm_failure_corpus.yaml   scripts/quality/failure_corpus.py scripts/quality/compile_failure_corpus.py   tests/test_failure_corpus.py tests/test_compile_failure_corpus.py
git commit -m "test: bind first reviewed LLM failure corpus"
~~~

## Task 3: Add the non-compensating A/B/C evaluator

**Files:**

- Create: scripts/quality/failure_ablation.py
- Create: tests/test_failure_ablation.py

The evaluator reads evidence produced elsewhere. It does not call an LLM, generate a figure, or accept publication quality.

- [ ] **Step 1: Write RED tests for comparability and scientific hard failure**

Create tests/test_failure_ablation.py with a helper that writes three manifests using schema figure-agent.failure-ablation-run.v1. Each manifest contains variant, model_contract_hash, input_packet_hash, budget_contract_hash, figure_family, findings, human_correction_minutes, intervention_count, clean_reproduction, and human_verdict.

Use this concrete helper:

~~~python
def _write_run(root: Path, variant: str, findings: list[dict[str, str]]) -> Path:
    path = root / f"{variant}.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.failure-ablation-run.v1",
                "variant": variant,
                "model_contract_hash": "sha256:" + "1" * 64,
                "input_packet_hash": "sha256:" + "2" * 64,
                "budget_contract_hash": "sha256:" + "3" * 64,
                "figure_family": "synthetic-ablation",
                "findings": findings,
                "human_correction_minutes": None,
                "intervention_count": 0,
                "clean_reproduction": True,
                "human_verdict": {"state": "pending"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def write_comparable_runs(root: Path) -> dict[str, Path]:
    typography = {
        "id": "TYPO001",
        "failure_class": "typography",
        "review_outcome": "confirmed_defect",
    }
    return {
        "raw": _write_run(root, "raw", [typography]),
        "verified": _write_run(root, "verified", [typography]),
        "repaired": _write_run(root, "repaired", []),
    }
~~~

Add these tests:

~~~python
def test_ablation_requires_exactly_raw_verified_repaired(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    paths.pop("repaired")
    with pytest.raises(FailureAblationError, match="variant_set_invalid"):
        evaluate_ablation(paths)


def test_ablation_rejects_mismatched_model_input_or_budget(tmp_path: Path) -> None:
    paths = write_comparable_runs(tmp_path)
    payload = yaml.safe_load(paths["verified"].read_text(encoding="utf-8"))
    payload["model_contract_hash"] = "sha256:" + "9" * 64
    paths["verified"].write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(FailureAblationError, match="comparison_contract_mismatch"):
        evaluate_ablation(paths)


def test_scientific_failure_cannot_be_compensated_by_visual_improvement(
    tmp_path: Path,
) -> None:
    paths = write_comparable_runs(tmp_path)
    payload = yaml.safe_load(paths["repaired"].read_text(encoding="utf-8"))
    payload["findings"].append(
        {
            "id": "SEM001",
            "failure_class": "semantic",
            "review_outcome": "confirmed_defect",
        }
    )
    paths["repaired"].write_text(yaml.safe_dump(payload), encoding="utf-8")
    report = evaluate_ablation(paths)
    assert report["variants"]["repaired"]["scientific_gate"] == "failed"
    assert report["product_claim"] == "not_authorized"


def test_reports_failure_reduction_without_claiming_acceptance(tmp_path: Path) -> None:
    report = evaluate_ablation(write_comparable_runs(tmp_path))
    assert report["schema"] == "figure-agent.failure-ablation-report.v1"
    assert report["deltas"]["verified_vs_raw"]["confirmed_defect_count"] <= 0
    assert report["deltas"]["repaired_vs_raw"]["confirmed_defect_count"] < 0
    assert report["publication_acceptance"] == "not_claimed"
~~~

- [ ] **Step 2: Run tests and verify RED**

~~~bash
uv run pytest tests/test_failure_ablation.py -q
~~~

Expected: FAIL because failure_ablation.py does not exist.

- [ ] **Step 3: Implement the evaluator**

Create scripts/quality/failure_ablation.py with:

~~~python
RUN_SCHEMA = "figure-agent.failure-ablation-run.v1"
REPORT_SCHEMA = "figure-agent.failure-ablation-report.v1"
VARIANTS = {"raw", "verified", "repaired"}
SCIENTIFIC_CLASSES = {"semantic", "relation"}


class FailureAblationError(ValueError):
    pass


def evaluate_ablation(run_paths: dict[str, Path]) -> dict[str, Any]:
    if set(run_paths) != VARIANTS:
        raise FailureAblationError("variant_set_invalid")
    runs = {name: _load_run(path, expected_variant=name) for name, path in run_paths.items()}
    keys = ("model_contract_hash", "input_packet_hash", "budget_contract_hash", "figure_family")
    if any(len({runs[name][key] for name in VARIANTS}) != 1 for key in keys):
        raise FailureAblationError("comparison_contract_mismatch")

    variants = {name: _summarize_run(runs[name]) for name in sorted(VARIANTS)}
    raw = variants["raw"]
    verified = variants["verified"]
    repaired = variants["repaired"]
    scientific_pass = all(
        item["scientific_gate"] == "passed" for item in variants.values()
    )
    human_complete = all(
        item["human_verdict_state"] == "recorded" for item in variants.values()
    )
    return {
        "schema": REPORT_SCHEMA,
        "variants": variants,
        "deltas": {
            "verified_vs_raw": _delta(verified, raw),
            "repaired_vs_raw": _delta(repaired, raw),
        },
        "product_claim": (
            "review_eligible" if scientific_pass and human_complete else "not_authorized"
        ),
        "publication_acceptance": "not_claimed",
    }
~~~

Helper rules:

- _load_run rejects symlinks and wrong schemas.
- _summarize_run counts confirmed defects by failure class.
- semantic or relation confirmed defects set scientific_gate to failed.
- missing named human verdict sets human_verdict_state to pending.
- null correction minutes remain null and never become zero.
- _delta subtracts only comparable numeric fields.
- no score may offset a scientific failure.

- [ ] **Step 4: Run focused verification**

~~~bash
uv run pytest tests/test_failure_ablation.py -q
uv run ruff check scripts/quality/failure_ablation.py tests/test_failure_ablation.py
git diff --check
~~~

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add scripts/quality/failure_ablation.py tests/test_failure_ablation.py
git commit -m "feat: compare raw verified and repaired figure runs"
~~~

## Task 4: Expose read-only corpus and ablation commands

**Files:**

- Modify: bin/fig-agent
- Create: tests/test_failure_first_cli.py

Commands:

~~~text
fig-agent failure-corpus --json
fig-agent failure-ablation --raw review/raw.yaml --verified review/verified.yaml --repaired review/repaired.yaml --json
~~~

Both commands are read-only. They write only when an explicit --output path beneath the current workspace is supplied. They never mutate figure source.

- [ ] **Step 1: Write failing CLI tests**

Create tests/test_failure_first_cli.py:

~~~python
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CLI = PLUGIN_ROOT / "bin" / "fig-agent"


def test_failure_corpus_cli_is_read_only() -> None:
    before = {
        path.relative_to(PLUGIN_ROOT): path.stat().st_mtime_ns
        for path in PLUGIN_ROOT.rglob("*")
        if path.is_file()
    }
    result = subprocess.run(
        [str(CLI), "failure-corpus", "--json"],
        cwd=PLUGIN_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.llm-failure-corpus.v1"
    after = {
        path.relative_to(PLUGIN_ROOT): path.stat().st_mtime_ns
        for path in PLUGIN_ROOT.rglob("*")
        if path.is_file()
    }
    assert after == before
~~~

Add this second test and helper in the same file:

~~~python
def _write_run(root: Path, variant: str, defect_count: int) -> Path:
    path = root / f"{variant}.yaml"
    payload = {
        "schema": "figure-agent.failure-ablation-run.v1",
        "variant": variant,
        "model_contract_hash": "sha256:" + "1" * 64,
        "input_packet_hash": "sha256:" + "2" * 64,
        "budget_contract_hash": "sha256:" + "3" * 64,
        "figure_family": "synthetic-cli",
        "findings": [
            {
                "id": f"TYPO-{index}",
                "failure_class": "typography",
                "review_outcome": "confirmed_defect",
            }
            for index in range(defect_count)
        ],
        "human_correction_minutes": None,
        "intervention_count": 0,
        "clean_reproduction": True,
        "human_verdict": {"state": "pending"},
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_failure_ablation_cli_keeps_acceptance_unclaimed(tmp_path: Path) -> None:
    paths = {
        "raw": _write_run(tmp_path, "raw", 2),
        "verified": _write_run(tmp_path, "verified", 2),
        "repaired": _write_run(tmp_path, "repaired", 1),
    }
    result = subprocess.run(
        [
            str(CLI),
            "failure-ablation",
            "--raw", str(paths["raw"]),
            "--verified", str(paths["verified"]),
            "--repaired", str(paths["repaired"]),
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.failure-ablation-report.v1"
    assert payload["publication_acceptance"] == "not_claimed"
~~~

- [ ] **Step 2: Run tests and verify RED**

~~~bash
uv run pytest tests/test_failure_first_cli.py -q
~~~

Expected: FAIL because the CLI does not recognize failure-corpus.

- [ ] **Step 3: Add focused command adapters**

In bin/fig-agent, add adapters that import from scripts/quality using the existing module-path setup:

~~~python
def _failure_corpus(rest: list[str]) -> int:
    import argparse
    import json
    import failure_corpus

    parser = argparse.ArgumentParser(prog="fig-agent failure-corpus")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(rest)
    payload = failure_corpus.load_failure_corpus(
        _paths().plugin_root / "benchmarks" / "llm_failure_corpus.yaml"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
~~~

Add the analogous _failure_ablation adapter and dispatch branches:

~~~python
def _failure_ablation(rest: list[str]) -> int:
    import argparse
    import json
    import failure_ablation

    parser = argparse.ArgumentParser(prog="fig-agent failure-ablation")
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--verified", type=Path, required=True)
    parser.add_argument("--repaired", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(rest)
    payload = failure_ablation.evaluate_ablation(
        {
            "raw": args.raw,
            "verified": args.verified,
            "repaired": args.repaired,
        }
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if command == "failure-corpus":
    return _failure_corpus(rest)
if command == "failure-ablation":
    return _failure_ablation(rest)
~~~

The ablation adapter requires --raw, --verified, and --repaired Path arguments and passes them directly to evaluate_ablation.

- [ ] **Step 4: Verify CLI and existing benchmark routing**

~~~bash
uv run pytest tests/test_failure_first_cli.py tests/test_quality_benchmark.py   tests/test_command_contract_docs.py -q
uv run ruff check bin/fig-agent tests/test_failure_first_cli.py
git diff --check
~~~

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add bin/fig-agent tests/test_failure_first_cli.py
git commit -m "feat: expose failure-first evidence commands"
~~~

## Task 5: Harden bounded repair around exact attribution and invariants

**Files:**

- Modify: scripts/quality/quality_patch_policy.py
- Modify: scripts/quality/quality_patch_plan.py
- Modify: scripts/quality/quality_patch_apply.py
- Modify: tests/test_quality_patch_policy.py
- Modify: tests/test_quality_patch_plan.py
- Modify: tests/test_quality_patch_apply.py

The current planner always writes selector confidence exact and semantic_guard allowed true. This task removes those invented assurances.

- [ ] **Step 1: Write RED policy tests**

Add to tests/test_quality_patch_policy.py:

~~~python
def test_safe_class_requires_exact_attribution_and_stable_selector() -> None:
    defect = safe_defect("text_overlap")
    defect["attribution"] = {"state": "ambiguous"}
    defect["selector_hint"] = {"kind": "line_range", "value": "4:4"}
    result = quality_patch_policy.classify_patchability(defect)
    assert result["state"] == "assisted_only"
    assert "exact_attribution_required" in result["blocked_codes"]


def test_safe_class_requires_protected_invariants() -> None:
    defect = safe_defect("text_overlap")
    defect["attribution"] = {"state": "exact"}
    defect["selector_hint"] = {
        "kind": "semantic_anchor",
        "selector_id": "panel_f.label.repulsion",
        "anchor_start": "% figure-agent:start panel_f.label.repulsion",
        "anchor_end": "% figure-agent:end panel_f.label.repulsion",
        "source_hash": "sha256:" + "1" * 64,
    }
    defect["protected_invariants"] = []
    result = quality_patch_policy.classify_patchability(defect)
    assert result["state"] == "assisted_only"
    assert "protected_invariants_required" in result["blocked_codes"]
~~~

- [ ] **Step 2: Run focused policy tests and verify RED**

~~~bash
uv run pytest tests/test_quality_patch_policy.py -q
~~~

Expected: FAIL because classify_patchability ignores attribution and invariants.

- [ ] **Step 3: Tighten policy classification**

In quality_patch_policy.py:

- retain all existing path/evidence checks;
- require attribution.state == exact for safe_candidate;
- require selector_hint.kind == semantic_anchor;
- require selector_id, anchor_start, anchor_end, and source_hash;
- require a non-empty protected_invariants list;
- leave may_edit false;
- return assisted_only, not human_required, for repairable but unbound defects.

Do not add SVG or TikZ coordinates to the policy.

- [ ] **Step 4: Write RED plan tests**

Add to tests/test_quality_patch_plan.py:

~~~python
def exact_anchor_fixture(workspace: Path) -> Path:
    fixture = workspace / "examples" / "quality_demo"
    fixture.mkdir(parents=True)
    (fixture / "quality_demo.tex").write_text(
        "% figure-agent:start panel_f.label.repulsion\n"
        "\\node at (0,0) {Coulomb repulsion};\n"
        "\\node at (2,0) {electrode separation};\n"
        "% figure-agent:end panel_f.label.repulsion\n",
        encoding="utf-8",
    )
    return fixture


def exact_anchor_ledger(fixture: Path) -> dict:
    source = fixture / "quality_demo.tex"
    return {
        "schema": "figure-agent.quality-defect-ledger.v1",
        "fixture": fixture.name,
        "ledger_hash": "sha256:" + "1" * 64,
        "defects": [
            {
                "id": "QD001",
                "defect_class": "text_overlap",
                "repair_family": "label_reflow",
                "affected_files": ["examples/quality_demo/quality_demo.tex"],
                "evidence": [{"uri": "figure://quality_demo/zoom/repulsion"}],
                "attribution": {"state": "exact"},
                "selector_hint": {
                    "kind": "semantic_anchor",
                    "selector_id": "panel_f.label.repulsion",
                    "anchor_start": "% figure-agent:start panel_f.label.repulsion",
                    "anchor_end": "% figure-agent:end panel_f.label.repulsion",
                    "source_hash": file_sha256(source),
                },
                "protected_invariants": [
                    "panel_f.coulomb_direction",
                    "panel_f.electrode_relation",
                ],
                "patchability": {"state": "safe_candidate"},
                "suggested_change": {
                    "operation_type": "tikz_coordinate_adjust",
                    "summary": "separate the repulsion label",
                    "patch": "",
                },
                "freshness": {
                    "audit_evidence_graph_hash": "sha256:" + "2" * 64,
                    "source_hashes": {
                        "examples/quality_demo/quality_demo.tex": file_sha256(source)
                    },
                },
            }
        ],
    }


def test_plan_preserves_selector_invariants_and_change_budget(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = exact_anchor_fixture(workspace)
    ledger = exact_anchor_ledger(fixture)
    plan = quality_patch_plan.build_quality_patch_plan(
        fixture.name,
        ledger,
        workspace_root=workspace,
    )
    operation = plan["operations"][0]
    assert operation["selector"]["selector_id"] == "panel_f.label.repulsion"
    assert operation["protected_invariants"] == [
        "panel_f.coulomb_direction",
        "panel_f.electrode_relation",
    ]
    assert operation["change_budget"] == {
        "max_source_blocks": 1,
        "max_changed_lines": 6,
        "max_rendered_pixel_ratio": 0.03,
    }
    assert operation["semantic_guard"]["allowed"] is False
    assert operation["semantic_guard"]["state"] == "pending_post_render_verification"


def test_plan_does_not_upgrade_line_range_to_exact(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _multiline_fixture(workspace)
    ledger = _multiline_ledger(fixture)
    ledger["defects"][0]["patchability"]["state"] = "assisted_only"
    plan = quality_patch_plan.build_quality_patch_plan(
        "quality_demo",
        ledger,
        workspace_root=workspace,
    )
    assert plan["operations"] == []
    assert plan["refusals"][0]["code"] == "exact_selector_required"
~~~

- [ ] **Step 5: Implement the stricter plan contract**

In quality_patch_plan.py:

- copy selector fields without inventing confidence;
- refuse non-semantic_anchor selectors;
- copy protected_invariants;
- emit repair_family from the defect;
- emit the fixed initial change budget shown above;
- set semantic_guard to pending_post_render_verification;
- retain required compile and status commands;
- retain reverse_patch rollback.

The initial implementation remains TikZ-source-only. SVG repair is a later slice only after the same contract passes the first real pilot.

- [ ] **Step 6: Write RED apply tests**

Add to tests/test_quality_patch_apply.py:

~~~python
def exact_anchor_fixture(workspace: Path) -> Path:
    fixture = workspace / "examples" / "quality_demo"
    fixture.mkdir(parents=True)
    (fixture / "quality_demo.tex").write_text(
        "% figure-agent:start panel_f.label.repulsion\n"
        "\\node (label-a) at (0,0) {Old Label};\n"
        "\\node at (1,0) {Coulomb repulsion};\n"
        "\\node at (2,0) {electrode separation};\n"
        "% figure-agent:end panel_f.label.repulsion\n",
        encoding="utf-8",
    )
    return fixture


def exact_anchor_plan(fixture: Path) -> dict:
    plan = _plan(fixture)
    operation = plan["operations"][0]
    relative = f"examples/{fixture.name}/{fixture.name}.tex"
    operation["proposed_change"]["patch"] = (
        f"--- {relative}\n"
        f"+++ {relative}\n"
        "@@ -2 +2 @@\n"
        "-\\node (label-a) at (0,0) {Old Label};\n"
        "+\\node (label-a) at (0.2,0) {Old Label};\n"
    )
    operation["selector"] = {
        "kind": "semantic_anchor",
        "selector_id": "panel_f.label.repulsion",
        "anchor_start": "% figure-agent:start panel_f.label.repulsion",
        "anchor_end": "% figure-agent:end panel_f.label.repulsion",
        "source_hash": file_sha256(fixture / f"{fixture.name}.tex"),
    }
    operation["repair_family"] = "label_reflow"
    operation["protected_invariants"] = [
        "Coulomb repulsion",
        "electrode separation",
    ]
    operation["change_budget"] = {
        "max_source_blocks": 1,
        "max_changed_lines": 6,
        "max_rendered_pixel_ratio": 0.03,
    }
    operation["semantic_guard"] = {
        "allowed": False,
        "state": "pending_post_render_verification",
    }
    return plan


def patch_that_changes_relation_label(fixture: Path) -> str:
    relative = f"examples/{fixture.name}/{fixture.name}.tex"
    return (
        f"--- {relative}\n"
        f"+++ {relative}\n"
        "@@ -3 +3 @@\n"
        "-\\node at (1,0) {Coulomb repulsion};\n"
        "+\\node at (1,0) {changed relation};\n"
    )


def test_apply_refuses_changed_protected_invariant(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = exact_anchor_fixture(workspace)
    plan = exact_anchor_plan(fixture)
    plan["operations"][0]["proposed_change"]["patch"] = patch_that_changes_relation_label(
        fixture
    )
    path = _write_plan(fixture, plan)
    with pytest.raises(
        quality_patch_apply.QualityPatchApplyError,
        match="protected_invariant_changed",
    ):
        quality_patch_apply.apply_quality_patch_plan(
            fixture.name,
            plan_path=path,
            workspace_root=workspace,
            apply=True,
        )


def test_apply_receipt_keeps_acceptance_unclaimed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = exact_anchor_fixture(workspace)
    path = _write_plan(fixture, exact_anchor_plan(fixture))
    result = quality_patch_apply.apply_quality_patch_plan(
        fixture.name,
        plan_path=path,
        workspace_root=workspace,
        apply=True,
    )
    assert result["publication_acceptance"] == "not_claimed"
    assert result["post_render_verification"] == "pending"
~~~

- [ ] **Step 7: Implement invariant-preserving apply**

Before writing source:

- resolve the declared anchor block exactly once;
- confirm its source hash;
- apply the patch in memory;
- reject edits outside the one anchor block;
- reject any change to literal protected invariant tokens declared in the operation;
- reject more than max_changed_lines;
- write source and rollback only after all preflight checks pass.

The apply receipt records publication_acceptance not_claimed and post_render_verification pending. It never marks the repair successful before compile, render, detector recheck, and human review.

- [ ] **Step 8: Run repair regression tests**

~~~bash
uv run pytest tests/test_quality_patch_policy.py tests/test_quality_patch_plan.py   tests/test_quality_patch_apply.py -q
uv run ruff check scripts/quality/quality_patch_policy.py   scripts/quality/quality_patch_plan.py scripts/quality/quality_patch_apply.py   tests/test_quality_patch_policy.py tests/test_quality_patch_plan.py   tests/test_quality_patch_apply.py
git diff --check
~~~

Expected: PASS.

- [ ] **Step 9: Commit**

~~~bash
git add scripts/quality/quality_patch_policy.py   scripts/quality/quality_patch_plan.py scripts/quality/quality_patch_apply.py   tests/test_quality_patch_policy.py tests/test_quality_patch_plan.py   tests/test_quality_patch_apply.py
git commit -m "fix: require exact bounded figure repairs"
~~~

## Task 6: Run the first complete failure-first vertical slice

**Files:**

- Create: examples/failure_first_label_repair_demo/spec.yaml
- Create: examples/failure_first_label_repair_demo/briefing.md
- Create: examples/failure_first_label_repair_demo/failure_first_label_repair_demo.tex
- Create: examples/failure_first_label_repair_demo/semantic_regions.yaml
- Create: examples/failure_first_label_repair_demo/benchmark_contract.yaml
- Create: examples/failure_first_label_repair_demo/review/ablation/
- Create: tests/test_failure_first_vertical_slice.py
- Modify: benchmarks/quality_suites.yaml

This fixture tests the control system, not drawing quality. It contains one deliberate label/leader collision inside a stable semantic anchor and two protected relation labels. The three variants use identical source, model/input/budget receipts:

- raw: collision present;
- verified: collision detected and exactly attributed, source unchanged;
- repaired: one bounded label reflow, protected relations unchanged.

- [ ] **Step 1: Write the RED fixture test**

Create tests/test_failure_first_vertical_slice.py:

~~~python
def test_vertical_slice_has_comparable_raw_verified_repaired_evidence() -> None:
    fixture = PLUGIN_ROOT / "examples" / "failure_first_label_repair_demo"
    report = evaluate_ablation(
        {
            name: fixture / "review" / "ablation" / f"{name}.yaml"
            for name in ("raw", "verified", "repaired")
        }
    )
    assert report["variants"]["raw"]["confirmed_defect_count"] == 1
    assert report["variants"]["verified"]["confirmed_defect_count"] == 1
    assert report["variants"]["repaired"]["confirmed_defect_count"] == 0
    assert report["deltas"]["repaired_vs_raw"]["confirmed_defect_count"] == -1
    assert report["publication_acceptance"] == "not_claimed"


def test_repaired_source_preserves_declared_relations() -> None:
    fixture = PLUGIN_ROOT / "examples" / "failure_first_label_repair_demo"
    source = (fixture / "failure_first_label_repair_demo.tex").read_text(encoding="utf-8")
    assert "Coulomb repulsion" in source
    assert "electrode separation" in source
~~~

- [ ] **Step 2: Run the test and verify RED**

~~~bash
uv run pytest tests/test_failure_first_vertical_slice.py -q
~~~

Expected: FAIL because the fixture does not exist.

- [ ] **Step 3: Create the smallest semantic fixture**

The TeX source uses one semantic block:

~~~tex
% figure-agent:start panel_a.label.repulsion
\node[draw, rounded corners=1pt] (electrode) at (0,0) {electrode};
\node (sample) at (3,0) {sample};
\draw[->] (electrode) -- node[above] {electrode separation} (sample);
\draw[->] (sample) -- ++(0,1.2) node[right] {Coulomb repulsion};
\node[anchor=west] at (2.95,1.2) {repulsion label};
% figure-agent:end panel_a.label.repulsion
~~~

The raw evidence marks the intentional label/leader collision. The verified evidence adds exact attribution and a repair candidate without changing source. The repaired source moves only repulsion label within the anchor block.

Do not add publication acceptance, a taste score, or a claim that this synthetic figure proves general quality improvement.

- [ ] **Step 4: Compile and generate evidence**

Run:

~~~bash
bash scripts/compile.sh   examples/failure_first_label_repair_demo/failure_first_label_repair_demo.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh   examples/failure_first_label_repair_demo/failure_first_label_repair_demo.tex
fig-agent failure-ablation   --raw examples/failure_first_label_repair_demo/review/ablation/raw.yaml   --verified examples/failure_first_label_repair_demo/review/ablation/verified.yaml   --repaired examples/failure_first_label_repair_demo/review/ablation/repaired.yaml   --json
~~~

Expected: compile PASS, strict PASS, report shows one defect removed only in repaired, publication_acceptance not_claimed.

- [ ] **Step 5: Add the suite and run affected tests**

Add failure_first_label_repair_demo to a new failure-first-smoke suite in benchmarks/quality_suites.yaml.

Run:

~~~bash
uv run pytest tests/test_failure_corpus.py tests/test_compile_failure_corpus.py   tests/test_failure_ablation.py tests/test_failure_first_cli.py   tests/test_quality_patch_policy.py tests/test_quality_patch_plan.py   tests/test_quality_patch_apply.py tests/test_failure_first_vertical_slice.py   tests/test_quality_benchmark.py tests/test_document_authority.py   tests/test_release_contract.py -q
uv run ruff check scripts/quality/failure_corpus.py   scripts/quality/compile_failure_corpus.py scripts/quality/failure_ablation.py   scripts/quality/quality_patch_policy.py scripts/quality/quality_patch_plan.py   scripts/quality/quality_patch_apply.py bin/fig-agent tests/test_failure_*.py   tests/test_quality_patch_policy.py tests/test_quality_patch_plan.py   tests/test_quality_patch_apply.py
uv run python -m compileall -q scripts/quality tests
git diff --check
~~~

Expected: PASS.

- [ ] **Step 6: Commit**

~~~bash
git add examples/failure_first_label_repair_demo benchmarks/quality_suites.yaml   tests/test_failure_first_vertical_slice.py
git commit -m "test: prove first failure-first repair slice"
~~~

## Task 7: Bind a real complex-panel pilot without claiming success

**Files:**

- Create: examples/fig1_failure_first_panel_f_pilot/
- Create: tests/test_fig1_failure_first_panel_f_pilot.py
- Modify: benchmarks/llm_failure_sources.yaml
- Modify: benchmarks/llm_failure_corpus.yaml

Fork tracked editable source from the latest accepted or human-reviewed Fig1-family artifact only after recording its source commit and tree hash. Do not read user untracked files or another worktree build directory. The pilot must use a tracked Fig1-family editable source and a predeclared comparison protocol.

- [ ] **Step 1: Pin authority and geometry**

The pilot authority manifest includes:

~~~yaml
selector_id: panel_f.metal_contact
anchor_start: "% figure-agent:start panel_f.metal_contact"
anchor_end: "% figure-agent:end panel_f.metal_contact"
coordinate_space: pdf_cm
page_index: 0
render_geometry_hash: null
review_input_hash: null
publication_acceptance: not_claimed
~~~

Every panel reference used by the pilot must also bind a tracked source path,
source commit, local path, and exact byte hash. A same-named untracked copy is
not reference authority even when its pixels appear identical.

Before validation, render_geometry_hash and review_input_hash are null with
hash_authority: generated_receipt. The validator computes both hashes and writes
them into a generated receipt. The committed source manifest records source
commit and tree hash. Do not hand-type hashes into the tracked manifest.

- [ ] **Step 2: Write RED tests before importing the pilot**

Tests require:

- exact attribution to panel_f.metal_contact;
- required objects and forbidden implications, including no invented ground;
- one bounded repair family;
- protected cantilever/electrode/force relations;
- raw, verified, and repaired manifests with identical model/input/budget hashes;
- a focused crop and overlay for each state;
- stale audit-crop manifests rejected when a newer build render exists;
- human correction minutes left null until measured;
- publication acceptance not claimed.

- [ ] **Step 3: Build evidence without extending fixture-specific search**

Use failure_corpus.py, failure_ablation.py, visual_finding_attribution.py, visual_finding_artifacts.py, quality_patch_policy.py, quality_patch_plan.py, and quality_patch_apply.py. Do not add a template, coordinate constant, or branch to quality_search.py.

- [ ] **Step 4: Compile and verify from a clean checkout**

Run from plugins/figure-agent:

~~~bash
bash scripts/compile.sh examples/fig1_failure_first_panel_f_pilot/fig1_failure_first_panel_f_pilot.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh   examples/fig1_failure_first_panel_f_pilot/fig1_failure_first_panel_f_pilot.tex
uv run pytest tests/test_fig1_failure_first_panel_f_pilot.py   tests/test_failure_first_vertical_slice.py tests/test_failure_ablation.py -q
git diff --check
~~~

Expected: machine-valid or review-ready only.

- [ ] **Step 5: Stop at the human boundary**

A named human reviews whole figure, Panel F, object/relation crop, and contact zoom. Record scientific fidelity, defect presence, correction minutes, and visual verdict separately. A machine gate cannot fill these values.

Commit only the actual state:

~~~bash
git add examples/fig1_failure_first_panel_f_pilot   benchmarks/llm_failure_sources.yaml benchmarks/llm_failure_corpus.yaml   tests/test_fig1_failure_first_panel_f_pilot.py
git commit -m "test: stage real failure-first Panel F review"
~~~

## Legacy evidence boundaries retained

The previous plan completed or staged important contracts that remain valid evidence:

- tracked editable source and tracked Fig1-family editable source requirements;
- reference source commit and tree hash;
- stable selector fields such as selector_id: and anchor_start:;
- coordinate_space: pdf_cm, page_index:, and render_geometry_hash:;
- rejection of network access and external URLs;
- bound review_input_hash and aggregate review-input hash;
- the predeclared comparison protocol;
- Task 15: Validate clean-room direct-SVG input packets;
- target_crop_forbidden and blocked_pending_independent_semantic_packet;
- Run two cold reproductions only for a passing claim.

These are retained boundaries, not the new task order. Historical direct-SVG and grammar artifacts remain immutable evidence. No unfinished human verdict is converted into success.

Legacy schema ownership remains unchanged for
figure-agent.direct-svg-crop-authority.v1,
figure-agent.direct-svg-packet.v1,
figure-agent.direct-svg-task20-status.v1,
figure-agent.illustration-backend-profile.v1,
figure-agent.illustration-grammar.v1,
figure-agent.illustration-grammar.v2,
figure-agent.illustration-instance.v1, and
figure-agent.semantic-regions.v1. Their implementation modules and historical
tests remain the runtime authority for those artifacts.

## Completion boundary for this plan

The first plan is complete only when:

1. the failure-first authority test passes;
2. a hash-bound reviewed corpus covers at least typography, geometry, finish, style, and one accepted false positive;
3. the A/B/C evaluator rejects incomparable runs and non-compensating scientific failures;
4. exact attribution and protected invariants are required before a repair candidate can be applied;
5. the synthetic vertical slice proves the evidence and rollback machinery;
6. the real Panel F pilot is reproducible from tracked inputs;
7. whole, panel, object/relation, and zoom evidence exist for the real pilot; and
8. its actual human state is recorded without publication overclaim.

This plan does not promote SVG, retire TikZ, generalize from one fixture, or authorize another illustration grammar. A second materially different figure family is a later plan, opened only when the real Panel F pilot shows a reusable failure reduction rather than a fixture-specific polish win.
