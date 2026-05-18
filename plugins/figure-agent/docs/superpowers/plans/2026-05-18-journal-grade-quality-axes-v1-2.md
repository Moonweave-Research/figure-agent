# Journal-Grade Quality Axes v1.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `/fig_critique` and `/fig_adjudicate` so v1.2 critiques must include journal-grade `quality_axes` while preserving v1/v1.1 legacy parsing.

**Architecture:** Keep the first slice narrow: `critique_brief.py` emits the v1.2 prompt/schema, `quality_manifest.py` owns the rubric bump, and `critique_adjudication.py` validates v1.2 shape before scaffolding. `/fig_loop` ingestion is deliberately deferred to a follow-up slice after the v1.2 critique contract is stable.

**Tech Stack:** Python stdlib, PyYAML, pytest, ruff, existing figure-agent command markdown.

---

## Source Of Truth

Read these first:

- `plugins/figure-agent/docs/superpowers/issues/2026-05-18-issue-6b-journal-grade-quality-axes-v1-2.md`
- `plugins/figure-agent/docs/superpowers/specs/2026-05-18-journal-grade-quality-axes-v1-2-design.md`
- `plugins/figure-agent/docs/superpowers/specs/2026-05-18-critique-structural-audit-v1-1-design.md`
- `plugins/figure-agent/scripts/critique_brief.py`
- `plugins/figure-agent/scripts/critique_adjudication.py`
- `plugins/figure-agent/scripts/quality_manifest.py`
- `plugins/figure-agent/tests/test_critique_brief.py`
- `plugins/figure-agent/tests/test_critique_adjudication.py`

## File Structure

- Modify: `plugins/figure-agent/scripts/critique_brief.py`
  - Add journal-grade quality axes prompt section.
  - Add v1.2 `quality_axes` YAML output schema.
  - Bump emitted schema from `figure-agent.critique.v1.1` to `figure-agent.critique.v1.2`.
- Modify: `plugins/figure-agent/scripts/quality_manifest.py`
  - Bump `CRITIQUE_RUBRIC_VERSION` to `figure-agent.critique-rubric.v1.2`.
- Modify: `plugins/figure-agent/scripts/critique_adjudication.py`
  - Add `CRITIQUE_SCHEMA_V1_2`.
  - Validate v1.2 `audit_enumeration` and `quality_axes`.
  - Preserve v1 legacy warnings and v1.1 audit validation.
- Modify: `plugins/figure-agent/commands/fig_critique.md`
  - Document v1.2 schema and required `quality_axes`.
- Modify: `plugins/figure-agent/tests/test_critique_brief.py`
  - Add prompt/schema tests for journal-grade axes.
  - Update schema/rubric expectations to v1.2.
- Modify: `plugins/figure-agent/tests/test_critique_adjudication.py`
  - Add v1.2 valid/invalid quality-axis validation tests.
- Modify: `plugins/figure-agent/tests/test_status.py`
  - Update hashed critique helper to v1.2/rubric v1.2 and include minimal `quality_axes`.
- Modify: `plugins/figure-agent/tests/test_run_export.py`
  - Update hashed critique helper to v1.2/rubric v1.2 and include minimal `quality_axes`.

Do not modify existing `examples/<name>/critique.md` files in this slice.

## Task 1: Add Brief Contract Tests

**Files:**

- Modify: `plugins/figure-agent/tests/test_critique_brief.py`

- [ ] **Step 1: Add a required-axis list constant in the test file**

Add near the imports:

```python
QUALITY_AXIS_NAMES = (
    "message_storyline",
    "panel_role_coherence",
    "subregion_integration",
    "component_fidelity",
    "scientific_plausibility",
    "composition_layout",
    "label_annotation_semantics",
    "journal_polish",
    "reference_fidelity",
    "publication_readiness",
)
```

- [ ] **Step 2: Add the failing prompt-section test**

Add:

```python
def test_critique_brief_includes_journal_grade_quality_axes(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Journal-Grade Quality Axes (host LLM MUST evaluate)" in brief
    assert "### 1. Message and Storyline" in brief
    assert "### 2. Panel Role Coherence" in brief
    assert "### 3. Sub-region Integration" in brief
    assert "### 4. Component Fidelity" in brief
    assert "### 5. Scientific Plausibility" in brief
    assert "### 6. Composition and Layout" in brief
    assert "### 7. Label and Annotation Semantics" in brief
    assert "### 8. Journal Polish" in brief
    assert "### 9. Reference Fidelity" in brief
    assert "### 10. Publication Readiness" in brief
```

