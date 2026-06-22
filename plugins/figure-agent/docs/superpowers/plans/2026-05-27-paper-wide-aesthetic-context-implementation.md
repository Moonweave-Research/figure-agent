# Paper-Wide Aesthetic Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit, opt-in paper-wide aesthetic context pack that grounds `/fig_critique`, participates in critique freshness, and prevents host critiques from silently ignoring manuscript-series visual-language constraints.

**Architecture:** Keep paper-wide context separate from fixture-local `aesthetic_intent.yaml`. A new parser module validates `examples/_paper_aesthetic_contexts/<paper_id>.yaml`, `quality_manifest.py` includes the resolved pack only when `spec.yaml.paper_aesthetic_context` opts in, `critique_brief.py` emits a mandatory context section, and `critique_lint.py` enforces exact anchor citations in three existing critique slots.

**Tech Stack:** Python 3, PyYAML, pytest, existing figure-agent scripts under `plugins/figure-agent/scripts`.

---

## File Structure

- Create `plugins/figure-agent/scripts/paper_aesthetic_context.py`
  - Owns schema constants, safe-id validation, pack path resolution, parser validation, matching fixture-role lookup, and anchor extraction.
- Create `plugins/figure-agent/tests/test_paper_aesthetic_context.py`
  - Covers valid pack loading, malformed pack failures, unsafe ids, missing opted-in packs, fixture-role matching, duplicate ids, and unknown `must_align_with` ids.
- Modify `plugins/figure-agent/scripts/quality_manifest.py`
  - Adds the resolved paper-wide pack to critique input manifest paths when `spec.yaml.paper_aesthetic_context` is declared.
- Modify `plugins/figure-agent/tests/test_quality_manifest.py`
  - Proves opted-in packs affect freshness inputs and missing opt-in preserves legacy behavior.
- Modify `plugins/figure-agent/scripts/critique_brief.py`
  - Loads the optional pack after parsing `spec.yaml`, emits `## Paper-Wide Aesthetic Context` before fixture-local `## Aesthetic Intent Calibration`, and converts parser errors to `CritiqueBriefError`.
- Modify `plugins/figure-agent/tests/test_critique_brief.py`
  - Proves brief section inclusion, matching-role filtering, exact anchor instructions, missing-pack controlled failure, and legacy omission.
- Modify `plugins/figure-agent/scripts/critique_lint.py`
  - Adds `paper_aesthetic_context_accounting` blockers for malformed opted-in packs and critiques that do not cite paper-wide anchors in required slots.
- Modify `plugins/figure-agent/tests/test_critique_lint.py`
  - Proves generic critique rejection, exact-anchor acceptance, malformed-pack blocker, and no-op legacy behavior.
- Modify docs only if behavior text must be surfaced:
  - `plugins/figure-agent/commands/fig_critique.md`
  - `plugins/figure-agent/skills/figure-agent/SKILL.md`
  - `plugins/figure-agent/docs/superpowers/issues/2026-05-27-issue-55-paper-wide-aesthetic-context.md`

## Task 1: Parser Contract

**Files:**
- Create: `plugins/figure-agent/scripts/paper_aesthetic_context.py`
- Create: `plugins/figure-agent/tests/test_paper_aesthetic_context.py`

- [ ] **Step 1: Write failing parser tests**

Add tests named:

```python
def test_load_paper_aesthetic_context_accepts_valid_pack(tmp_path: Path) -> None: ...
def test_load_paper_aesthetic_context_rejects_unsafe_paper_id(tmp_path: Path) -> None: ...
def test_load_paper_aesthetic_context_rejects_filename_mismatch(tmp_path: Path) -> None: ...
def test_load_paper_aesthetic_context_rejects_unknown_alignment_id(tmp_path: Path) -> None: ...
def test_load_optional_paper_aesthetic_context_returns_none_without_opt_in(tmp_path: Path) -> None: ...
def test_load_optional_paper_aesthetic_context_rejects_missing_opted_pack(tmp_path: Path) -> None: ...
def test_paper_context_anchors_include_series_fields_and_role_constraints(tmp_path: Path) -> None: ...
```

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_paper_aesthetic_context.py
```

Expected: fail because `paper_aesthetic_context` module does not exist.

- [ ] **Step 2: Implement parser**

Implement:

```python
PAPER_AESTHETIC_CONTEXT_SCHEMA = "figure-agent.paper-aesthetic-context.v1"
PAPER_CONTEXT_DIRNAME = "_paper_aesthetic_contexts"

class PaperAestheticContextError(Exception): ...

