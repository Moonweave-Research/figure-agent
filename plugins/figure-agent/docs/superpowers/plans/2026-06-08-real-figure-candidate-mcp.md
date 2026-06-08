# Real-Figure Candidate MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `fig-agent candidates fig1_overview_v2_pair_001_vault --panel C --family energy-trap-alignment` produce a real, reviewable Panel C candidate and expose it through CLI/MCP without source mutation.

**Architecture:** Add a conservative TeX index and panel model first, then implement one real candidate family for Panel C. Rendering remains sandboxed under `build/candidates/`; MCP remains a read-only facade over CLI contracts.

**Tech Stack:** Python 3 standard library, existing `fig-agent` CLI, existing candidate schema modules, pytest, ruff, current MCP stdio server.

---

## File Structure

- Create `plugins/figure-agent/scripts/candidate_tex_index.py`
  - Read-only TeX line/range index.
  - Owns panel boundary hints, active-command extraction, selector hashes, and dirty fixture metadata.
- Create `plugins/figure-agent/scripts/candidate_panel_model.py`
  - Joins intent model panels, `spec.yaml` bboxes, TeX index selectors, and render/crop metadata.
- Create `plugins/figure-agent/scripts/candidate_families.py`
  - Owns family names and candidate generation for `energy-trap-alignment`.
- Modify `plugins/figure-agent/scripts/candidate_generator.py`
  - Add `panel` and `family` filters while preserving existing default behavior.
- Modify `plugins/figure-agent/scripts/candidate_render.py`
  - Add staged render result fields and review artifact descriptors without compiling yet when host render is not requested.
- Modify `plugins/figure-agent/scripts/candidate_review_packet.py`
  - Surface panel, selector, `visual_review`, candidate hash, and missing-render status.
- Modify `plugins/figure-agent/bin/fig-agent`
  - Add `analyze-panel`, `compare-candidate`, `explain-no-candidate`.
  - Add `--panel` and `--family` to `candidates`.
- Modify `plugins/figure-agent/mcp/figure_agent_server.py`
  - Add read-only panel/candidate inspection tools.
- Add tests:
  - `plugins/figure-agent/tests/test_candidate_tex_index.py`
  - `plugins/figure-agent/tests/test_candidate_panel_model.py`
  - `plugins/figure-agent/tests/test_candidate_families.py`
  - Extend `test_candidate_generator.py`, `test_candidate_cli_contract.py`, `test_candidate_review_packet.py`, `test_mcp_facade.py`.

## Task 1: TeX Selector Index

**Files:**
- Create: `plugins/figure-agent/scripts/candidate_tex_index.py`
- Test: `plugins/figure-agent/tests/test_candidate_tex_index.py`

- [ ] **Step 1: Write failing tests**

Add tests for:

```python
def test_panel_boundaries_use_comments_but_only_active_commands_are_elements(tmp_path: Path) -> None:
    fixture = _fixture_with_tex(tmp_path, "% Panel C -- Energy\n% shallow only comment\n\\draw (0,0) -- (1,0);\n% Panel D\n\\node at (0,0) {not C};\n")
    index = candidate_tex_index.build_tex_index("candidate_demo", workspace_root=tmp_path / "workspace")
    panel_c = [item for item in index["selectors"] if item["panel"] == "C"]
    assert len(panel_c) == 1
    assert panel_c[0]["line_start"] == 3
    assert panel_c[0]["selector_text_hash"].startswith("sha256:")


def test_multiline_draw_selector_captures_full_command(tmp_path: Path) -> None:
    fixture = _fixture_with_tex(tmp_path, "% Panel C\n\\draw[red]\n  (0,0) --\n  (1,0);\n")
    index = candidate_tex_index.build_tex_index("candidate_demo", workspace_root=tmp_path / "workspace")
    selector = index["selectors"][0]
    assert selector["line_start"] == 2
    assert selector["line_end"] == 4
```

- [ ] **Step 2: Run RED**

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_tex_index.py
```

Expected: `ModuleNotFoundError: No module named 'candidate_tex_index'`.

- [ ] **Step 3: Implement**

Implement:

```python
SCHEMA = "figure-agent.candidate-tex-index.v1"

def build_tex_index(name: str, *, workspace_root: Path | None = None, plugin_root: Path | None = None) -> dict[str, Any]:
    ...
