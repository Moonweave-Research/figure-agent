# Reference-Conditioned Authoring Loop Milestone

**Status:** PLANNED
**Filed:** 2026-05-16
**Scope owner:** `figure-agent`
**Primary pilot:** `examples/fig1_overview_v2_pair_001_vault`
**Decision frame:** keep `figure-agent` as a quality kernel, then add the
minimum authoring-intelligence layer needed for LLM-authored professional
scientific schematics.

---

## 1. Goal

Make the active figure workflow capable of producing manuscript-grade,
theory-respecting scientific schematics with an LLM doing most of the drawing
work and the human acting as the final domain/aesthetic gate.

The milestone does **not** make the plugin an image-generation orchestrator.
The plugin continues to consume local references, TikZ source, build artifacts,
and critique outputs. The new work fills the missing layer between intent and
TikZ authoring: reference roles, theory guards, panel/sub-region iteration, and
auditable quality decisions.

## 2. External calibration

Current scientific-figure tooling is converging on a hybrid pattern:

- AI drafts or adapts a figure from text, sketch, or reference.
- The output remains editable as SVG, PPTX, or another vector surface.
- Human review remains required before formal/research use.
- Provenance and disclosure matter because many publishers remain conservative
  about generative-AI-created images.

Reference points:

- BioRender AI tools emphasize AI-assisted first drafts and targeted edits, but
  still recommend reviewing outputs before formal/research use:
  <https://www.biorender.com/ai-tools>
- FigPad markets text, sketch, reference-image, and vectorizer workflows with
  editable SVG/PPTX export:
  <https://figpad.ai/>
- AutoFigure-Edit frames the research direction as long-form scientific text +
  reference-guided styling + native SVG editing:
  <https://arxiv.org/abs/2603.06674>
- Nature Reviews Physics notes that generative-AI science-communication outputs
  must be checked by experts:
  <https://www.nature.com/articles/s42254-024-00691-7>
- Elsevier's current journal policy does not permit generative AI or
  AI-assisted tools to create or alter images in submitted manuscripts except
  where the tool is part of the research design/methods:
  <https://www.elsevier.com/en-au/about/policies-and-standards/generative-ai-policies-for-journals>

Implication for this repo: optimize for editable source, provenance, reference
grounding, and human accountability rather than a black-box prompt-to-final PNG.

## 3. Current gap

The existing kernel is strongest after authoring:

```text
briefing/spec/reference -> semantic TikZ -> compile -> visual checks
-> critique -> export -> status/reproducibility
```

The weak point is before and during authoring:

```text
scientific claim + references + theory constraints
-> authoring plan
-> panel/sub-region drawing decisions
-> patch loop
```

Without this missing layer, an LLM can produce valid TikZ that still has the
wrong polymer topology, wrong visual hierarchy, wrong reference transfer, or
wrong theory. Compile/export gates catch file and rendering failures; they do
not prove the figure is scientifically or aesthetically right.

## 4. Non-goals

- No external image-generation API call from the plugin.
- No automatic PNG/SVG-to-TikZ reconstruction as the main path.
- No large reference vault or retrieval layer until the consumer path proves it
  improves actual figure quality.
- No auto-acceptance of LLM critique findings.
- No broad ontology platform. Start with one figure family and one controlled
  pilot.

## 5. Milestone shape

This milestone has six deliverable layers. Each layer must be validated on the
primary pilot before generalization.

### M1.1 Design Contract v1

**Purpose:** turn loose prose intent into a compact contract the LLM author,
critique prompt, and human reviewer can all use.

**Artifact:** `examples/<name>/authoring_contract.md`

**Required sections:**

```markdown
# Authoring Contract: <name>

## Figure Claim
<one paragraph: what the whole figure must communicate>

## Panel Claims
- A: <one sentence>
- B: <one sentence>

## Theory Invariants
- BLOCKER: <must be true; violation makes figure scientifically wrong>
- MAJOR: <must be true for clear interpretation>

## Forbidden Transfers
- <what must not be copied from references or generated drafts>

## Visual Hierarchy
- Primary read path: <left-to-right/top-to-bottom path>
- Hero element: <panel/sub-region>
- De-emphasized elements: <list>

## Acceptance Rubric
- BLOCKER: <reject conditions>
- MAJOR: <revise conditions>
- MINOR: <polish conditions>
```