- [ ] **Step 3: Update existing schema/rubric expectations**

Change:

```python
assert "schema: figure-agent.critique.v1.1" in brief
```

to:

```python
assert "schema: figure-agent.critique.v1.2" in brief
```

Change:

```python
assert "rubric_version: figure-agent.critique-rubric.v1.1" in brief
```

to:

```python
assert "rubric_version: figure-agent.critique-rubric.v1.2" in brief
```

- [ ] **Step 4: Extend the metadata test to require `quality_axes`**

In `test_critique_brief_output_format_includes_hash_manifest_metadata`, add:

```python
assert "quality_axes:" in brief
for axis_name in QUALITY_AXIS_NAMES:
    assert f"  {axis_name}:" in brief
assert "verdict: pass | needs_patch | needs_human | block | not_applicable" in brief
assert "confidence: low | medium | high" in brief
assert "recommended_action: none | patch | human_review | revise_briefing | block_release" in brief
```

- [ ] **Step 5: Verify RED**

Run from `plugins/figure-agent`:

```bash
uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_journal_grade_quality_axes tests/test_critique_brief.py::test_critique_brief_output_format_includes_hash_manifest_metadata tests/test_critique_brief.py::test_critique_brief_includes_rubric_sections_A_and_B
```

Expected: FAIL because the brief still emits v1.1 and has no journal-grade quality axes section.

## Task 2: Implement Brief v1.2 Output

**Files:**

- Modify: `plugins/figure-agent/scripts/quality_manifest.py`
- Modify: `plugins/figure-agent/scripts/critique_brief.py`

- [ ] **Step 1: Bump the rubric version**

In `scripts/quality_manifest.py`, change:

```python
CRITIQUE_RUBRIC_VERSION = "figure-agent.critique-rubric.v1.2"
```

- [ ] **Step 2: Add shared quality-axis constants**

In `scripts/critique_brief.py`, near `_PHYSICAL_CHECK_VALUES`, add:

```python
_QUALITY_AXIS_NAMES = (
    "message_storyline",
    "panel_role_coherence",
    "subregion_integration",
    "component_fidelity",
    "scientific_plausibility",
    "composition_layout",
    "label_annotation_semantics",
    "journal_polish",
    "reference_fidelity",
    "publication_readiness",
)
_QUALITY_VERDICT_VALUES = "pass | needs_patch | needs_human | block | not_applicable"
_QUALITY_CONFIDENCE_VALUES = "low | medium | high"
_QUALITY_ACTION_VALUES = "none | patch | human_review | revise_briefing | block_release"
_PANEL_ROLE_VALUES = "setup | mechanism | result | comparison | control | zoom | model | workflow | context"
_PANEL_ROLE_QUALITY_VALUES = "clear | weak | missing | redundant"
```

- [ ] **Step 3: Add the journal quality axes prompt helper**

Add near `_mandatory_audit_checklists()`:

```python
def _journal_quality_axes() -> str:
    return """## Journal-Grade Quality Axes (host LLM MUST evaluate)

After completing `audit_enumeration`, evaluate every quality axis below under
top-level YAML field `quality_axes`. Do not collapse these axes into one opaque
score. Every `pass`, `needs_patch`, `needs_human`, or `block` verdict needs
concrete visible, briefing, reference, theory-guard, or finding evidence.
Use `not_applicable` only when the figure lacks the relevant input or structure.

### 1. Message and Storyline
Evaluate the one-sentence figure message, first-read order, relation to the
manuscript claim, missing story bridges, main-conclusion prominence, and
decorative/non-explanatory content.

### 2. Panel Role Coherence
Classify every panel role as setup, mechanism, result, comparison, control,
zoom, model, workflow, or context. Flag missing, redundant, weak, or misordered
panel roles.

### 3. Sub-region Integration
If sub-region context exists, evaluate active sub-region ids, integration with
stable regions, global imbalance from local fixes, detail-level mismatch, and
callout/zoom link correctness.

### 4. Component Fidelity
Evaluate component identity, support/mount/frame/stage, material boundaries,
wire/cable/arrow endpoints, standard missing parts, and whether omissions are
acceptable schematic simplifications.

### 5. Scientific Plausibility
Evaluate arrows, fields, flows, forces, charge motion, current, energy ordering,
scale/proximity, material/interface meaning, theory-guard invariants, and
mechanism-level label/object conflicts.

### 6. Composition and Layout
Evaluate visual hierarchy, reading path, spacing, alignment, density, white
space, relative scale, thumbnail readability, and whether the figure reads as
one coherent system instead of assembled fragments.

### 7. Label and Annotation Semantics
Evaluate every label-target audit item, terminology consistency, leader-line
necessity, label density, cross-panel label grammar, and annotation usefulness
versus clutter.

### 8. Journal Polish
Evaluate typography hierarchy, line-weight economy, palette economy, semantic
color consistency, export-scale contrast, schematic restraint, and absence of
decorative noise.

### 9. Reference Fidelity
When references exist, evaluate role/topology transfer, per-panel reference
crop comparisons, preserved key relations, intentional omissions versus
incomplete drawing, hallucinated additions, and source limitations.

### 10. Publication Readiness
Conservatively summarize whether the figure passes, needs a patch, needs human
review, or blocks release. This summary cannot be less severe than any
applicable upstream quality axis.
"""
```

