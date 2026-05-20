# Top-Tier Critique Audit v1.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a v1.3 critique contract that forces top-tier journal figure audit slots before scoring or polish.

**Architecture:** This is an additive critique-schema slice. `critique_brief.py` emits the new section/schema, `critique_adjudication.py` validates it, and existing status/loop/driver/export behavior remains unchanged.

**Tech Stack:** Python 3.12, PyYAML, pytest, ruff, Claude plugin validation.

---

## Files

- Modify: `plugins/figure-agent/scripts/quality_manifest.py`
- Modify: `plugins/figure-agent/scripts/critique_brief.py`
- Modify: `plugins/figure-agent/scripts/critique_adjudication.py`
- Modify: `plugins/figure-agent/tests/test_critique_brief.py`
- Modify: `plugins/figure-agent/tests/test_critique_adjudication.py`
- Optional docs update: `plugins/figure-agent/commands/fig_critique.md`

## Task 1: Brief Emits v1.3 Top-Tier Audit

- [ ] Add failing test in `tests/test_critique_brief.py`:

```python
def test_critique_brief_includes_top_tier_journal_audit(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Top-Tier Journal Figure Audit (host LLM MUST enumerate)" in brief
    assert "### 1. First-Glance Message" in brief
    assert "### 2. Target-Journal Fit" in brief
    assert "### 3. Novelty and Claim Support" in brief
    assert "### 4. Figure-Caption Coupling" in brief
    assert "### 5. Visual Economy" in brief
    assert "### 6. Cross-Panel Semantic Grammar" in brief
    assert "### 7. Reader Misinterpretation Risk" in brief
    assert "### 8. Reduction / Print Readability" in brief
    assert "### 9. Accessibility and Color Robustness" in brief
    assert "### 10. Aesthetic Coherence" in brief
```

- [ ] Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_top_tier_journal_audit
```

Expected: fail because the section is not emitted.

- [ ] Implement `_top_tier_journal_audit()` in `scripts/critique_brief.py` and insert it after `_journal_quality_axes()` and before `_journal_grade_assessment()`.

- [ ] Run the same test. Expected: pass.

## Task 2: Schema and Rubric Version Bump

- [ ] Add failing assertions to `tests/test_critique_brief.py`:

```python
def test_critique_brief_output_format_uses_v1_3_top_tier_schema(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "schema: figure-agent.critique.v1.3" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.3" in brief
    assert "top_tier_audit:" in brief
```

- [ ] Run:

```bash
uv run pytest -q tests/test_critique_brief.py::test_critique_brief_output_format_uses_v1_3_top_tier_schema
```

Expected: fail on v1.2 strings.

- [ ] Update `scripts/quality_manifest.py` `CRITIQUE_RUBRIC_VERSION` to `figure-agent.critique-rubric.v1.3`.

- [ ] Update `scripts/critique_brief.py` output schema text to `figure-agent.critique.v1.3` and add the `top_tier_audit` YAML schema block.

- [ ] Run:

```bash
uv run pytest -q tests/test_critique_brief.py
```

Expected: pass after updating existing v1.2 assertions to v1.3 where they describe the current brief.

## Task 3: v1.3 Validator Accepts Complete Top-Tier Audit

- [ ] Add helper in `tests/test_critique_adjudication.py`:

```python
def _complete_v1_3_top_tier_audit_yaml() -> str:
    keys = (
        "first_glance_message",
        "target_journal_fit",
        "novelty_claim_support",
        "figure_caption_coupling",
        "visual_economy",
        "cross_panel_semantic_grammar",
        "reader_misinterpretation_risk",
        "reduction_print_readability",
        "accessibility_color_robustness",
        "aesthetic_coherence",
    )
    lines = ["top_tier_audit:"]
    for key in keys:
        lines.extend(
            [
                f"  {key}:",
                "    verdict: pass",
                f"    finding: {key} is acceptable for the current artifact",
                "    concrete_fix: accept_simplification",
                "    blocks_high_impact: false",
            ]
        )
    return "\n".join(lines) + "\n"
```

- [ ] Add failing test:

```python
def test_build_adjudication_scaffold_accepts_v1_3_top_tier_audit(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml(),
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)
```

- [ ] If existing helpers do not accept `critique_schema` or `extra_frontmatter_yaml`, extend only the test helper, not production code.

- [ ] Run the new test. Expected: fail with unsupported critique schema.

- [ ] Add `CRITIQUE_SCHEMA_V1_3` and route v1.3 through v1.1 audit validation, v1.2 quality validation, journal assessment validation, and new top-tier audit validation.

- [ ] Run the new test. Expected: pass.

## Task 4: v1.3 Validator Rejects Malformed Top-Tier Audit

- [ ] Add failing tests:

```python
def test_build_adjudication_scaffold_rejects_v1_3_missing_top_tier_audit(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
    )

    with pytest.raises(CritiqueAdjudicationError, match="top_tier_audit"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_3_invalid_top_tier_verdict(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = _complete_v1_3_top_tier_audit_yaml().replace(
        "    verdict: pass\n",
        "    verdict: perfect\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=top_tier_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="verdict"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_3_empty_top_tier_finding(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = _complete_v1_3_top_tier_audit_yaml().replace(
        "    finding: first_glance_message is acceptable for the current artifact\n",
        "    finding: \"\"\n",
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=top_tier_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="finding"):
        build_adjudication_scaffold(fig_dir)
```

- [ ] Run these tests. Expected: fail before validator exists.

- [ ] Implement `_validate_v1_3_top_tier_audit(frontmatter)` in `scripts/critique_adjudication.py`.

- [ ] Validation rules:
  - all ten keys required;
  - each item must be a mapping;
  - `verdict` is one of `pass`, `weak`, `fail`, `needs_human`;
  - `finding` and `concrete_fix` are non-empty strings;
  - `blocks_high_impact` is boolean.

- [ ] Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py
```

Expected: pass.

## Task 5: Command Docs and Full Verification

- [ ] Update `commands/fig_critique.md` to say v1.3 critiques require both `audit_enumeration` and `top_tier_audit`.

- [ ] Run:

```bash
uv run pytest -q tests/test_critique_brief.py tests/test_critique_adjudication.py tests/test_fig_loop.py tests/test_status.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected:
- focused tests pass;
- full suite passes with the existing skip/xfail count;
- ruff passes;
- diff check clean;
- plugin validation passes.

## Closeout

- [ ] Commit implementation:

```bash
git add scripts/quality_manifest.py scripts/critique_brief.py scripts/critique_adjudication.py tests/test_critique_brief.py tests/test_critique_adjudication.py commands/fig_critique.md
git commit -m "Add top-tier critique audit v1.3"
```

- [ ] Report remaining risks:
  - v1.3 improves host critique prompt pressure but does not prove repeated human-level calibration until dogfood runs are collected.
  - target-journal policy validation remains manual/HITL.