**Pilot requirement:** Panel A must explicitly encode the linear/polymer-network
topology decision so the sulfur/DIB chemistry is not inferred from a generic
reference image.

**Exit gate:**

- `authoring_contract.md` exists for the pilot.
- `/fig_critique` prompt or manual critique brief can quote the contract without
  needing to re-read chat history.
- A reviewer can identify the top five BLOCKER invariants from the file alone.

### M1.2 Role-Typed Reference Pack v1

**Purpose:** stop treating all references as generic visual targets.

**Artifact:** `examples/<name>/reference/reference_pack.md`

**Reference roles:**

| Role | Meaning | Example use |
|---|---|---|
| `topology` | scientific structure that must be preserved | linear chain vs network |
| `motif` | reusable visual object | sulfur ring, polymer segment, trap lobe |
| `layout` | panel composition or read path | row-level flow, hero-center panel |
| `style` | color, stroke, typography, journal feel | muted palette, soft labels |
| `label_hierarchy` | what text is prominent vs secondary | panel title vs callout |
| `anti_reference` | tempting but wrong pattern | network-looking polymer if claim is linear |

**Required format:**

```markdown
# Reference Pack: <name>

| File | Role | Use | Do Not Transfer |
|---|---|---|---|
| reference/panel_A_topology.png | topology | preserve linear chain topology | do not copy exact color/noise |
```

**Exit gate:**

- Every reference file used in authoring has a role.
- At least one `anti_reference` or `Do Not Transfer` row exists for the pilot.
- The pack distinguishes style transfer from scientific topology transfer.

### M1.3 Authoring Plan Gate

**Purpose:** make the LLM explain drawing strategy before writing or patching
TikZ.

**Artifact:** `examples/<name>/authoring_plan.md`

**Required sections:**

```markdown
# Authoring Plan: <name>

## Inputs Read
- briefing.md
- authoring_contract.md
- reference/reference_pack.md
- coordinate_hints.yaml, if present

## Panel Strategy
- A: <semantic objects, TikZ primitives/macros, key risks>
- B: <semantic objects, TikZ primitives/macros, key risks>

## Theory Decisions
- <decision>: <source in contract or reference pack>

## Patch Order
1. <highest-risk panel/sub-region>
2. <next>

## Human Checkpoints
- <decisions the human must approve before final export>
```

**Exit gate:**

- The plan names the exact panel/sub-region patch order.
- The plan states which decisions are theory-critical and which are aesthetic.
- The first TikZ patch can be traced back to one plan item.

### M1.4 Sub-Region Active-Set Loop

**Purpose:** make iteration happen at the unit people actually patch, not only
at whole-figure or panel level.

**Artifact:** extend the existing text-form sub-region list in `briefing.md` or
create `examples/<name>/subregion_iteration_log.md`.

**Required log format:**

```markdown
# Sub-Region Iteration Log: <name>

| Iteration | Sub-region ID | Problem | Patch Summary | Result | Follow-up |
|---|---|---|---|---|---|
| 001 | A-chem-chain | topology reads network-like | rewrote chain as linear repeat | improved | check sulfur labels |
```

**Exit gate:**

- At least five real iterations are logged on the pilot.
- Each iteration targets one sub-region or one cross-panel structure.
- The log distinguishes `named but stable` regions from `active patch` regions.

### M1.5 Domain Theory Guard v1

**Purpose:** catch scientific nonsense before visual polish.

**Artifact:** `examples/<name>/theory_guard.md`

**Required format:**

```markdown
# Theory Guard: <name>

| ID | Severity | Claim | Check Method | Pass Evidence |
|---|---|---|---|---|
| TG-A-001 | BLOCKER | Panel A polymer topology matches the manuscript claim | visual + source review | <filled during audit> |
```

**Pilot guard candidates:**

- Polymer topology: linear vs network must match the claim.
- Sulfur/DIB depiction must not imply a different crosslinking mechanism than
  the text.
- Arrows must not imply unsupported causality.
- Trap/energy landscape orientation must match the manuscript reading.

**Exit gate:**