- [ ] **Step 4: Add the output-schema helper**

Add near `_journal_quality_axes()`:

```python
def _quality_axis_schema(axis_name: str, *, evidence: str, rationale: str) -> str:
    return "\n".join(
        [
            f"  {axis_name}:",
            f"    verdict: {_QUALITY_VERDICT_VALUES}",
            f"    confidence: {_QUALITY_CONFIDENCE_VALUES}",
            f"    rationale: \"<{rationale}>\"",
            f"    evidence: \"<{evidence}>\"",
            "    blocking_items: []",
            f"    recommended_action: {_QUALITY_ACTION_VALUES}",
        ]
    )


def _quality_axes_schema() -> str:
    axes = [
        _quality_axis_schema(
            "message_storyline",
            rationale="message/story verdict rationale",
            evidence="visible evidence, briefing/spec reference, or finding id",
        ),
        "\n".join(
            [
                "  panel_role_coherence:",
                f"    verdict: {_QUALITY_VERDICT_VALUES}",
                f"    confidence: {_QUALITY_CONFIDENCE_VALUES}",
                "    rationale: \"<panel role coherence summary>\"",
                "    evidence: \"<panel ids and visual evidence>\"",
                "    panel_roles:",
                "      - panel_id: \"<id>\"",
                f"        role: {_PANEL_ROLE_VALUES}",
                f"        role_quality: {_PANEL_ROLE_QUALITY_VALUES}",
                "        rationale: \"<one-line>\"",
                "    blocking_items: []",
                f"    recommended_action: {_QUALITY_ACTION_VALUES}",
            ]
        ),
        _quality_axis_schema(
            "subregion_integration",
            rationale="sub-region/global integration summary",
            evidence="subregion id, log evidence, or visible evidence",
        ),
        _quality_axis_schema(
            "component_fidelity",
            rationale="component fidelity summary",
            evidence="component audit ids or visible evidence",
        ),
        _quality_axis_schema(
            "scientific_plausibility",
            rationale="scientific plausibility summary",
            evidence="theory guard, briefing invariant, or visible evidence",
        ),
        _quality_axis_schema(
            "composition_layout",
            rationale="layout/composition summary",
            evidence="visible evidence, checker output, or finding id",
        ),
        _quality_axis_schema(
            "label_annotation_semantics",
            rationale="label semantics summary",
            evidence="label-target audit ids or visible evidence",
        ),
        _quality_axis_schema(
            "journal_polish",
            rationale="polish summary",
            evidence="visible evidence or export-scale issue",
        ),
        _quality_axis_schema(
            "reference_fidelity",
            rationale="reference fidelity summary",
            evidence="reference path, panel id, or reference_pack note",
        ),
        _quality_axis_schema(
            "publication_readiness",
            rationale="conservative readiness summary",
            evidence="axis verdict summary",
        ),
    ]
    return "quality_axes:\n" + "\n".join(axes)
```

- [ ] **Step 5: Insert the new prompt section**

In `generate_for()`, after `{_mandatory_audit_checklists()}` and before `## Critique rubric`, insert:

```python
{_journal_quality_axes()}
```

The returned brief sequence should become:

```markdown
## Source under review (TikZ)
...

## Mandatory Audit Checklists (host LLM MUST enumerate)
...

## Journal-Grade Quality Axes (host LLM MUST evaluate)
...

## Critique rubric
```

- [ ] **Step 6: Update the output schema**

Change output prose from `schema v1.1` to `schema v1.2`.

Change:

```yaml
schema: figure-agent.critique.v1.1
```

to:

```yaml
schema: figure-agent.critique.v1.2
```

After the `audit_enumeration` block and before `panels:`, insert:

```python
{_quality_axes_schema()}
```

Add this instruction after the schema block:

```markdown
Every `needs_patch` and `block` quality axis must expose a concrete
`blocking_items` entry and either a normal panel/top-level finding or a
non-patch `recommended_action` such as `human_review`, `revise_briefing`, or
`block_release`. `publication_readiness.verdict` must not be less severe than
any applicable upstream quality axis.
```

- [ ] **Step 7: Verify GREEN for brief tests**

Run:

```bash
uv run pytest -q tests/test_critique_brief.py
```

Expected: PASS.

## Task 3: Add v1.2 Quality-Axis Validation Tests

**Files:**

- Modify: `plugins/figure-agent/tests/test_critique_adjudication.py`

- [ ] **Step 1: Add v1.2 helper constants**

Add near `_complete_v1_1_audit_yaml()`:

```python
QUALITY_AXIS_NAMES = (
    "message_storyline",
    "panel_role_coherence",
    "subregion_integration",
    "component_fidelity",
    "scientific_plausibility",
    "composition_layout",
    "label_annotation_semantics",
    "journal_polish",
    "reference_fidelity",
    "publication_readiness",
)
```

- [ ] **Step 2: Add a complete quality axes helper**

Add:

```python
def _quality_axis_yaml(
    name: str,
    *,
    verdict: str = "pass",
    confidence: str = "high",
    recommended_action: str = "none",
    blocking_items: tuple[str, ...] = (),
) -> str:
    blocking_yaml = (
        "[]"
        if not blocking_items
        else "\n" + "".join(f"      - {item}\n" for item in blocking_items).rstrip()
    )
    return (
        f"  {name}:\n"
        f"    verdict: {verdict}\n"
        f"    confidence: {confidence}\n"
        f"    rationale: {name} rationale\n"
        f"    evidence: {name} evidence\n"
        f"    blocking_items: {blocking_yaml}\n"
        f"    recommended_action: {recommended_action}\n"
    )


def _complete_v1_2_quality_axes_yaml(
    *,
    axis_overrides: dict[str, str] | None = None,
) -> str:
    axis_overrides = axis_overrides or {}
    parts = ["quality_axes:\n"]
    for axis_name in QUALITY_AXIS_NAMES:
        if axis_name in axis_overrides:
            parts.append(axis_overrides[axis_name])
            continue
        if axis_name == "panel_role_coherence":
            parts.append(
                "  panel_role_coherence:\n"
                "    verdict: pass\n"
                "    confidence: high\n"
                "    rationale: panel roles are coherent\n"
                "    evidence: panel A is setup\n"
                "    panel_roles:\n"
                "      - panel_id: A\n"
                "        role: setup\n"
                "        role_quality: clear\n"
                "        rationale: panel A introduces the apparatus\n"
                "    blocking_items: []\n"
                "    recommended_action: none\n"
            )
        elif axis_name == "publication_readiness":
            parts.append(
                _quality_axis_yaml(
                    "publication_readiness",
                    verdict="pass",
                    confidence="high",
                    recommended_action="none",
                )
            )
        else:
            parts.append(_quality_axis_yaml(axis_name))
    return "".join(parts)
```

- [ ] **Step 3: Add a v1.2 critique helper**

Add:

```python
def _write_v1_2_critique_with_quality_axes(
    fig_dir: Path,
    *,
    audit_yaml: str | None = None,
    quality_axes_yaml: str | None = None,
) -> Path:
    critique = fig_dir / "critique.md"
    critique.write_text(
        "---\n"
        "schema: figure-agent.critique.v1.2\n"
        "fixture: demo_fig\n"
        f"{audit_yaml or _complete_v1_1_audit_yaml()}"
        f"{quality_axes_yaml or _complete_v1_2_quality_axes_yaml()}"
        "findings:\n"
        "  - id: C001\n"
        "    status: open\n"
        "    tex_lines: [10, 20]\n"
        "    observation: needs review\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    return critique
```

