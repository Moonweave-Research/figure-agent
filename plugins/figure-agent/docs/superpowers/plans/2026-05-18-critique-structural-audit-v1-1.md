# Critique Structural Audit v1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `/fig_critique` to emit a v1.1 critique contract with mandatory structural audit enumeration, while preserving legacy v1 adjudication parsing.

**Architecture:** Keep critique generation host-LLM-only. `critique_brief.py` emits stronger instructions and v1.1 schema text; `quality_manifest.py` owns the rubric version; `critique_adjudication.py` validates v1.1 audit completeness when scaffolding. `/fig_loop` integration is deliberately deferred.

**Tech Stack:** Python stdlib, PyYAML, pytest, ruff, existing figure-agent command markdown.

---

## File Structure

- Modify: `plugins/figure-agent/scripts/critique_brief.py`
  - Add mandatory audit checklist section.
  - Update output format to schema v1.1 and include `audit_enumeration`.
- Modify: `plugins/figure-agent/scripts/quality_manifest.py`
  - Bump `CRITIQUE_RUBRIC_VERSION` to `figure-agent.critique-rubric.v1.1`.
- Modify: `plugins/figure-agent/scripts/critique_adjudication.py`
  - Validate v1.1 audit completeness during scaffold.
  - Preserve v1 legacy scaffold behavior.
- Modify: `plugins/figure-agent/commands/fig_critique.md`
  - Match v1.1 output format and audit instructions.
- Modify: `plugins/figure-agent/tests/test_critique_brief.py`
  - Add brief output contract tests.
- Modify: `plugins/figure-agent/tests/test_critique_adjudication.py`
  - Add v1/v1.1 audit validation tests.
- Modify: `plugins/figure-agent/tests/test_status.py`
  - Update default rubric expectation to v1.1.
- Modify: `plugins/figure-agent/tests/test_run_export.py`
  - Update hashed critique helper to v1.1.

## Task 1: Add Brief Contract Tests

**Files:**

- Modify: `plugins/figure-agent/tests/test_critique_brief.py`

- [ ] **Step 1: Add mandatory checklist test**

Add:

```python
def test_critique_brief_includes_mandatory_audit_checklists(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Mandatory Audit Checklists (host LLM MUST enumerate)" in brief
    assert "### A. Structural Completeness Audit" in brief
    assert "### B. Label-Target Matching Audit" in brief
    assert "### C. Physical Plausibility Audit" in brief
    assert "### D. Conceptual Completeness Audit" in brief
```

- [ ] **Step 2: Update schema/rubric test expectations**

Change every existing `test_critique_brief.py` assertion that directly expects
the old critique schema or rubric version to expect:

```python
assert "schema: figure-agent.critique.v1.1" in brief
assert "rubric_version: figure-agent.critique-rubric.v1.1" in brief
assert "audit_enumeration:" in brief
```

- [ ] **Step 3: Verify RED**

Run:

```bash
uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_mandatory_audit_checklists tests/test_critique_brief.py::test_critique_brief_output_format_includes_hash_manifest_metadata
```

Expected: fails because the brief still emits v1 and has no mandatory audit section.

## Task 2: Implement Brief v1.1 Output

**Files:**

- Modify: `plugins/figure-agent/scripts/critique_brief.py`
- Modify: `plugins/figure-agent/scripts/quality_manifest.py`

- [ ] **Step 1: Bump rubric version**

Change:

```python
CRITIQUE_RUBRIC_VERSION = "figure-agent.critique-rubric.v1.1"
```

- [ ] **Step 2: Add helper for audit checklist text**

Add a small helper near the formatting helpers:

```python
def _mandatory_audit_checklists() -> str:
    return """## Mandatory Audit Checklists (host LLM MUST enumerate)

The host LLM MUST fill every numbered audit family below in the resulting
`critique.md` under top-level YAML field `audit_enumeration`. Empty v1.1 audit
enumeration is invalid. Do not invent literature citations; use bounded
reference provenance values from the output schema.

### A. Structural Completeness Audit
For each instrument/component currently drawn in the figure, enumerate:
1. Component name -> mounting/support visible? (yes/no/N-A + 1-line rationale)
2. Connections (wires/cables) -- does each connection have BOTH endpoints
   visibly attached to a defined component?
3. Per the provided reference context, list 3 standard parts that exist in the
   real reference-system but are MISSING or weakly represented in the current
   rendering. For each, declare `intentional_omission` vs `incomplete`.

### B. Label-Target Matching Audit
For EVERY label/annotation in the figure (enumerate, do not summarize):
1. Label text -> visually-nearest drawn object.
2. Is that nearest object the INTENDED label target per briefing/spec/source?
3. If mismatch: propose ONE concrete fix (relocation coordinate, leader-line
   addition, OR rename).

### C. Physical Plausibility Audit
Enumerate at least 5 physical-plausibility checks specific to this figure:
1. Cables/wires -- do they follow gravity, or are they intentionally schematic?
2. Floating components -- list any drawn object with no visible support, mount,
   or frame attachment.
3. Spatial proximities -- list any two components whose drawn proximity
   contradicts real-system separation.
4. Direction/orientation -- list any arrow, modulation cue, or motion indicator
   whose direction conflicts with the labeled physics.
5. Material distinction -- verify each labeled material region is visually
   distinguishable from neighbors.

### D. Conceptual Completeness Audit
List 3 elements that SHOULD be present per provided reference/briefing context
but are weakly represented or missing entirely. For each, provide element name,
bounded reference provenance, severity, and proposed action.
"""
```

- [ ] **Step 3: Insert checklist into returned brief**

In `generate_for()`, insert `{_mandatory_audit_checklists()}` after the TikZ
source block and before `## Critique rubric`.

- [ ] **Step 4: Update output schema text**

Change output format prose to say schema v1.1, use
`schema: figure-agent.critique.v1.1`, and include the full `audit_enumeration`
YAML shape from the design spec before `panels:`.

Include this instruction after the schema block:

```markdown
Any `structural_defect`, `incomplete`, `BLOCKER`, or `MAJOR` audit item must
either appear as a normal panel/top-level finding or be explicitly justified as
`accept_simplification`.
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
uv run pytest -q tests/test_critique_brief.py
```

Expected: passes.

## Task 3: Add Adjudication v1.1 Audit Validation Tests

**Files:**

- Modify: `plugins/figure-agent/tests/test_critique_adjudication.py`

- [ ] **Step 1: Add complete v1.1 fixture helper**

Add helper test content that writes a critique with:

```yaml
schema: figure-agent.critique.v1.1
fixture: demo_fig
audit_enumeration:
  structural_completeness:
    components:
      - component: probe
        mount_support: yes
        rationale: visible shaft mount
        connections: cable endpoint attaches to meter
    missing_from_reference:
      - element: sample stage
        status: incomplete
        rationale: standard support is absent
  label_target_matching:
    - label: polymer film
      nearest_object: polymer band
      intended_target: polymer film
      matches: true
      proposed_fix: ""
  physical_plausibility:
    - check: cable_gravity
      finding: cable is schematic-straight consistently
      verdict: convention_acceptable
  conceptual_completeness:
    - element: sample stage
      reference: provided_reference
      severity: MAJOR
      proposed_action: add
findings:
  - id: C001
    status: open
    tex_lines: [10, 20]
```

- [ ] **Step 2: Add v1.1 valid scaffold test**

Assert `build_adjudication_scaffold(fig_dir)` returns a valid adjudication with
finding `C001`.

- [ ] **Step 3: Add missing audit block test**

Write a v1.1 critique without `audit_enumeration.physical_plausibility`.
Assert `CritiqueAdjudicationError` includes `audit_enumeration.physical_plausibility`.

- [ ] **Step 4: Add empty audit block test**

Write a v1.1 critique with `label_target_matching: []`. Assert
`CritiqueAdjudicationError` includes `audit_enumeration.label_target_matching`.

- [ ] **Step 5: Assert v1 remains legacy-parseable**

Keep or add a test proving existing `schema: figure-agent.critique.v1` fixture
still scaffolds without `audit_enumeration`.

- [ ] **Step 6: Verify RED**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py
```

Expected: new v1.1 missing/empty audit tests fail because no validator exists yet.

## Task 4: Implement v1.1 Audit Validation

**Files:**

- Modify: `plugins/figure-agent/scripts/critique_adjudication.py`

- [ ] **Step 1: Add critique schema constants**

Add:

```python
CRITIQUE_SCHEMA_V1 = "figure-agent.critique.v1"
CRITIQUE_SCHEMA_V1_1 = "figure-agent.critique.v1.1"
```

- [ ] **Step 2: Add audit validation helpers**

Add:

```python
def _require_non_empty_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise CritiqueAdjudicationError(f"{label} must be a non-empty list")
    return value