- At least three BLOCKER checks exist.
- Every BLOCKER check has a pass/fail decision during `QUALITY_AUDIT`.
- Any failed BLOCKER prevents `accepted: true`.

### M1.6 Evaluator Ladder and Acceptance

**Purpose:** separate "compiled" from "accepted for manuscript use."

**Required sequence for the pilot:**

```text
1. /fig_compile
2. static collision/clash/drift review
3. /fig_critique with contract + reference pack available
4. author adjudication of critique findings
5. QUALITY_AUDIT.md
6. blind or side-by-side A/B comparison when a previous version exists
7. provenance/publication-compliance review
8. accepted flag only after theory, visual, and publication-compliance gates pass
```

**Artifact:** `examples/<name>/QUALITY_AUDIT.md`

**Minimum sections:**

```markdown
# QUALITY_AUDIT: <name>

## Build Evidence
- compile command:
- export command:
- status command:

## Theory Guard Result
- BLOCKER pass/fail summary:

## Visual Quality Result
- hierarchy:
- label placement:
- reference-role fidelity:
- panel rhythm:

## Critique Adjudication
- true positives applied:
- false positives rejected:
- missed issues added:

## Provenance and Publication Compliance
- target venue or policy family:
- AI/tool role:
- human-authored or human-edited source files:
- source provenance:
- disclosure needed: yes|no|unknown
- submission-safe for this target: yes|no|unknown

## Acceptance Decision
- accepted: true|false
- reason:
```

**Exit gate:**

- The audit explicitly says `accepted: true` or `accepted: false`.
- `accepted: true` is impossible with unresolved theory BLOCKERs.
- `accepted: true` is impossible when publication-compliance status is
  `unknown` or `no` for the intended target.
- The audit records which LLM findings were rejected, not only which were
  applied.

## 6. Pilot starter content

The first pass should start from the following concrete content rather than a
blank template.

### 6.1 Pilot figure claim

`fig1_overview_v2_pair_001_vault` should read as a cover-style graphical
abstract, not a result-table or plot grid. The 30-second message is:

> Sulfur-rich polymer contains deep charge traps; three independent evidence
> paths point to the same trap landscape; the trapped charge manifests as
> macroscopic Coulomb-driven bending.

The primary read path is:

```text
Panel A material identity
-> Panel B molecular heterogeneity
-> Panel C trap landscape hero
-> Row 2 three-spoke evidence radiation
-> Panel G mechanical manifestation
```

### 6.2 Pilot panel claims

| Panel | Claim | Critical risk |
|---|---|---|
| A | poly(S-r-DIB) primary microstructure, locked to linear DIB-polysulfide-DIB grammar | accidentally implying a 2D crosslinked network |
| B | variable S60-S85 chain-length scaffold | becoming a quantitative composition plot |
| C | hero trap landscape combining real-space polymer traps and energy diagram | spatially segregating shallow/deep traps or weakening deep-trap hierarchy |
| D | kinetic non-Debye I(t) evidence icon | reading as measured plot with ticks/data |
| E | ISPD raw decay icon | over-detailed plot frame |
| F | ISPD-derived bimodal g(E_t) icon | color/order mismatch with Panel C |
| G | Coulomb-driven bending scene | adding Maxwell-attraction or wrong clamp orientation |

### 6.3 Pilot BLOCKER invariants

| ID | Invariant | Reason |
|---|---|---|
| TG-A-001 | Panel A must depict linear poly(S-r-DIB) primary microstructure, not a crosslinked network. | Wrong topology changes the material claim. |
| TG-C-001 | Panel C must show shallow and deep traps in the same polymer matrix, not spatially separate materials. | Wrong trap distribution changes the physical model. |
| TG-CF-001 | Shallow is blue and deep is red consistently across Panels C, F, and G. | Color mismatch breaks evidence unification. |
| TG-D-001 | Panel D non-Debye tail must lie above the Debye reference at long times. | Reversing it changes the kinetic claim. |
| TG-G-001 | Panel G uses Coulomb repulsion only, with top clip and polymer hanging down. | Maxwell attraction or wrong clamp direction changes the mechanism. |
| TG-R2-001 | Row 2 arrows are three independent evidence spokes, not a D->E->F->G causation chain. | Linear causation would misstate the experiment logic. |