- [ ] **Step 4: Add the valid v1.2 scaffold test**

Add:

```python
def test_build_adjudication_scaffold_accepts_v1_2_quality_axes(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(fig_dir)

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)
    assert [decision["finding_id"] for decision in scaffold["decisions"]] == ["C001"]
```

- [ ] **Step 5: Add missing/invalid field tests**

Add:

```python
def test_build_adjudication_scaffold_rejects_v1_2_missing_quality_axis(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        _quality_axis_yaml("journal_polish"),
        "",
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="journal_polish"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_invalid_verdict(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    verdict: pass\n",
        "    verdict: excellent\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="verdict"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_invalid_confidence(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    confidence: high\n",
        "    confidence: certain\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="confidence"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_invalid_recommended_action(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    recommended_action: none\n",
        "    recommended_action: auto_fix\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="recommended_action"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_non_list_blocking_items(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    blocking_items: []\n",
        "    blocking_items: hidden issue\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="blocking_items"):
        build_adjudication_scaffold(fig_dir)
```

- [ ] **Step 6: Add consistency-rule tests**

Add:

```python
def test_build_adjudication_scaffold_rejects_v1_2_empty_evidence_for_pass(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    evidence: message_storyline evidence\n",
        "    evidence: \"\"\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="evidence"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_patch_without_blocking_item(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "composition_layout": _quality_axis_yaml(
                "composition_layout",
                verdict="needs_patch",
                recommended_action="patch",
                blocking_items=(),
            )
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="blocking_items"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_action_conflict(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "scientific_plausibility": _quality_axis_yaml(
                "scientific_plausibility",
                verdict="needs_human",
                recommended_action="patch",
                blocking_items=("Mechanism requires domain review.",),
            )
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="recommended_action"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_readiness_less_severe_than_axis(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "journal_polish": _quality_axis_yaml(
                "journal_polish",
                verdict="block",
                recommended_action="block_release",
                blocking_items=("Export-scale text is unreadable.",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="pass",
                recommended_action="none",
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="publication_readiness"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_readiness_not_applicable_with_axes(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="not_applicable",
                recommended_action="none",
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="publication_readiness"):
        build_adjudication_scaffold(fig_dir)
```

- [ ] **Step 7: Add panel-role validation tests**

Add:

```python
def test_build_adjudication_scaffold_rejects_v1_2_invalid_panel_role(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "        role: setup\n",
        "        role: decoration\n",
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="panel_roles"):
        build_adjudication_scaffold(fig_dir)
```