```

Rules:

- validate fixture name;
- reject symlinked fixture/source;
- panel hints come from `% Panel <ID>` comments;
- for real fig1, treat Panel C header at source line 433 and Row 2 start at
  line 866 as hints only; the B->C inter-arrow at lines 430-431 must not be
  classified as Panel C just because it points into that region;
- active selectors are only lines/ranges beginning with TeX commands such as `\draw`, `\node`, `\coordinate`, `\fill`, `\path`, `\shade`;
- multiline selector ends at the first line containing `;`;
- selector hash uses `candidate_contracts.canonical_hash(selected_text)`;
- include `fixture_dirty` and `affected_files_dirty` placeholders as booleans.

Real Panel C anchors to preserve in tests or dogfood notes:

- trap site coordinates: source lines 557-560;
- trap dot rendering: lines 610-617;
- energy labels: lines 632-659;
- Gaussian distributions: lines 682-695;
- energy axis: lines 707-724;
- trap level lines: lines 740-745;
- right-side trap markers: lines 753-760;
- shallow/deep labels: lines 770-775;
- escape curves: lines 790-797;
- trap-depth caliper/label: lines 814-821;
- site-to-level leaders: lines 833-840.

- [ ] **Step 4: Run GREEN**

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_tex_index.py
uv run ruff check plugins/figure-agent/scripts/candidate_tex_index.py plugins/figure-agent/tests/test_candidate_tex_index.py
```

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/scripts/candidate_tex_index.py plugins/figure-agent/tests/test_candidate_tex_index.py
git commit -m "Add candidate TeX selector index"
```

## Task 2: Panel Model and CLI Analyze

**Files:**
- Create: `plugins/figure-agent/scripts/candidate_panel_model.py`
- Modify: `plugins/figure-agent/bin/fig-agent`
- Test: `plugins/figure-agent/tests/test_candidate_panel_model.py`
- Extend: `plugins/figure-agent/tests/test_candidate_cli_contract.py`

- [ ] **Step 1: Write tests**

Test `build_panel_model("candidate_demo", "C")` returns:

```json
{
  "schema": "figure-agent.candidate-panel-model.v1",
  "fixture": "candidate_demo",
  "panel": {"id": "C", "bbox_pdf_cm": [0.0, 0.0, 1.0, 1.0]},
  "selectors": [...]
}
```

Test `fig-agent analyze-panel candidate_demo C --json` returns that schema.

- [ ] **Step 2: Implement**

Use `figure_intent_model.build_intent_model` plus `candidate_tex_index.build_tex_index`. Reject unsafe panel ids with a strict `[A-Za-z0-9_-]+` check. Include:

- `coordinate_system: "pdf_cm_bottom_left"` when `bbox_pdf_cm` exists;
- `visual_review.status = "missing_render"` until crop helper lands;
- selector count and selector list filtered to the panel.

- [ ] **Step 3: Verify and commit**

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_panel_model.py plugins/figure-agent/tests/test_candidate_cli_contract.py
uv run ruff check plugins/figure-agent/scripts/candidate_panel_model.py plugins/figure-agent/bin/fig-agent
git add plugins/figure-agent/scripts/candidate_panel_model.py plugins/figure-agent/bin/fig-agent plugins/figure-agent/tests/test_candidate_panel_model.py plugins/figure-agent/tests/test_candidate_cli_contract.py
git commit -m "Add panel candidate analysis"
```

## Task 3: Panel C Energy-Trap Candidate Family

**Files:**
- Create: `plugins/figure-agent/scripts/candidate_families.py`
- Modify: `plugins/figure-agent/scripts/candidate_generator.py`
- Modify: `plugins/figure-agent/bin/fig-agent`
- Test: `plugins/figure-agent/tests/test_candidate_families.py`
- Extend: `plugins/figure-agent/tests/test_candidate_generator.py`, `plugins/figure-agent/tests/test_candidate_cli_contract.py`

- [ ] **Step 1: Write tests**

Tests must cover:

- synthetic Panel C with `mobility edge`, `shallow`, `deep`, `siteS1`, and `siteD1` active TeX yields at least one candidate;
- unknown family returns `unsupported_candidate_family`;
- `plot-marker-hierarchy` on Panel C returns `unsupported_panel_family`;
- real fixture `fig1_overview_v2_pair_001_vault --panel C --family energy-trap-alignment` produces non-empty candidates.

- [ ] **Step 2: Implement family**

`candidate_families.build_family_candidates(...)` supports only:

```text
energy-trap-alignment
```

Initial conservative candidate:

- target Panel C;
- find active selectors containing `mobility edge`, `shallow`, `deep`, `siteS`, or `siteD`;
- generate one review-only `style_normalization` or `label_offset` candidate with a local replacement that is guaranteed to exist in source;
- include deterministic `candidate_hash`;
- set `apply_authority = "review_only"` for accepted/golden fixtures and semantic-risk candidates.

- [ ] **Step 3: Wire generator**

`candidate_generator.build_candidate_set(..., panel=None, family=None)`:

- preserves old synthetic default when no panel/family is passed;
- delegates to `candidate_families` when panel or family is passed;
- emits structured refusals for no-supported/unsupported-family cases.

CLI:

```text
fig-agent candidates <name> --panel C --family energy-trap-alignment --json --output build/candidates/panel_C_candidate_set.json
```

- [ ] **Step 4: Verify and commit**

```bash
PYTHONPATH=/opt/homebrew/lib/python3.14/site-packages:/Users/choemun-yeong/Library/Python/3.14/lib/python/site-packages uv run pytest -q \
  plugins/figure-agent/tests/test_candidate_families.py \
  plugins/figure-agent/tests/test_candidate_generator.py \
  plugins/figure-agent/tests/test_candidate_cli_contract.py
uv run ruff check plugins/figure-agent/scripts/candidate_families.py plugins/figure-agent/scripts/candidate_generator.py plugins/figure-agent/bin/fig-agent
git add plugins/figure-agent/scripts/candidate_families.py plugins/figure-agent/scripts/candidate_generator.py plugins/figure-agent/bin/fig-agent plugins/figure-agent/tests/test_candidate_families.py plugins/figure-agent/tests/test_candidate_generator.py plugins/figure-agent/tests/test_candidate_cli_contract.py
git commit -m "Add Panel C energy trap candidates"
```

## Task 4: Review Packet and Compare CLI

**Files:**
- Modify: `plugins/figure-agent/scripts/candidate_render.py`
- Modify: `plugins/figure-agent/scripts/candidate_review_packet.py`
- Modify: `plugins/figure-agent/bin/fig-agent`
- Extend: `plugins/figure-agent/tests/test_candidate_render.py`, `plugins/figure-agent/tests/test_candidate_review_packet.py`, `plugins/figure-agent/tests/test_candidate_cli_contract.py`

- [ ] **Step 1: Write tests**

Assert rendered manifests include:

- `candidate_hash`;
- `panel`;
- `selectors`;
- `stages.prepare = "passed"`;
- `stages.compile/export/crop = "not_run"` for this slice;
- `visual_review.status = "missing_render"`.

Assert `fig-agent compare-candidate <name> CAND001 --json` returns the same review packet schema and includes `visual_review`.

- [ ] **Step 2: Implement**

Carry candidate fields through render manifest and review packet. Do not compile or export candidate artifacts yet; record `missing_render` explicitly.

- [ ] **Step 3: Verify and commit**

```bash
uv run pytest -q plugins/figure-agent/tests/test_candidate_render.py plugins/figure-agent/tests/test_candidate_review_packet.py plugins/figure-agent/tests/test_candidate_cli_contract.py
uv run ruff check plugins/figure-agent/scripts/candidate_render.py plugins/figure-agent/scripts/candidate_review_packet.py plugins/figure-agent/bin/fig-agent
git add plugins/figure-agent/scripts/candidate_render.py plugins/figure-agent/scripts/candidate_review_packet.py plugins/figure-agent/bin/fig-agent plugins/figure-agent/tests/test_candidate_render.py plugins/figure-agent/tests/test_candidate_review_packet.py plugins/figure-agent/tests/test_candidate_cli_contract.py
git commit -m "Add candidate visual review packets"
```

## Task 5: MCP Panel Candidate Tools

**Files:**
- Modify: `plugins/figure-agent/mcp/figure_agent_server.py`
- Extend: `plugins/figure-agent/tests/test_mcp_facade.py`

- [ ] **Step 1: Write tests**

Add MCP tests for:

- tool list includes `figure_agent_analyze_panel`, `figure_agent_propose_panel_improvements`, `figure_agent_compare_candidate`, `figure_agent_explain_no_candidate`;
- analyze/propose/render/compare flow succeeds on synthetic Panel C;
- apply remains a deterministic refusal and no new MCP tool mutates source;
- mutating render path remains fixture-locked.

- [ ] **Step 2: Implement**

Reuse existing `_run_json_fig_agent_tool`, `_validated_workspace_and_name`, `_fixture_lock`, and bounded error envelopes.

Tool mapping:

```text
figure_agent_analyze_panel -> fig-agent analyze-panel <name> <panel_id> --json
figure_agent_propose_panel_improvements -> fig-agent candidates <name> --panel <panel_id> --family <family> --json
figure_agent_compare_candidate -> fig-agent compare-candidate <name> <candidate_id> --json
figure_agent_explain_no_candidate -> fig-agent explain-no-candidate <name> --panel <panel_id> --json
```

Do not add `figure_agent_prepare_apply_command` in this vertical slice. Defer it
until candidate hashes, dirty-state recording, and CLI apply eligibility are
real enough to verify authority. Keep `figure_agent_apply_candidate` as the
deterministic refusal.