def is_safe_paper_context_id(value: str) -> bool: ...
def paper_context_id_from_spec(spec: dict[str, Any]) -> str | None: ...
def paper_context_path_for_id(example_dir: Path, paper_id: str) -> Path: ...
def declared_paper_context_path(example_dir: Path, spec: dict[str, Any]) -> Path | None: ...
def load_paper_aesthetic_context(path: Path) -> dict[str, Any]: ...
def matching_figure_role(pack: dict[str, Any], fixture: str) -> dict[str, Any]: ...
def load_optional_paper_aesthetic_context(example_dir: Path, spec: dict[str, Any]) -> dict[str, Any] | None: ...
def paper_context_anchors(pack: dict[str, Any], fixture: str) -> set[str]: ...
```

Validation details:

```text
schema == figure-agent.paper-aesthetic-context.v1
safe paper_id and safe spec id; ids must start with an ASCII letter or number
and then use only ASCII letters, numbers, `_`, `.`, and `-`
paper_id == path.stem
target_journal, visual_maturity, density use aesthetic_intent.py enums
shared_visual_language is non-empty, unique ids, max 12
figure_roles is non-empty, unique fixture, max 50
must_align_with ids all exist in shared_visual_language
must_avoid is non-empty, unique ids, max 12
```

- [ ] **Step 3: Verify parser tests pass**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_paper_aesthetic_context.py
uv run ruff check scripts/paper_aesthetic_context.py tests/test_paper_aesthetic_context.py
```

Expected: all parser tests pass and ruff is clean.

## Task 2: Freshness Integration

**Files:**
- Modify: `plugins/figure-agent/scripts/quality_manifest.py`
- Modify: `plugins/figure-agent/tests/test_quality_manifest.py`

- [ ] **Step 1: Write failing freshness tests**

Add tests named:

```python
def test_critique_manifest_includes_declared_paper_aesthetic_context(tmp_path: Path) -> None: ...
def test_critique_manifest_omits_paper_aesthetic_context_without_opt_in(tmp_path: Path) -> None: ...
```

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_quality_manifest.py::test_critique_manifest_includes_declared_paper_aesthetic_context tests/test_quality_manifest.py::test_critique_manifest_omits_paper_aesthetic_context_without_opt_in
```

Expected: first test fails because the pack is not yet included.

- [ ] **Step 2: Add manifest path participation**

Import `declared_paper_context_path()` and append the returned path when it exists:

```python
paper_context_path = declared_paper_context_path(example_dir, spec)
if paper_context_path is not None and paper_context_path.exists():
    paths.append(paper_context_path)
```

Do not make non-opted fixtures depend on `examples/_paper_aesthetic_contexts`.

- [ ] **Step 3: Verify freshness tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_quality_manifest.py tests/test_paper_aesthetic_context.py
uv run ruff check scripts/quality_manifest.py scripts/paper_aesthetic_context.py tests/test_quality_manifest.py tests/test_paper_aesthetic_context.py
```

Expected: targeted tests pass and ruff is clean.

## Task 3: Critique Brief Section

**Files:**
- Modify: `plugins/figure-agent/scripts/critique_brief.py`
- Modify: `plugins/figure-agent/tests/test_critique_brief.py`
- Modify: `plugins/figure-agent/commands/fig_critique.md`
- Modify: `plugins/figure-agent/skills/figure-agent/SKILL.md`

- [ ] **Step 1: Write failing brief tests**

Add tests named:

```python
def test_critique_brief_includes_paper_wide_aesthetic_context(tmp_path: Path) -> None: ...
def test_critique_brief_omits_paper_wide_context_without_opt_in(tmp_path: Path) -> None: ...
def test_critique_brief_reports_invalid_paper_wide_context(tmp_path: Path) -> None: ...
```

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_paper_wide_aesthetic_context tests/test_critique_brief.py::test_critique_brief_omits_paper_wide_context_without_opt_in tests/test_critique_brief.py::test_critique_brief_reports_invalid_paper_wide_context
```

Expected: inclusion test fails because the section is absent.

- [ ] **Step 2: Emit the section**

Add `_paper_aesthetic_context_section(pack, fixture)` that emits:

```markdown
## Paper-Wide Aesthetic Context
Host LLM MUST evaluate whether this figure remains coherent with the declared
paper-wide visual language. The critique must cite exact paper context anchors
in `top_tier_audit.cross_panel_semantic_grammar`,
`top_tier_audit.aesthetic_coherence`, and
`editorial_art_direction.visual_identity`.
```

Include paper id, journal, maturity, density, matching role, required shared
language items, role variations, must-avoid patterns, and exact anchor list.

- [ ] **Step 3: Document command-facing behavior**

Update `/fig_critique` docs and `SKILL.md` to state:

```text
If spec.yaml declares paper_aesthetic_context, the critique must consume the
Paper-Wide Aesthetic Context section and cite exact anchors in the required
slots; generic art-direction prose is invalid.
```

- [ ] **Step 4: Verify brief tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_critique_brief.py tests/test_paper_aesthetic_context.py
uv run ruff check scripts/critique_brief.py scripts/paper_aesthetic_context.py tests/test_critique_brief.py
```

Expected: targeted tests pass and ruff is clean.

