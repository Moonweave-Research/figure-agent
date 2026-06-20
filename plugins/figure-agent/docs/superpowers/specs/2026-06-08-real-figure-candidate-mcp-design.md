# Real-Figure Candidate Engine and MCP Review Surface Design

Status: draft for review

Target: figure-agent after the reference-aware candidate-search vertical slice

## Summary

The first candidate-search slice proved the safety shell:

```text
intent -> candidates -> render-candidates -> rank-candidates -> review-candidate
```

It works on a synthetic fixture and is exposed through read-only MCP tools. The
dogfood on `fig1_overview_v2_pair_001_vault` showed the real blocker:

```json
{"refusals": [{"code": "no_supported_candidate"}]}
```

The MCP facade can ask for candidates, render them, rank them, and prepare
review packets. It cannot make the figure better when the core engine cannot
generate real-figure candidates. The next upgrade must therefore build a
panel-aware, TeX-pattern-aware candidate engine, then expose its evidence through
a richer MCP review surface.

Product principle:

> MCP should make candidate evidence easier to inspect and approve. Core
> candidate modules should make better alternatives exist.

## Dogfood Baseline

Fixture:

```text
plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault
```

Observed state:

- `status`: accepted, critique fresh, audit evidence passed, publication gate
  passed.
- First blocker: `export_tracked_golden`, a human approval boundary.
- `intent`: six panels A-F were detected with source, caption, reference image,
  panel references, and perception pack present.
- `candidates`: empty candidate set with `no_supported_candidate`.
- `render-candidates` and `rank-candidates`: valid empty results.

Interpretation:

- Runtime separation and MCP/CLI contracts are not the current bottleneck.
- The current candidate generator only handles a toy single-line label-offset
  pattern.
- Real figures need candidate families for complex TikZ source patterns:
  panels, plots, arrows, labels, apparatus blocks, marker glyphs, and energy
  diagrams.

## Goals

1. Generate at least one useful candidate on a real mature fixture without
   mutating source.
2. Support panel-scoped candidate search so operators can ask for Panel C or
   Panel F rather than the whole figure.
3. Make candidate generation evidence-backed: each candidate must point to TeX
   selectors, panel/subregion identity, source hashes, and rendered artifacts.
4. Add visual review packets with before/after crop metadata so Claude/Cowork
   can inspect candidates without guessing file paths.
5. Keep accepted/golden/export roll-forward under explicit human authority.
6. Keep MCP read-only for source mutation in this phase.

## Non-Goals

- Do not make MCP directly edit source files.
- Do not claim automatic Nature/Science acceptance.
- Do not use external image-generation APIs.
- Do not infer new scientific claims from visual style.
- Do not generalize to every TikZ construct in one pass.
- Do not mutate `fig1_overview_v2_pair_001_vault` accepted/golden outputs during
  dogfood.

## Architecture

Use a two-track architecture.

### Boundary Definitions

The implementation must keep three write classes separate:

| Write class | Allowed in this phase? | Notes |
|---|---:|---|
| Candidate evidence under `examples/<name>/build/candidates/` | yes | Generated sandbox state; safe even when the fixture is accepted/golden. |
| Normal build/cache files outside `build/candidates/` | only through existing compile/export commands | Candidate commands must not refresh accepted exports or publication artifacts as a side effect. |
| Source, accepted exports, golden exports, final artifacts, publication files | no | Requires explicit human-approved CLI apply/export flow outside MCP. |

For an accepted/golden fixture such as `fig1_overview_v2_pair_001_vault`,
candidate search is allowed to create sandbox evidence, but every candidate must
default to `review_only` unless the apply path later proves that accepted/golden
roll-forward approval has been granted.

The source trust boundary is content-hash based, not git-commit based. A dirty
worktree is allowed for read-only candidate exploration, but every candidate and
review packet must record:

- source file hash at candidate generation time;
- selected range hash;
- whether the workspace had uncommitted changes in the fixture;
- whether any uncommitted change is in an affected file.

Apply preparation must refuse or downgrade when the affected source file changed
after candidate generation.

### Track A: Real-Figure Candidate Core

The core owns candidate creation, sandbox rendering, scoring, and apply
authority. It must work through CLI without MCP.

New or expanded modules:

| Module | Responsibility |
|---|---|
| `candidate_tex_index.py` | Build a read-only index of panel scopes, node names, draw commands, labels, style tokens, and line ranges from fixture TeX. |
| `candidate_panel_model.py` | Join `spec.yaml` panel bboxes, briefing roles, source selectors, and rendered crop paths into a panel-level model. |
| `candidate_families.py` | Produce bounded edit alternatives for supported pattern families. |
| `candidate_visual_packets.py` | Create before/after crop descriptors and artifact metadata for review. |
| `candidate_rank.py` | Extend scoring to include panel-local visual deltas and human-review burden. |

Existing modules remain authoritative for contracts:

- `candidate_contracts.py`
- `figure_intent_model.py`
- `candidate_generator.py`
- `candidate_render.py`
- `candidate_review_packet.py`
- `candidate_apply.py`

### Track B: MCP Review Surface

MCP must expose the candidate workflow as structured inspection tools, not as
hidden mutation.

Expanded tools:

| Tool | Contract |
|---|---|
| `figure_agent_analyze_panel` | Return one panel's intent, selectors, artifacts, and known blockers. |
| `figure_agent_propose_panel_improvements` | Return candidate set filtered by panel and candidate family. |
| `figure_agent_render_candidates` | Continue to render fixture-local candidate sandboxes under lock. |
| `figure_agent_compare_candidate` | Return before/after artifact descriptors, score, and review checklist for one candidate. |
| `figure_agent_explain_no_candidate` | Explain why no candidate was produced and which candidate family is missing. |
| `figure_agent_prepare_apply_command` | Return a CLI command suggestion only when a candidate is eligible; never mutate. |

MCP source mutation remains unsupported:

```json
{
  "schema": "figure-agent.mcp.apply-candidate.v1",
  "success": false,
  "error": {
    "category": "unsupported_operation",
    "message": "apply_requires_cli_opt_in"
  }
}
```

## Candidate Families

Implement candidate families incrementally. Each family must have synthetic unit
tests and one real-figure dogfood fixture check.

Candidate family names are stable public strings:

| Family | Public name |
|---|---|
| Plot marker and curve hierarchy | `plot-marker-hierarchy` |
| Energy diagram and trap marker alignment | `energy-trap-alignment` |
| Apparatus label and callout routing | `apparatus-callout-routing` |

A command with an unknown family fails as `unsupported_candidate_family`. A
known family that does not support the selected panel fails as
`unsupported_panel_family`.

Candidate ids must be deterministic within a candidate set. The id seed is:

```text
fixture + panel + family + selector_text_hash + operation_payload_hash
```

The display form remains `CAND001`, `CAND002`, ... ordered by deterministic
sort key, but each candidate also carries a stable `candidate_hash`.

### Family 1: Plot Marker and Curve Hierarchy

Target panels:

- Panel D kinetic plot
- Panel E `V_s(t)` and `g(E_t)` plots

Candidate examples:

- reduce hollow marker dominance on already clear curves;
- increase visual separation between shallow/deep peaks;
- normalize curve/marker z-order;
- adjust label offsets for `low n`, `high n`, `Debye`, `Shallow`, `Deep`.

Allowed edits:

- style token changes;
- marker size changes;
- label coordinate offsets;
- local draw ordering within a panel scope.

Forbidden edits:

- changing curve direction;
- changing data meaning;
- changing axis labels or material identity.

### Family 2: Energy Diagram and Trap Marker Alignment

Target panel:

- Panel C energy diagram and localized-trap bridge.

Candidate examples:

- align trap markers with corresponding shallow/deep energy levels;
- reduce ambiguity between mobility edge, vacuum, and trap distributions;
- adjust dashed connector endpoints to reduce crossing or weak association;
- tighten `deep` and `shallow` label spacing.

Allowed edits:

- local coordinate offsets;
- line endpoint offsets;
- label offsets;
- style-token normalization.

Forbidden edits:

- changing `E_C`, `E_V`, vacuum, mobility edge ordering;
- changing shallow/deep semantics;
- deleting trap levels.

### Family 3: Apparatus Label and Callout Routing

Target panels:

- Panel E probe/corona apparatus
- Panel F actuator/electrode/air-gap schematic

Candidate examples:

- route callout lines away from dense apparatus edges;
- improve `q_tr`, `Coulomb repulsion`, `air gap`, and `electrode` label
  clearance;
- reduce collision risk between device blocks and annotations.

Allowed edits:

- label offsets;
- leader-line endpoint offsets;
- callout bend-point changes.

Forbidden edits:

- changing device topology;
- changing polarity or force direction;
- deleting required apparatus components.

## TeX Selector Contract

Every candidate must be grounded in a stable selector.

Required selector fields:

```json
{
  "kind": "tex_selector.v1",
  "path": "examples/<name>/<name>.tex",
  "panel": "C",
  "line_start": 120,
  "line_end": 148,
  "source_hash": "sha256:...",
  "selector_text_hash": "sha256:...",
  "anchors": ["node:trapDeepA", "style:cTrapDeep"]
}
```

Selector rules:

- The path must resolve inside `examples/<name>`.
- The selected source range must match the stored hash before render/apply.
- Candidates may include multiple selectors only when all are in the same
  fixture.
- A panel-scoped candidate must not modify another panel unless the review
  packet marks it as cross-panel and downgrades to `review_only`.
- Selectors must be derived from active source text only; comments can define
  panel boundaries but cannot by themselves prove a drawable element exists.
- If a TeX command spans multiple lines, the selector must include the full
  command range, not just the anchor line.
- Candidate operations must be structured. Free-form `replace_text` is allowed
  only as a compatibility fallback when the selector range hash proves the
  replacement is local.

Initial selector extraction may use existing source comments such as
`% Panel C ...` and `Panel C bbox` as panel-boundary hints, but the indexer must
also verify that the selected lines fall inside the declared `spec.yaml` panel
or are explicitly marked cross-panel.

## Coordinate and Crop Contract

`spec.yaml.panels[].bbox_pdf_cm` is the canonical panel crop input. Because PDF
coordinate systems, TikZ coordinates, and PNG pixel coordinates differ, the
panel model must record the coordinate system for every bbox and crop:

```json
{
  "bbox_pdf_cm": [8.914, 0.141, 17.878, 5.227],
  "coordinate_system": "pdf_cm_bottom_left",
  "render_size_px": [1920, 1280],
  "crop_px": [x0, y0, x1, y1]
}
```

Before/after panel crops must be generated through one shared crop helper so
ranking, review packets, and MCP resources cannot disagree about panel bounds.
If no current render exists, review packets may include source-only evidence but
must mark `visual_review.status = "missing_render"`.

## Render Sandbox Contract

The current `render-candidates` command writes candidate source copies and
manifests. This spec requires a second render stage:

1. `prepare`: write candidate source copy and manifest.
2. `compile`: compile the candidate source in the sandbox.
3. `export`: produce candidate PDF/SVG/PNG artifacts in the sandbox.
4. `crop`: produce before/after panel crops for visual review.

Each stage must be explicit in the render result:

```json
{
  "candidate_id": "CAND001",
  "stages": {
    "prepare": "passed",
    "compile": "passed",
    "export": "passed",
    "crop": "passed"
  }
}
```

If compile/export is unavailable on the host, render may return a partial
manifest but rank must downgrade the candidate to `review_only` or `rejected`
with a dependency-specific reason.

Sandbox compile rules:

- all candidate aux/build/export files must remain under
  `examples/<name>/build/candidates/<candidate_id>/`;
- bundled styles are read from `plugin_root/styles`;
- fixture-local inputs are read from `examples/<name>`;
- the candidate source copy overlays only the affected source file for compile;
- accepted/golden exports under `examples/<name>/exports/` are read-only inputs
  at most and must never be overwritten;
- a failed sandbox compile records stderr/stdout in bounded form and produces no
  normal fixture build artifacts.

## Data Flow

Panel-scoped happy path:

```text
fig-agent analyze-panel fig1 C --json
  -> candidate_panel_model

fig-agent candidates fig1 --panel C --family energy-trap-alignment \
  --json --output build/candidates/panel_C_candidate_set.json
  -> candidate_tex_index
  -> candidate_families
  -> candidate-set

fig-agent render-candidates fig1 \
  --candidate-set build/candidates/panel_C_candidate_set.json
  -> build/candidates/CAND001/

fig-agent rank-candidates fig1 \
  --candidate-set build/candidates/panel_C_candidate_set.json --json
  -> candidate-rank-result

fig-agent review-candidate fig1 CAND001 --json
  -> candidate-review-packet with before/after artifacts
```