### 6.4 Pilot reference-role seed

| File or source | Role | Use | Do Not Transfer |
|---|---|---|---|
| `reference/codex_gen_overview_v1.png` | layout/style | overall cover composition and soft scientific-illustration feel | do not treat every visual detail as ground-truth chemistry |
| `reference/sulfur_polymer_panelA_ref.png` | topology/motif | sulfur/DIB polymerization grammar and sulfur-rich material identity | do not copy a topology that contradicts the locked linear primary microstructure |
| `manual_seed_cho2024_fig1_s8_polymerization` | motif | S8 ring-opening and inverse-vulcanization visual grammar | do not reinterpret as 2D network formation |
| `manual_seed_natcommun2024_fig1` | motif/layout | energy landscape and trap hierarchy grammar | do not copy unrelated material phases |
| external network-like multi-panel references | anti_reference | useful only as a negative example for Panel A | do not import network topology into Panel A |

### 6.5 Pilot active patch order

1. Panel A topology and chemistry readability.
2. Panel C left polymer sample readability and trap-site hierarchy.
3. Row 2 three-spoke evidence radiation.
4. Panels D/E/F plot-to-icon reduction.
5. Panel G Coulomb scene and clamp orientation.
6. Cross-panel color and label hierarchy.

## 7. Implementation order

### Worktree safety rule for every task

Before any task commit:

```bash
git status --short
```

The current pilot may already contain unrelated dirty authoring edits. Stage
only the paths listed in that task's **Files** section. Do not stage existing
dirty `briefing.md`, `.tex`, `build/`, or `exports/` changes unless that task
explicitly owns them.

Use path-specific staging:

```bash
git add <exact file path 1> <exact file path 2>
git diff --cached --stat
git commit -m "<task-specific message>"
```

### Task 1: Pilot contract and reference pack

**Files:**

- Create: `plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/authoring_contract.md`
- Create: `plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/reference/reference_pack.md`

**Steps:**

- Read `briefing.md`, `spec.yaml`, current `.tex`, and `coordinate_hints.yaml`
  if present. If `coordinate_hints.yaml` is missing, record that in
  `authoring_contract.md` under source limitations instead of fabricating
  placement evidence.
- Draft the contract with panel claims, BLOCKER invariants, forbidden transfers,
  visual hierarchy, and acceptance rubric.
- Draft the reference pack with one role row per reference file.
- Verify no section relies on chat-only knowledge.
- Commit only these two files.

**Verification:**

```bash
git status --short
test -f plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/authoring_contract.md
test -f plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/reference/reference_pack.md
rg "BLOCKER|Forbidden Transfers|Reference Pack|Do Not Transfer" plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault
git diff --cached --stat
```

### Task 2: Authoring plan gate

**Files:**

- Create: `plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/authoring_plan.md`
- Modify: `plugins/figure-agent/skills/figure-agent/SKILL.md`

**Steps:**

- Add an authoring-plan step to the skill workflow before semantic TikZ edits.
- Write the pilot `authoring_plan.md` from the contract and reference pack.
- Ensure the plan names panel/sub-region patch order and human checkpoints.
- Commit the skill doc and pilot plan together.

**Verification:**

```bash
git status --short
rg "authoring_plan|Authoring Plan" plugins/figure-agent/skills/figure-agent/SKILL.md plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/authoring_plan.md
git diff --cached --stat
```

### Task 3: Sub-region iteration log

**Files:**

- Create: `plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/subregion_iteration_log.md`
- Modify: `plugins/figure-agent/docs/subregion-iteration-tool.md`

**Steps:**

- Start the iteration log using the existing sub-region enumeration.
- Record at least the current active target set before further drawing patches.
- Update `subregion-iteration-tool.md` to point to the pilot log as the live
  evidence source.
- Commit the log and doc update.

**Verification:**

```bash
git status --short
rg "Sub-Region Iteration Log|active target|fig1_overview_v2_pair_001_vault" plugins/figure-agent/docs/subregion-iteration-tool.md plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/subregion_iteration_log.md
git diff --cached --stat
```

### Task 4: Theory guard

**Files:**

- Create: `plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/theory_guard.md`
- Modify: `plugins/figure-agent/docs/architecture-overview.md`

