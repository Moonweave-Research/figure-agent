# Journal Art-Direction Playbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Issue 56A-C: optional journal art-direction playbook parser, critique freshness, brief section, schema v1.12, and lint accountability.

**Architecture:** Keep the playbook as an explicit opt-in pack resolved from `spec.yaml.journal_art_direction_playbook`. Add one focused parser module, thread it into the existing quality manifest and critique brief, then validate v1.12 critique output and fixture-aware lint accounting. Do not add drawing, SVG mutation, release behavior, or loop routing in this slice.

**Tech Stack:** Python 3.12, PyYAML, pytest, existing `critique_brief.py`, `quality_manifest.py`, `critique_schema_validator.py`, and `critique_lint.py` patterns.

---

## File Map

- Create `scripts/journal_art_direction_playbook.py`: parse, validate, resolve, and expose exact playbook anchors.
- Modify `scripts/quality_manifest.py`: include opted-in playbook packs in critique hashes and expect rubric/schema v1.12.
- Modify `scripts/critique_brief.py`: load the optional pack, emit `## Journal Art-Direction Playbook`, and choose v1.12 output when present.
- Modify `scripts/critique_schema_vocab.py`: add v1.12 and playbook-audit closed enums.
- Modify `scripts/critique_schema_validator.py`: validate `journal_art_direction_playbook_audit` for v1.12.
- Modify `scripts/critique_lint.py`: fixture-aware playbook accounting and required anchor checks.
- Modify `commands/fig_critique.md` and `skills/figure-agent/SKILL.md`: operator-facing contract.
- Add/update tests in `tests/test_journal_art_direction_playbook.py`, `tests/test_quality_manifest.py`, `tests/test_critique_brief.py`, `tests/test_critique_schema_validator.py`, and `tests/test_critique_lint.py`.

## Task 1: 56A Parser and Freshness

**Files:**
- Create: `scripts/journal_art_direction_playbook.py`
- Modify: `scripts/quality_manifest.py`
- Test: `tests/test_journal_art_direction_playbook.py`
- Test: `tests/test_quality_manifest.py`

- [ ] **Step 1: Write failing parser tests**

Create tests for:

```python
def test_load_playbook_accepts_valid_pack(tmp_path: Path) -> None:
    pack = journal_art_direction_playbook.load_journal_art_direction_playbook(path)
    assert pack["playbook_id"] == "nc-main-text"

def test_load_optional_playbook_returns_none_without_opt_in(tmp_path: Path) -> None:
    assert load_optional_journal_art_direction_playbook(example_dir, {"name": "demo"}) is None

def test_load_optional_playbook_rejects_missing_opted_pack(tmp_path: Path) -> None:
    with pytest.raises(JournalArtDirectionPlaybookError, match="missing"):
        load_optional_journal_art_direction_playbook(example_dir, {"journal_art_direction_playbook": "nc-main-text"})

def test_playbook_anchors_include_ids_and_target_fields(tmp_path: Path) -> None:
    assert "editorial_restraint" in journal_art_direction_playbook.playbook_anchors(pack)
```

- [ ] **Step 2: Verify parser tests fail**

Run:

```bash
uv run pytest -q tests/test_journal_art_direction_playbook.py
```

Expected: import failure because `journal_art_direction_playbook.py` does not exist.

- [ ] **Step 3: Implement parser**

Mirror `paper_aesthetic_context.py`: safe-id validation, enum validation, list limits, controlled YAML errors, optional loader, and `playbook_anchors(pack) -> set[str]`.

- [ ] **Step 4: Write failing freshness tests**

Add tests that `critique_manifest_paths()` includes the declared playbook and that `expected_critique_rubric_version()` returns v1.12 when `spec.yaml` declares the playbook, with v1.12 taking precedence over v1.11 aesthetic intent.

- [ ] **Step 5: Verify freshness tests fail**

Run:

```bash
uv run pytest -q tests/test_quality_manifest.py::test_critique_manifest_includes_declared_journal_art_direction_playbook tests/test_quality_manifest.py::test_expected_critique_rubric_version_uses_v1_12_for_journal_playbook
```

Expected: missing constants/imports or v1.10/v1.11 expectation mismatch.

- [ ] **Step 6: Implement freshness**