MCP path:

```text
figure_agent_analyze_panel
figure_agent_propose_panel_improvements
figure_agent_render_candidates
figure_agent_compare_candidate
figure_agent_prepare_human_review
```

## Review Packet Contract

A candidate review packet must include:

- candidate metadata;
- affected selectors;
- before source hash;
- sandbox source hash;
- rendered PDF/SVG/PNG descriptors when present;
- panel crop descriptors when available;
- hard gate results;
- effective apply authority;
- semantic risks;
- human checklist;
- recommended next CLI command.

Minimum schema addition:

```json
{
  "schema": "figure-agent.candidate-review-packet.v1",
  "fixture": "fig1",
  "candidate_id": "CAND001",
  "panel": "C",
  "visual_review": {
    "before": [{"uri": "figure://fig1/panel/C/before.png"}],
    "after": [{"uri": "figure://fig1/candidates/CAND001/panel/C/after.png"}],
    "checklist": [
      "trap markers still map to shallow/deep semantics",
      "energy ordering is unchanged",
      "label clearance improved"
    ]
  },
  "effective_apply_authority": "review_only"
}
```

## Scoring

Hard gates run first:

- source hash matches;
- candidate renders;
- candidate artifacts are fixture-local;
- no accepted/golden/export mutation;
- no semantic invariant violation;
- no path escape or symlink escape;
- no cross-panel edit without explicit review-only downgrade.

Soft scores are advisory:

- label clearance delta;
- connector crossing delta;
- marker/curve hierarchy delta;
- local whitespace balance;
- reference-style consistency;
- human-review burden.

Ranking may preserve or downgrade `apply_authority`; it must never upgrade it.

## Error Handling

Required refusal codes:

| Code | Meaning |
|---|---|
| `no_supported_candidate` | Source parsed, but no implemented family found a candidate. |
| `unsupported_candidate_family` | Operator requested a family name the plugin does not know. |
| `unsupported_panel_family` | Operator requested a family not implemented for that panel. |
| `source_selector_unstable` | Selector hash or line range changed before render/rank. |
| `affected_source_dirty` | Candidate targets a file with uncommitted changes that were not part of the candidate base hash. |
| `accepted_golden_boundary` | Candidate would require accepted/golden/export roll-forward. |
| `semantic_invariant_missing` | Candidate is semantic-risky and no invariant file exists; generation may continue only as `review_only`. |
| `panel_scope_ambiguous` | Candidate cannot be tied to one panel or declared cross-panel scope. |
| `candidate_render_dependency_missing` | Host lacks a dependency needed for sandbox compile/export/crop. |

`explain_no_candidate` must convert these codes into actionable next work:

```text
Panel C has source and reference context, but no energy-trap-alignment family is
implemented. Add a candidate family that recognizes energy-level lines, trap
markers, and shallow/deep labels.
```

## CLI Surface

Add:

```text
fig-agent analyze-panel <name> <panel-id> --json
fig-agent candidates <name> [--panel <panel-id>] [--family <family>] --json [--output <path>]
fig-agent compare-candidate <name> <candidate-id> --json
fig-agent explain-no-candidate <name> [--panel <panel-id>] --json
```

Keep:

```text
fig-agent render-candidates <name> --candidate-set <path>
fig-agent rank-candidates <name> --candidate-set <path> --json
fig-agent review-candidate <name> <candidate-id> --json
```

Do not add MCP source-apply mutation in this phase.

## MCP Resource Templates

Add resource templates for candidate inspection:

```text
figure://{name}/panel/{panel_id}/intent
figure://{name}/panel/{panel_id}/current-render
figure://{name}/candidates/{candidate_id}/manifest
figure://{name}/candidates/{candidate_id}/review
figure://{name}/candidates/{candidate_id}/artifacts/{artifact}
```

Resource reads return metadata and bounded text/JSON where safe. Large binary
artifacts should be exposed as paths/URIs, not inlined.

## Tests

Contract tests:

- panel analyzer rejects escaped fixture and panel ids;
- candidate set filters by panel and family;
- no-candidate explanation is deterministic;
- MCP tool list includes new tools;
- MCP resource templates are templates, not literal resources;
- MCP apply still refuses mutation.

Candidate family tests:

- synthetic Panel C energy diagram yields at least two bounded candidates;
- synthetic Panel D plot marker hierarchy yields at least two candidates;
- synthetic Panel F callout route yields at least two candidates;
- multiline TeX command selectors include the full command range;
- comment-only matches do not produce drawable candidates;
- PDF-cm bboxes map to deterministic PNG crop rectangles;
- dirty affected source files downgrade apply preparation;
- accepted/golden fixtures still allow `build/candidates/` evidence writes but
  do not permit source/export mutation;
- selector hash drift blocks render/rank;
- cross-panel edits downgrade to `review_only`.

Real fixture dogfood tests:

- `fig1_overview_v2_pair_001_vault --panel C --family energy-trap-alignment`
  yields a non-empty candidate set or a specific `unsupported_panel_family`
  refusal before the family is implemented.
- after Family 2 lands, Panel C yields at least one rendered candidate and a
  review packet with before/after artifact descriptors.
- no command mutates accepted/golden exports without explicit human approval.

Release gate:

- targeted tests include the new panel/candidate/MCP tests;
- schema/module map includes new schemas;
- package audit still excludes real manuscript build/export artifacts.

## Acceptance Criteria

The upgrade is accepted when:

1. On a synthetic fixture, each new family produces multiple candidates.
2. On `fig1_overview_v2_pair_001_vault`, at least one panel-scoped command
   produces a non-empty candidate set.
3. The candidate prepare/compile/export/crop stages are represented in
   `build/candidates/<candidate_id>/`; host dependency gaps are explicit.
4. On the real Panel C dogfood path, the review packet exposes before/after
   artifact descriptors. `missing_render` is acceptable only in a dedicated
   host-dependency-negative test, not as the success path.
5. MCP can drive analyze/propose/render/compare/review without source mutation.
6. `figure_agent_apply_candidate` still refuses MCP-side apply.
7. Full targeted tests and release gate pass.

## Implementation Order

1. Build `candidate_tex_index.py` with read-only TeX selector extraction.
2. Build `candidate_panel_model.py` and `fig-agent analyze-panel`.
3. Add `--panel` and `--family` filters to `fig-agent candidates`.
4. Add shared PDF-cm to PNG crop conversion and source dirty-state recording.
5. Implement Family 2 first for Panel C energy/trap alignment because the
   dogfood image shows a clear, high-value panel-local target.
6. Extend `render-candidates` from manifest-only prepare to staged
   prepare/compile/export/crop.
7. Add visual review packet artifact descriptors.
8. Add MCP panel tools and candidate resources.
9. Dogfood on Panel C of `fig1_overview_v2_pair_001_vault`.
10. Add Family 1 or Family 3 based on the Panel C dogfood result.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| TeX parsing becomes too broad | Start with conservative selector patterns and explicit family tests. |
| Candidate looks better but changes science | Semantic-risk candidates default to `review_only`; hard gates preserve human authority. |
| MCP hides important boundaries | MCP tools return structured refusal codes and never mutate source. |
| Real fig1 accepted state is accidentally changed | Dogfood writes only under `build/candidates/`; export roll-forward remains human-gated. |
| Review packet overwhelms Claude/Cowork | Use resource descriptors and panel-scoped packets instead of embedding large artifacts. |
| Panel crops disagree across tools | Use one shared crop helper and record coordinate systems in every panel model. |
| Dirty user work is overwritten or mis-ranked | Record dirty-state, affected file hashes, and downgrade apply preparation on drift. |

## Self-Review Notes

- The spec separates the real bottleneck from MCP facade work.
- The first real target is Panel C because dogfood showed the whole fixture is
  accepted/golden-gated but still has a visually inspectable panel-local
  candidate opportunity.
- MCP improvements are valuable only after candidate evidence exists; this is
  reflected in the implementation order.
- Source mutation remains out of scope for MCP in this phase.
- Review pass 2 closed gaps around accepted/golden write boundaries, dirty
  source state, coordinate/crop contracts, staged sandbox rendering, and
  comment-only TeX selector false positives.