- [ ] **Step 3: Verify and commit**

```bash
PYTHONPATH=/opt/homebrew/lib/python3.14/site-packages:/Users/choemun-yeong/Library/Python/3.14/lib/python/site-packages uv run pytest -q plugins/figure-agent/tests/test_mcp_facade.py
uv run ruff check plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/tests/test_mcp_facade.py
git add plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/tests/test_mcp_facade.py
git commit -m "Expose panel candidate MCP tools"
```

## Task 6: Release Gate and Dogfood

**Files:**
- Modify: `plugins/figure-agent/scripts/release_gate.py`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md`
- Create: `plugins/figure-agent/docs/milestones/2026-06-08-real-figure-panel-c-candidate-dogfood.md`

- [ ] **Step 1: Add release tests and schema map rows**

Add new targeted tests to `TARGETED_TESTS`. Add schema rows:

- `figure-agent.candidate-tex-index.v1`
- `figure-agent.candidate-panel-model.v1`

- [ ] **Step 2: Dogfood on real Panel C**

Run:

```bash
FIGURE_AGENT_PLUGIN_ROOT=$PWD/plugins/figure-agent \
FIGURE_AGENT_WORKSPACE=$PWD/plugins/figure-agent \
plugins/figure-agent/bin/fig-agent analyze-panel fig1_overview_v2_pair_001_vault C --json

FIGURE_AGENT_PLUGIN_ROOT=$PWD/plugins/figure-agent \
FIGURE_AGENT_WORKSPACE=$PWD/plugins/figure-agent \
plugins/figure-agent/bin/fig-agent candidates fig1_overview_v2_pair_001_vault \
  --panel C --family energy-trap-alignment --json \
  --output build/candidates/panel_C_candidate_set.json

FIGURE_AGENT_PLUGIN_ROOT=$PWD/plugins/figure-agent \
FIGURE_AGENT_WORKSPACE=$PWD/plugins/figure-agent \
plugins/figure-agent/bin/fig-agent render-candidates fig1_overview_v2_pair_001_vault \
  --candidate-set build/candidates/panel_C_candidate_set.json

FIGURE_AGENT_PLUGIN_ROOT=$PWD/plugins/figure-agent \
FIGURE_AGENT_WORKSPACE=$PWD/plugins/figure-agent \
plugins/figure-agent/bin/fig-agent rank-candidates fig1_overview_v2_pair_001_vault \
  --candidate-set build/candidates/panel_C_candidate_set.json --json
```

Expected:

- candidate set is non-empty;
- render writes only under `build/candidates/`;
- rank returns reviewable scores;
- source and exports are unchanged.

- [ ] **Step 3: Verify and commit**

```bash
PYTHONPATH=/opt/homebrew/lib/python3.14/site-packages:/Users/choemun-yeong/Library/Python/3.14/lib/python/site-packages uv run pytest -q \
  plugins/figure-agent/tests/test_candidate_tex_index.py \
  plugins/figure-agent/tests/test_candidate_panel_model.py \
  plugins/figure-agent/tests/test_candidate_families.py \
  plugins/figure-agent/tests/test_candidate_generator.py \
  plugins/figure-agent/tests/test_candidate_cli_contract.py \
  plugins/figure-agent/tests/test_mcp_facade.py \
  plugins/figure-agent/tests/test_release_contract.py \
  plugins/figure-agent/tests/test_release_gate.py

uv run ruff check plugins/figure-agent/scripts/candidate_*.py plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/bin/fig-agent
git add plugins/figure-agent/scripts/release_gate.py plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md plugins/figure-agent/docs/milestones/2026-06-08-real-figure-panel-c-candidate-dogfood.md
git commit -m "Record real Panel C candidate dogfood"
```

## Final Verification

Run from `plugins/figure-agent`:

```bash
PY314=$(python3 - <<'PY'
import sys
print(sys.executable)
PY
)
UV_PYTHON="$PY314" uv run pytest -q tests
```

Also run:

```bash
git diff --check
claude plugin validate <unpacked-cowork-zip> --strict
claude plugin validate .claude-plugin/marketplace.json
```

## Plan Self-Review

- Spec coverage: covers TeX index, panel model, candidate family, sandbox review packet, MCP facade, release gate, and real dogfood.
- Scope: intentionally implements only Panel C `energy-trap-alignment` first; full compile/export/crop sandbox is represented as staged metadata in this slice, not fully compiled.
- Known deferral: real before/after image crops require the next render-stage implementation. This plan still makes real fig1 leave `no_supported_candidate`.