Import the parser, include the resolved playbook path in `critique_manifest_paths()`, add `CRITIQUE_RUBRIC_VERSION_V1_12` and `CRITIQUE_SCHEMA_VERSION_V1_12`, and update expected schema/rubric precedence.

- [ ] **Step 7: Verify Task 1**

Run:

```bash
uv run pytest -q tests/test_journal_art_direction_playbook.py tests/test_quality_manifest.py
uv run ruff check scripts/journal_art_direction_playbook.py scripts/quality_manifest.py tests/test_journal_art_direction_playbook.py tests/test_quality_manifest.py
git diff --check
```

## Task 2: 56B Brief and Docs

**Files:**
- Modify: `scripts/critique_brief.py`
- Modify: `commands/fig_critique.md`
- Modify: `skills/figure-agent/SKILL.md`
- Test: `tests/test_critique_brief.py`

- [ ] **Step 1: Write failing brief tests**

Add tests that an opted-in fixture emits `## Journal Art-Direction Playbook`, exact anchors, v1.12 schema/rubric, and that malformed packs raise `CritiqueBriefError`.

- [ ] **Step 2: Verify brief tests fail**

Run:

```bash
uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_journal_art_direction_playbook
```

Expected: missing section.

- [ ] **Step 3: Implement brief section**

Load the optional pack beside paper-wide context and aesthetic intent. Emit the playbook section after paper-wide context and before aesthetic intent. Select v1.12 when playbook exists.

- [ ] **Step 4: Update operator docs**

Update `/fig_critique` and `SKILL.md` so the host LLM must account for playbook anchors and fill `journal_art_direction_playbook_audit` for v1.12.

- [ ] **Step 5: Verify Task 2**

Run:

```bash
uv run pytest -q tests/test_critique_brief.py
uv run ruff check scripts/critique_brief.py tests/test_critique_brief.py
git diff --check
```

## Task 3: 56C Schema and Lint Accountability

**Files:**
- Modify: `scripts/critique_schema_vocab.py`
- Modify: `scripts/critique_schema_validator.py`
- Modify: `scripts/critique_lint.py`
- Test: `tests/test_critique_schema_validator.py`
- Test: `tests/test_critique_lint.py`

- [ ] **Step 1: Write failing schema tests**

Add tests that v1.12 accepts a complete `journal_art_direction_playbook_audit` and rejects missing audit, duplicate design-center ids, unknown verdict, non-passing entries without linked evidence, pass entries without positive refs, and route-rule mismatch.

- [ ] **Step 2: Verify schema tests fail**

Run:

```bash
uv run pytest -q tests/test_critique_schema_validator.py::test_validate_critique_schema_accepts_v1_12_journal_art_direction_playbook_audit
```

Expected: unsupported critique schema v1.12.

- [ ] **Step 3: Implement schema validator**

Add v1.12 constants and validator helpers. Reuse v1.11 validation, then validate `journal_art_direction_playbook_audit` shape.

- [ ] **Step 4: Write failing lint tests**

Add tests that opted-in playbook critiques reject generic slots, accept exact playbook anchors with complete audit, reject missing audit, reject unknown audit ids, and report malformed playbook as a controlled blocker.

- [ ] **Step 5: Verify lint tests fail**

Run:

```bash
uv run pytest -q tests/test_critique_lint.py::test_lint_critique_rejects_missing_journal_playbook_anchors
```

Expected: no journal playbook accounting yet.

- [ ] **Step 6: Implement lint accountability**

Load the optional playbook from `spec.yaml`, require anchors in the documented slots, validate audit ids and route evidence against the pack, and keep fixtures without playbooks unchanged.

- [ ] **Step 7: Verify Task 3**

Run:

```bash
uv run pytest -q tests/test_critique_schema_validator.py tests/test_critique_lint.py
uv run ruff check scripts/critique_schema_vocab.py scripts/critique_schema_validator.py scripts/critique_lint.py tests/test_critique_schema_validator.py tests/test_critique_lint.py
git diff --check
```

## Final Verification

- [ ] Run:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

- [ ] Review:
  - no figure source/export/accepted/golden mutation;
  - legacy fixtures without playbook remain v1.10/v1.11 compatible;
  - v1.12 only appears for explicit playbook opt-in;
  - docs match implemented schema/rubric names.