## Task 4: Lint Accountability

**Files:**
- Modify: `plugins/figure-agent/scripts/critique_lint.py`
- Modify: `plugins/figure-agent/tests/test_critique_lint.py`

- [ ] **Step 1: Write failing lint tests**

Add tests named:

```python
def test_lint_critique_rejects_missing_paper_context_anchors(tmp_path: Path) -> None: ...
def test_lint_critique_accepts_exact_paper_context_anchors(tmp_path: Path) -> None: ...
def test_lint_critique_keeps_missing_paper_context_legacy_behavior(tmp_path: Path) -> None: ...
def test_lint_critique_reports_invalid_paper_context_as_controlled_blocker(tmp_path: Path) -> None: ...
```

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_critique_lint.py::test_lint_critique_rejects_missing_paper_context_anchors tests/test_critique_lint.py::test_lint_critique_accepts_exact_paper_context_anchors tests/test_critique_lint.py::test_lint_critique_keeps_missing_paper_context_legacy_behavior tests/test_critique_lint.py::test_lint_critique_reports_invalid_paper_context_as_controlled_blocker
```

Expected: rejection tests fail because lint does not yet load paper-wide packs.

- [ ] **Step 2: Add paper context accounting**

Add:

```python
_PAPER_CONTEXT_REQUIRED_SLOTS = (
    ("top_tier_audit", "cross_panel_semantic_grammar"),
    ("top_tier_audit", "aesthetic_coherence"),
    ("editorial_art_direction", "visual_identity"),
)
```

Implement `_paper_aesthetic_context_accounting_violations(example_dir, frontmatter)`:

```text
parse spec.yaml;
load_optional_paper_aesthetic_context(example_dir, spec);
return [] when no opt-in;
return paper_aesthetic_context_accounting blocker on parser/spec errors;
require at least one exact anchor in each required slot;
message missing slots deterministically.
```

Call it from `lint_critique()` after aesthetic intent accounting.

- [ ] **Step 3: Verify lint tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_critique_lint.py tests/test_paper_aesthetic_context.py
uv run ruff check scripts/critique_lint.py scripts/paper_aesthetic_context.py tests/test_critique_lint.py
```

Expected: targeted tests pass and ruff is clean.

## Task 5: Dogfood and Closeout

**Files:**
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-27-issue-55-paper-wide-aesthetic-context.md`
- Create or modify: `plugins/figure-agent/docs/milestones-archive/2026-05-27-paper-wide-aesthetic-context-closeout.md`

- [ ] **Step 1: Run synthetic dogfood without mutating real figure source**

Use test fixtures and direct script calls to prove:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_paper_aesthetic_context.py tests/test_quality_manifest.py tests/test_critique_brief.py tests/test_critique_lint.py
```

Expected: all targeted contract tests pass.

- [ ] **Step 2: Record closeout evidence**

Document:

```text
- No `.tex`, accepted, golden, export, or SVG polish artifact mutation.
- Non-opted fixtures preserve legacy behavior.
- Opted-in fixture packs participate in critique freshness.
- Brief section is present only for explicit opt-in.
- Lint rejects generic critiques that ignore paper-wide anchors.
```

- [ ] **Step 3: Mark Issue 55 implemented**

Update status in the issue doc after verification. Use `implemented` or
`completed in commit <sha>` only after commit exists.

## Final Verification

Run from `plugins/figure-agent`:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected:

```text
pytest: all passing except existing skipped/xfailed tests
ruff: All checks passed
git diff --check: no output, exit 0
plugin validate: all three commands pass
```

## Review Checklist

Run three critical passes before final completion:

1. Contract/freshness correctness
   - Pack only applies on explicit `spec.yaml.paper_aesthetic_context`.
   - Safe ids prevent path traversal.
   - Pack content affects `critique_input_hash`.
   - Missing opted-in pack is a controlled failure.

2. Backward compatibility and scope containment
   - Non-opted fixtures do not see new lint blockers.
   - No compile/export/status/release behavior changes.
   - No generated artifacts are staged.
   - Existing `aesthetic_intent.yaml` behavior is unchanged.

3. Test coverage and integration readiness
   - Parser failures are covered.
   - Brief inclusion and omission are covered.
   - Lint rejection and acceptance are covered.
   - Docs explain command-facing host-LLM obligations.

## Self-Review

- Spec coverage: parser, explicit opt-in, safe-id resolution, freshness, brief section, lint accountability, legacy behavior, and docs closeout are all mapped to tasks.
- Placeholder scan: no `TBD`, `TODO`, or undefined future behavior remains.
- Type consistency: all planned public functions use `Path`, `dict[str, Any]`, `set[str]`, and local `PaperAestheticContextError`; downstream modules depend only on those functions.
- Scope guard: Issue 55D is evidence/docs closeout only unless the user explicitly approves a real fixture opt-in that would intentionally stale that fixture's critique.