- [ ] **Step 8: Verify RED**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py
```

Expected: FAIL because v1.2 validation does not exist yet.

## Task 4: Implement v1.2 Quality-Axis Validation

**Files:**

- Modify: `plugins/figure-agent/scripts/critique_adjudication.py`

- [ ] **Step 1: Add schema and enum constants**

Near the existing schema constants, add:

```python
CRITIQUE_SCHEMA_V1_2 = "figure-agent.critique.v1.2"
_QUALITY_AXIS_NAMES = (
    "message_storyline",
    "panel_role_coherence",
    "subregion_integration",
    "component_fidelity",
    "scientific_plausibility",
    "composition_layout",
    "label_annotation_semantics",
    "journal_polish",
    "reference_fidelity",
    "publication_readiness",
)
_QUALITY_VERDICTS = frozenset(
    {"pass", "needs_patch", "needs_human", "block", "not_applicable"}
)
_QUALITY_CONFIDENCES = frozenset({"low", "medium", "high"})
_QUALITY_ACTIONS = frozenset(
    {"none", "patch", "human_review", "revise_briefing", "block_release"}
)
_PANEL_ROLES = frozenset(
    {"setup", "mechanism", "result", "comparison", "control", "zoom", "model", "workflow", "context"}
)
_PANEL_ROLE_QUALITIES = frozenset({"clear", "weak", "missing", "redundant"})
_VERDICT_RANK = {"pass": 0, "needs_patch": 1, "needs_human": 2, "block": 3}
_ACTIONS_BY_VERDICT = {
    "pass": frozenset({"none"}),
    "not_applicable": frozenset({"none"}),
    "needs_patch": frozenset({"patch", "revise_briefing"}),
    "needs_human": frozenset({"human_review", "revise_briefing"}),
    "block": frozenset({"block_release", "human_review"}),
}
```

If ruff flags the long `_PANEL_ROLES` line, split it vertically.

- [ ] **Step 2: Add enum and list helpers**

Add near `_require_non_empty_string()`:

```python
def _require_string_value(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise CritiqueAdjudicationError(f"{label}.{key} must be a string")
    return value.strip()


def _require_enum(
    data: dict[str, Any],
    key: str,
    allowed: frozenset[str],
    *,
    label: str,
) -> str:
    value = _require_string_value(data, key, label=label)
    if value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise CritiqueAdjudicationError(f"{label}.{key} must be one of: {allowed_values}")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CritiqueAdjudicationError(f"{label} must be a list")
    return value
```

Keep `_require_non_empty_string()` unchanged because existing adjudication tests depend on its current wording.

- [ ] **Step 3: Add common axis validation**

Add:

```python
def _validate_quality_axis(axis: dict[str, Any], label: str) -> str:
    verdict = _require_enum(axis, "verdict", _QUALITY_VERDICTS, label=label)
    _require_enum(axis, "confidence", _QUALITY_CONFIDENCES, label=label)
    recommended_action = _require_enum(
        axis,
        "recommended_action",
        _QUALITY_ACTIONS,
        label=label,
    )
    if recommended_action not in _ACTIONS_BY_VERDICT[verdict]:
        allowed = ", ".join(sorted(_ACTIONS_BY_VERDICT[verdict]))
        raise CritiqueAdjudicationError(
            f"{label}.recommended_action must be one of: {allowed} for verdict {verdict}"
        )

    blocking_items = _require_list(axis.get("blocking_items"), f"{label}.blocking_items")
    if verdict in {"pass", "needs_patch", "needs_human", "block"}:
        _require_non_empty_string(axis, "rationale", label=label)
        _require_non_empty_string(axis, "evidence", label=label)
    if verdict in {"needs_patch", "block"} and not blocking_items:
        raise CritiqueAdjudicationError(
            f"{label}.blocking_items must include at least one item for verdict {verdict}"
        )
    return verdict
```

- [ ] **Step 4: Add panel-role validation**

Add:

```python
def _validate_panel_roles(axis: dict[str, Any], label: str, verdict: str) -> None:
    if verdict == "not_applicable":
        return
    raw_roles = _require_non_empty_list(axis.get("panel_roles"), f"{label}.panel_roles")
    for index, raw_role in enumerate(raw_roles):
        role_label = f"{label}.panel_roles[{index}]"
        role = _require_mapping(raw_role, role_label)
        _require_non_empty_string(role, "panel_id", label=role_label)
        _require_enum(role, "role", _PANEL_ROLES, label=role_label)
        _require_enum(role, "role_quality", _PANEL_ROLE_QUALITIES, label=role_label)
        _require_non_empty_string(role, "rationale", label=role_label)
```

- [ ] **Step 5: Add v1.2 quality-axes validation**

Add:

```python
def _validate_v1_2_quality_axes(frontmatter: dict[str, Any]) -> None:
    axes = _require_mapping(
        frontmatter.get("quality_axes"),
        "critique frontmatter.quality_axes",
    )
    verdicts: dict[str, str] = {}
    for axis_name in _QUALITY_AXIS_NAMES:
        label = f"critique frontmatter.quality_axes.{axis_name}"
        axis = _require_mapping(axes.get(axis_name), label)
        verdict = _validate_quality_axis(axis, label)
        verdicts[axis_name] = verdict
        if axis_name == "panel_role_coherence":
            _validate_panel_roles(axis, label, verdict)

    upstream_ranks = [
        _VERDICT_RANK[verdict]
        for axis_name, verdict in verdicts.items()
        if axis_name != "publication_readiness" and verdict != "not_applicable"
    ]
    readiness = verdicts["publication_readiness"]
    if upstream_ranks and readiness == "not_applicable":
        raise CritiqueAdjudicationError(
            "critique frontmatter.quality_axes.publication_readiness.verdict "
            "must be applicable when upstream quality axes are applicable"
        )
    if readiness != "not_applicable" and upstream_ranks:
        readiness_rank = _VERDICT_RANK[readiness]
        if readiness_rank < max(upstream_ranks):
            raise CritiqueAdjudicationError(
                "critique frontmatter.quality_axes.publication_readiness.verdict "
                "must not be less severe than upstream quality axes"
            )
```

- [ ] **Step 6: Wire v1.2 into `build_adjudication_scaffold()`**

Change the schema branch to:

```python
    if critique_schema == CRITIQUE_SCHEMA_V1:
        warnings.warn(
            (
                f"{CRITIQUE_SCHEMA_V1} is legacy; v1.1 critiques should include "
                "audit_enumeration"
            ),
            DeprecationWarning,
            stacklevel=2,
        )
    elif critique_schema == CRITIQUE_SCHEMA_V1_1:
        _validate_v1_1_audit(frontmatter)
    elif critique_schema == CRITIQUE_SCHEMA_V1_2:
        _validate_v1_1_audit(frontmatter)
        _validate_v1_2_quality_axes(frontmatter)
    elif isinstance(critique_schema, str) and critique_schema.startswith("figure-agent.critique."):
        raise CritiqueAdjudicationError(f"unsupported critique schema: {critique_schema}")
```

Keep the deprecation text as `v1.1` or update it to `v1.2`; tests only require `legacy`.

- [ ] **Step 7: Verify GREEN for adjudication tests**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py
```

Expected: PASS.

## Task 5: Update Status/Export Freshness Helpers

**Files:**

- Modify: `plugins/figure-agent/tests/test_status.py`
- Modify: `plugins/figure-agent/tests/test_run_export.py`

- [ ] **Step 1: Update helper rubric strings**

In both test files, change default/current rubric strings from:

```python
"figure-agent.critique-rubric.v1.1"
```

to:

```python
"figure-agent.critique-rubric.v1.2"
```

Keep deliberate mismatch values such as `figure-agent.critique-rubric.v0` unchanged.

- [ ] **Step 2: Update helper schemas**

In both hashed critique helpers, change:

```python
"schema: figure-agent.critique.v1.1\n"
```

to:

```python
"schema: figure-agent.critique.v1.2\n"
```

- [ ] **Step 3: Add minimal `quality_axes` to helper critique frontmatter**

After the existing `audit_enumeration` block and before `panels: []`, insert this exact string content in both helpers:

```python
        "quality_axes:\n"
        "  message_storyline:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: story is clear\n"
        "    evidence: briefing and render\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  panel_role_coherence:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: panel role is clear\n"
        "    evidence: panel A\n"
        "    panel_roles:\n"
        "      - panel_id: A\n"
        "        role: setup\n"
        "        role_quality: clear\n"
        "        rationale: panel introduces the setup\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  subregion_integration:\n"
        "    verdict: not_applicable\n"
        "    confidence: low\n"
        "    rationale: \"\"\n"
        "    evidence: \"\"\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  component_fidelity:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: components are recognizable\n"
        "    evidence: structural audit\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  scientific_plausibility:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: no visible scientific conflict\n"
        "    evidence: briefing invariant\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  composition_layout:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: layout is readable\n"
        "    evidence: render\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  label_annotation_semantics:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: labels match targets\n"
        "    evidence: label audit\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  journal_polish:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: polish is adequate\n"
        "    evidence: render\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  reference_fidelity:\n"
        "    verdict: not_applicable\n"
        "    confidence: low\n"
        "    rationale: \"\"\n"
        "    evidence: \"\"\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  publication_readiness:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: all applicable quality axes pass\n"
        "    evidence: quality axis summary\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
```

- [ ] **Step 4: Verify freshness/export tests**

Run:

```bash
uv run pytest -q tests/test_status.py tests/test_run_export.py
```

Expected: PASS.

## Task 6: Update Command Documentation

**Files:**

- Modify: `plugins/figure-agent/commands/fig_critique.md`

- [ ] **Step 1: Update prose to v1.2**

Replace references to schema v1.1 with schema v1.2 where the command describes the current output format.

Keep legacy mentions only if explicitly discussing old critique files.

- [ ] **Step 2: Add the quality axes workflow instruction**

In Step 3, after the mandatory audit checklist sentence, add:

```markdown
Then fill `quality_axes` for every journal-grade audit axis. Do not collapse the axes into a single score. `publication_readiness` must be at least as severe as the most severe applicable upstream axis.
```

- [ ] **Step 3: Add the `quality_axes` YAML block**

In the example frontmatter, after `audit_enumeration` and before `panels:`, add the same v1.2 schema shape emitted by `critique_brief.py`.

The command doc can use compact axis examples, but it must include every required axis name and the bounded values for:

```yaml
verdict: pass | needs_patch | needs_human | block | not_applicable
confidence: low | medium | high
recommended_action: none | patch | human_review | revise_briefing | block_release
```

- [ ] **Step 4: Verify command docs contain all axes**

Run:

```bash
rg -n "figure-agent\\.critique\\.v1\\.2|quality_axes|message_storyline|publication_readiness" commands/fig_critique.md
```

Expected: all four patterns are found.

## Task 7: Run Targeted and Full Verification

**Files:**

- All modified files.

- [ ] **Step 1: Run targeted suite**

```bash
uv run pytest -q tests/test_critique_brief.py tests/test_critique_adjudication.py tests/test_status.py tests/test_run_export.py
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest
```

Expected: PASS.

- [ ] **Step 3: Run lint on changed files**

```bash
uv run ruff check scripts/critique_brief.py scripts/critique_adjudication.py scripts/quality_manifest.py tests/test_critique_brief.py tests/test_critique_adjudication.py tests/test_status.py tests/test_run_export.py
```

Expected: PASS.

- [ ] **Step 4: Run tracked Python lint**

The current workspace has untracked dogfood/example code outside this slice, so do not use `uv run ruff check .` unless the untracked example workspace is cleaned first. Use tracked Python files:

```bash
git ls-files '*.py' | xargs uv run ruff check
```

Expected: PASS.

- [ ] **Step 5: Run whitespace check**

```bash
git diff --check
```

Expected: PASS.

- [ ] **Step 6: Validate plugin manifests**

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all pass.

## Task 8: Review Scope Before Commit

**Files:**

- Inspect only.

- [ ] **Step 1: Confirm changed files**

Run from repository root:

```bash
git status --short
```

Expected Issue 6B implementation files:

```text
 M plugins/figure-agent/commands/fig_critique.md
 M plugins/figure-agent/scripts/critique_adjudication.py
 M plugins/figure-agent/scripts/critique_brief.py
 M plugins/figure-agent/scripts/quality_manifest.py
 M plugins/figure-agent/tests/test_critique_adjudication.py
 M plugins/figure-agent/tests/test_critique_brief.py
 M plugins/figure-agent/tests/test_run_export.py
 M plugins/figure-agent/tests/test_status.py
```

Docs may also be present if the Issue 6B docs and this plan are included in the same commit:

```text
?? plugins/figure-agent/docs/superpowers/issues/2026-05-18-issue-6b-journal-grade-quality-axes-v1-2.md
?? plugins/figure-agent/docs/superpowers/specs/2026-05-18-journal-grade-quality-axes-v1-2-design.md
?? plugins/figure-agent/docs/superpowers/plans/2026-05-18-journal-grade-quality-axes-v1-2.md
```

Do not stage dirty example files, `.scratch/`, build artifacts, export artifacts, or unrelated dogfood fixture edits.

- [ ] **Step 2: Review final diff**

Run:

```bash
git diff -- plugins/figure-agent/commands/fig_critique.md plugins/figure-agent/scripts/critique_adjudication.py plugins/figure-agent/scripts/critique_brief.py plugins/figure-agent/scripts/quality_manifest.py plugins/figure-agent/tests/test_critique_adjudication.py plugins/figure-agent/tests/test_critique_brief.py plugins/figure-agent/tests/test_run_export.py plugins/figure-agent/tests/test_status.py
```

Check:

- v1 and v1.1 legacy paths still exist.
- v1.2 validates both `audit_enumeration` and `quality_axes`.
- No `/fig_loop` runtime behavior changed.
- No accepted/golden/export behavior changed.
- No example critique file was migrated.

## Self-Review Checklist

Before claiming first-stage completion:

- [ ] `quality_axes` contains exactly the ten required axes from the design spec.
- [ ] All enum values are bounded and tested.
- [ ] `publication_readiness` severity ordering is deterministic and tested.
- [ ] `needs_patch` and `block` cannot hide issues with empty `blocking_items`.
- [ ] v1 and v1.1 critique files remain parseable.
- [ ] v1.2 critiques require both `audit_enumeration` and `quality_axes`.
- [ ] No hidden auto-editing, auto-acceptance, compile/export mutation, or `/fig_loop` ingestion was implemented in this slice.
- [ ] Full tests and plugin validation passed from `plugins/figure-agent`.