def _validate_v1_1_audit(frontmatter: dict[str, Any]) -> None:
    audit = _require_mapping(
        frontmatter.get("audit_enumeration"),
        "critique frontmatter.audit_enumeration",
    )
    structural = _require_mapping(
        audit.get("structural_completeness"),
        "critique frontmatter.audit_enumeration.structural_completeness",
    )
    _require_non_empty_list(
        structural.get("components"),
        "critique frontmatter.audit_enumeration.structural_completeness.components",
    )
    _require_non_empty_list(
        structural.get("missing_from_reference"),
        "critique frontmatter.audit_enumeration.structural_completeness.missing_from_reference",
    )
    _require_non_empty_list(
        audit.get("label_target_matching"),
        "critique frontmatter.audit_enumeration.label_target_matching",
    )
    _require_non_empty_list(
        audit.get("physical_plausibility"),
        "critique frontmatter.audit_enumeration.physical_plausibility",
    )
    _require_non_empty_list(
        audit.get("conceptual_completeness"),
        "critique frontmatter.audit_enumeration.conceptual_completeness",
    )
```

- [ ] **Step 3: Validate bounded conceptual reference values**

Add this check inside `_validate_v1_1_audit()` after loading the conceptual
items:

```python
allowed_references = {"provided_reference", "briefing", "reference_pack", "not_provided"}
for index, raw_item in enumerate(conceptual_items):
    item = _require_mapping(
        raw_item,
        f"critique frontmatter.audit_enumeration.conceptual_completeness[{index}]",
    )
    reference = item.get("reference")
    if reference not in allowed_references:
        allowed = ", ".join(sorted(allowed_references))
        raise CritiqueAdjudicationError(
            "critique frontmatter.audit_enumeration.conceptual_completeness"
            f"[{index}].reference must be one of: {allowed}"
        )
```

- [ ] **Step 4: Call validator in scaffold path**

In `build_adjudication_scaffold()`, after loading `frontmatter`, add:

```python
schema = frontmatter.get("schema")
if schema == CRITIQUE_SCHEMA_V1_1:
    _validate_v1_1_audit(frontmatter)
```

Do not reject v1 solely for missing audit enumeration.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
uv run pytest -q tests/test_critique_adjudication.py
```

Expected: passes.

## Task 5: Update Command Docs and Freshness Tests

**Files:**

- Modify: `plugins/figure-agent/commands/fig_critique.md`
- Modify: `plugins/figure-agent/tests/test_status.py`
- Modify: `plugins/figure-agent/tests/test_run_export.py`

- [ ] **Step 1: Update `/fig_critique` command**

Change the command output format from schema v1 to v1.1, add the
`audit_enumeration` block, and mention that the host LLM must complete all four
audit families before writing critique findings.

- [ ] **Step 2: Update status/run_export helper rubric strings**

Replace test helper strings:

```python
"rubric_version: figure-agent.critique-rubric.v1\n"
```

with:

```python
"rubric_version: figure-agent.critique-rubric.v1.1\n"
```

Where tests intentionally check mismatch, keep the mismatch value as a distinct
old version.

- [ ] **Step 3: Verify targeted freshness tests**

Run:

```bash
uv run pytest -q tests/test_status.py tests/test_run_export.py
```

Expected: passes.

## Task 6: Full Verification

**Files:**

- All files modified in this plan.

- [ ] **Step 1: Run targeted suite**

```bash
uv run pytest -q tests/test_critique_brief.py tests/test_critique_adjudication.py tests/test_status.py tests/test_run_export.py
```

Expected: passes.

- [ ] **Step 2: Run full suite**

```bash
uv run pytest
```

Expected: passes.

- [ ] **Step 3: Run lint and diff checks**

```bash
uv run ruff check .
git diff --check
```

Expected: both pass.

- [ ] **Step 4: Validate plugin manifests**

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all pass.

- [ ] **Step 5: Review scope before commit**

Confirm the commit includes only:

- `scripts/critique_brief.py`
- `scripts/quality_manifest.py`
- `scripts/critique_adjudication.py`
- `commands/fig_critique.md`
- relevant tests

Do not stage active dogfood fixture edits under `examples/`.

## Self-Review

Spec coverage:

- Mandatory audit checklists are included.
- v1.1 schema and rubric version are included.
- v1 legacy path remains parseable.
- v1.1 missing/empty audit blocks fail cleanly.
- `/fig_loop` integration is explicitly deferred.

Placeholder scan:

- No placeholders remain.
- Every task has exact file paths and verification commands.

Type consistency:

- Field names match the design spec:
  `audit_enumeration`, `structural_completeness`, `components`,
  `missing_from_reference`, `label_target_matching`,
  `physical_plausibility`, `conceptual_completeness`.