**Steps:**

- Add theory guard as an authoring/acceptance layer between Layer 2 and Layer
  4.5, not as a compile gate.
- Write at least three BLOCKER guard rows for the pilot.
- State that failed theory guards block `accepted: true` even if compile/export
  pass.
- Commit the theory guard and architecture doc update.

**Verification:**

```bash
git status --short
rg "Theory Guard|accepted: true|BLOCKER" plugins/figure-agent/docs/architecture-overview.md plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/theory_guard.md
git diff --cached --stat
```

### Task 5: QUALITY_AUDIT pilot

**Files:**

- Create: `plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/QUALITY_AUDIT.md`
- Modify, if needed: `plugins/figure-agent/docs/quality-kernel-goal.md`

**Steps:**

- Run the current compile/status/export commands for the pilot and paste the
  exact command lines plus pass/fail summaries into `QUALITY_AUDIT.md`.
- Fill build evidence, theory guard result, visual quality result, critique
  adjudication, provenance/publication-compliance review, and acceptance
  decision.
- Keep `accepted: false` unless all BLOCKER and MAJOR issues are resolved and
  publication-compliance status is target-safe.
- Update `quality-kernel-goal.md` only if the audit reveals a durable policy
  change.
- Commit the audit and any policy doc update.

**Verification:**

```bash
git status --short
bash scripts/compile.sh examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex
uv run python scripts/status.py fig1_overview_v2_pair_001_vault
uv run python scripts/run_export.py fig1_overview_v2_pair_001_vault
uv run pytest -q
uv run ruff check .
rg "accepted: false|accepted: true|Theory Guard Result|Critique Adjudication|Provenance and Publication Compliance|submission-safe" plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/QUALITY_AUDIT.md
git diff --cached --stat
```

### Task 6: Decide whether to implement tooling

**Files:**

- Create: `plugins/figure-agent/docs/milestones-archive/2026-05-16-reference-conditioned-authoring-loop-decision.md`

**Steps:**

- Review Tasks 1-5 artifacts.
- Decide whether the next implementation should be:
  - `contract/reference-pack` parser,
  - `/fig_critique` prompt integration,
  - sub-region active-set parser,
  - theory-guard checker,
  - or no code yet because the manual protocol is still unstable.
- Record the decision with evidence from the pilot.
- Explicitly state whether the manual artifacts affected critique or patch
  decisions. If not, do not approve parser/tooling work yet.
- Commit the decision doc.

**Verification:**

```bash
git status --short
rg "Decision|Evidence|Next implementation" plugins/figure-agent/docs/milestones-archive/2026-05-16-reference-conditioned-authoring-loop-decision.md
rg "manual artifacts affected|parser|tooling" plugins/figure-agent/docs/milestones-archive/2026-05-16-reference-conditioned-authoring-loop-decision.md
git diff --cached --stat
```

## 8. Success criteria

This milestone succeeds only if the pilot produces evidence that the new layer
changes authoring quality, not just documentation volume.

Minimum success:

- The pilot has contract, reference pack, authoring plan, theory guard,
  iteration log, and quality audit.
- At least five sub-region iterations are recorded.
- No theory BLOCKER is left unresolved in an `accepted: true` state.
- No publication-compliance `unknown` or `no` state is left unresolved in an
  `accepted: true` state.
- The human reviewer can explain why each applied patch was made without
  relying on chat history.

Strong success:

- A blind or side-by-side comparison prefers the contract/reference-pack-guided
  version over the previous version.
- The LLM critique produces fewer false-positive style suggestions because it
  reads forbidden transfers and theory invariants.
- The next figure can reuse the same artifact forms with only local content
  changes.

Failure signals:

- The artifacts become boilerplate and do not affect patch decisions.
- The LLM still ignores references or theory guards.
- Most quality decisions remain chat-only.
- A large reference/retrieval layer is proposed before the pilot proves consumer
  uptake.

## 9. Stop rule

Do not generalize this milestone into a full framework until the primary pilot
has completed Tasks 1-5 and produced a concrete decision in Task 6.

The next code change should be the smallest tool that removes a repeated manual
burden observed in the pilot, not the largest architecture that could cover all
future figures.
