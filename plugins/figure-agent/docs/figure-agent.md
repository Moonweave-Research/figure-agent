<!-- FIGURE_AGENT:AUTHORITY -->
# Figure Agent Product Contract and Execution Roadmap
**Status:** Active and authoritative
**Effective date:** 2026-07-18
**Committed baseline:** `c6a28e40` (`codex/figure-agent-closed-loop-reset`)

This is the sole product specification and forward execution authority for Figure
Agent. Other plans, roadmaps, reviews, and generated packets are implementation
references or historical evidence and cannot change product direction. The
baseline is a reproducible starting commit, not a release, quality, or publication
verdict; its clean worktree passed 235 targeted baseline tests. Future claims
require fresh evidence from the slice that makes the claim.

## 1. Outcome
Figure Agent does not compete with an LLM as a second general drawing model. The
LLM remains free to interpret the scientific narrative, propose a composition,
choose an analogy, and author editable TikZ or another declared representation.

Figure Agent complements that capability where an unconstrained LLM is
reliably weak:

- preserving scientific objects, relations, forbidden implications, domain-correct morphology, metric endpoints, visual ratios, curve-to-sample attribution, and process-stage ownership;
- seeing the rendered artifact at whole-figure, panel, object, and zoom scales;
- detecting collisions, clipping, broken or falsely intersecting semantic paths,
  reduction-only illegibility, workflow-metadata leakage, and ownership ambiguity;
- attributing a visible defect to an exact semantic object and editable source;
- repairing one bounded region without silently changing neighboring meaning;
- reproducing the result from declared inputs and tool versions; and
- separating machine evidence from human scientific and publication judgment.

The operating rule is: **Let the LLM propose freely.** Make Figure Agent constrain,
observe, localize, repair, reproduce, and prove.

Figure production is Figure Agent's primary dogfood and learning surface: a hand-tuned fixture exposes an LLM gap, visual contract, or detector need. Promote it only after the declared mechanism transfers across figure families without fixture coordinates or hidden human edits; preserve free LLM redraw rather than imposing a primitive, template, or coordinate recipe.
`docs/figure-design-philosophy.md` is the normative companion for manuscript conventions and recorded human lessons; this contract remains the sole authority for workflow, release, and product direction.
Each slice must produce or inspect one real figure artifact (or a defensible no-artifact diagnosis) and use its render to promote only transferable mechanisms. A component bank stays disabled until one component is reused and visually verified in a second independent figure.

## 2. Product boundaries
### 2.1 Representation roles
- **TikZ/TeX** is the current default editable publication-authoring path.
- **SVG** is a derived export surface; publication exports outline glyphs to preserve PDF text geometry, while editable/searchable text remains the TeX authority.
  Direct-SVG generation is not an active backend-development target.
- A valid `review/current-candidate.json` binds nested-repair export evidence without promotion or acceptance; invalid, incomplete, or stale bindings fail closed.
- **Python** is the control plane for contracts, compilation, observation,
  attribution, repair, provenance, and evaluation, not an illustration language.
- **PDF and PNG** are rendered evidence surfaces, not editable authority.
- Exact chemical structures and quantitative plots should use their domain
  authorities when needed; the general LLM must not imitate them freehand when
  a deterministic renderer or data pipeline owns the truth.

Backend selection is closed until comparative evidence shows a failure the control
plane cannot address. During closed-loop slices, do not add a renderer, Illustrator
clone, whole-page grammar, or fixture-specific coordinates to reusable code.

### 2.2 Knowledge and model boundaries
Read-only authoring context packs compile durable paper-specific knowledge. They
may bind explicit paper-local files, Style Lock tokens, reviewed assets, semantic
objects, relations, protected invariants, and human-declared non-coordinate aesthetic levers.
They are not LLM prompt plumbing, prompt-loop revival,
generation execution, or automatic physics detection.

The plugin may prepare crops and briefs, but host vision review occurs outside it.
Figure Agent accepts only a receipt binding actor, model or tool, request hash,
transcript hash, and inspected artifacts. Detectors, critiques, and scores are not
scientific truth; ambiguity remains visible and routes to the responsible human.

## 3. Closed-loop architecture

The canonical attempt lifecycle is:

```text
scientific task + references + declared invariants
                         |
                         v
              context and authoring packet
                         |
                         v
                 free LLM authoring
                         |
                         v
          deterministic compile and render
                         |
                         v
      machine checks + perception + review crops
                         |
                         v
             fresh host vision critique
                         |
                         v
          adjudicated actionable finding
                         |
                         v
        exact semantic and source attribution
                         |
                         v
       human-authorized bounded repair packet
                         |
                         v
          materialize, compile, and re-render
                         |
                         v
      fresh post-repair visual and regression review
                         |
                         v
        named human development-baseline verdict
```

The first priority is connecting observed critique to attributable bounded repair
and fresh post-repair visual review. Reuse existing detectors, crops, attribution,
repair transactions, and provenance before adding mechanisms.

Zero-feedback authoring is only a controlled benchmark arm, not the normal
workflow. In an A/B/C comparison:

- **A** is raw LLM authoring from the neutral scientific task;
- **B** is the same LLM and task plus Figure Agent's declared contracts; and
- **C** is the hash-bound child of B after exact attribution and bounded repair,
  not a third independent authoring call.

## 4. Evidence contract

Every attempt must hash-bind the task, model, budget, source commit, starting and
generated artifacts, context packet, toolchain, review inputs, and evidence. A line
number is not source identity; use stable selectors and reject missing, duplicate,
or stale anchors. Critique-input manifests bind fixture-relative logical paths
and content hashes, so the same workspace and Style Lock bytes produce the same
freshness result from a source checkout and an installed plugin; an installation
directory is not scientific evidence.

Evidence remains layered:

1. **Machine-valid:** schemas, hashes, compilation, assertions, and checks pass.
2. **Visually re-reviewed:** current render/crops are fresh and regression review is complete.
3. **Human development accepted:** a named reviewer accepts the current development baseline.
4. **Publication accepted:** an external editorial outcome outside Figure Agent's authority.

Panel analysis normally indexes the canonical fixture source. When review has
produced a repaired child that has not been promoted to that root, select it
explicitly with `fig-agent analyze-panel <name> <panel-id> --source
<fixture-relative.tex> --json`. The override is read-only, stays inside the
fixture boundary, and reports the selected source in `inputs.source`; it does
not promote the child or imply any acceptance state.

No lower state implies a higher one. Machine gates and model critiques use
`publication_acceptance: not_claimed`; any external record is evidence, not plugin
authority.

PDF-vector `silhouette_morphology_checks` may guard `filled_boundary` integrity or
measure a `stroked_centerline` member's rendered length, width, displacement,
and direction; optional `silhouette_morphology_groups` compare cross-panel scale
and bend order. `/fig_status`
must expose hash-bound checked/declared member and group coverage. Missing, stale,
incomplete, invalid, unanalyzable, or failing evidence blocks readiness. This is
not an aesthetic score: curvature, label hierarchy, and publication taste still
require fresh reduced-scale review, and thresholds do not transfer without evidence.

### Mechanism semantic-contract rule

`physics_grounding=grounded` only declares physics intent and at least one wired
directional or relational assertion; it is not scientific validity.
`semantic_contract_required: true` additionally requires coordinate-free objects,
visible relations, forbidden readings, and explicit unresolved electrical
topology before strict compile. This transferable meaning guard is not a primitive,
coordinate recipe, style lock, or publication-acceptance claim.

Promotion requires two materially different figure families, prospectively recorded correction time, named human outcomes, no semantic/relation regression, and reproducible evidence.
Reports require passing `correction_time_gate` and `lineage_gate`: A/B share task/model/budget/start; C is B's hash-bound repair child, not an independent generation.
Rejected and neutral attempts remain failure evidence.

Figure Agent learning is currently evidence-backed rule and contract promotion, not model-weight training; promotion requires prospective evidence from at least two materially different figure families. A single-fixture log is `blocked_single_fixture`, and cross-fixture review plus existing human/semantic gates remain required. Direct LLM or human TikZ edits are not invisible learning events: after a fresh strict compile, record them with `fig-agent record-manual-edit <fixture>`. The command binds the source hash to strict status, semantic assertions, and 100%/50%/33% render previews before appending the receipt. Compile success supplies provenance only; it never becomes a positive reward. A reward is created solely by an explicit `--decision accept|reject --reviewer <name>`, so unreviewed direct edits remain available for audit without teaching the ranker that they improved quality.

## 5. Executable roadmap

Execute one slice at a time with the smallest failing test first. Keep it
reviewable; open the next slice only after recording stop conditions and evidence.

### R0 — Establish the authority baseline

- [x] Start from committed baseline `c6a28e40` in a clean worktree.
- [x] Collapse product specification and execution direction into this file.
- [x] Preserve previous authorities in place as legacy evidence.
- [x] Run authority, package, and entrypoint contract tests after consolidation.

**Exit:** exactly one active authority marker exists; every entrypoint routes here.

### R1 — Specify the closed-loop attempt state

- [x] Add failing-first tests for adjudicated repair binding and hash-bound
  post-repair visual-review evidence.
- [x] Define attempt identity, lineage, freshness, actor boundary, and terminal
  fields without a new renderer or workflow shell.
- [x] Reject stale adjudication, ambiguous attribution, and missing repair
  evidence at the supported critique-to-target bridge.
- [x] Express and prove the complete lifecycle, including unadjudicated and
  unbound starts, through one shared attempt-state contract.

**Exit:** tests cover authored render through re-review and each fail-closed boundary.

### R2 — Connect critique to bounded repair

- [x] Convert one adjudicated visual finding into declared semantic object and
  relation references.
- [x] Bind one machine-backed finding to exact source attribution, one editable
  selector, and declared protected invariants.
- [x] Carry it through repair packet, materialization, finalization, rollback, and
  bounded edit-budget surfaces as one transaction.
- [x] Keep ambiguous or evidence-missing bridge inputs as fail-closed stops.
- [x] Route unbound semantic or relation findings to an explicit human handoff.

**Exit:** one reviewed finding produces safe repair without hidden source selection.

### R3 — Require fresh post-repair vision and regression evidence

- [x] Bind verified repaired-source/render hashes and full, target, neighboring,
  and print-scale artifacts in the post-repair review request.
- [x] Reject drift, missing inspection roles, unresolved targets, and present or
  uncertain regression.
- [x] Require a hash-valid external host-review execution receipt before a
  non-uncertain response can advance to visual re-review pending human judgment.
- [x] Wire fresh crops and a request-bound host handoff into the canonical run
  without performing or impersonating the external host review.
- [x] Consume a receipt-bound external host response through the same run.
- [x] Controlled-fault replay on maintained Fig3 source proves current v4 rejects
  a target fix that creates a declared neighboring collision.
- [x] Preserve hash-bound before/after evidence; execute identity-safe, crash-recoverable rollback with explicit legacy opt-in.
- [ ] Repeat on a prospective real defect; controlled fault is not acceptance.

**Exit:** `machine_repaired` needs fresh evidence to become `visually_re_reviewed`.

### R4 — Make the lifecycle the canonical run path

- [ ] Route the existing canonical run through R1-R3 state transitions.
- [x] Project the unique hash-validated current attempt into `status`, `drive`,
  and default `run`; fail closed on invalid, ambiguous, stale, or symlinked
  lineage instead of falling through to a legacy loop.
- [x] Wire `machine_repaired -> post_review_requested` through default `run`:
  plan-only writes nothing; execute creates the bound request/crops/state and
  stops before host invocation.
- [x] Consume an explicitly supplied post-review response against the canonical
  projected `post_review_requested` path and hash, then revalidate the canonical
  current leaf under the publication lock; do not discover responses or invoke
  the host automatically.
- [x] Consume an explicitly supplied, hash-bound repair response only from the
  canonical `repair_authorized` state. Reuse materialize/finalize/rollback: strict
  success publishes `machine_repaired`; strict failure rolls back and publishes
  `repair_required`. Never discover a response, invoke a host, accept legacy
  packets implicitly, or claim publication acceptance.
- [x] Consume explicit hash-bound human authorization only from canonical `repair_candidate_ready`; publish the named reviewer without inventing approval.
- [x] Consume an explicit v4 packet, response, and recomputed dry-run preview only
  from `repair_bound`; validate binding authority and stop for named authorization.
- [x] Bind one explicit named human verdict to canonical `visually_re_reviewed`; publish only development acceptance, rejection, or a new-repair requirement, never release or publication acceptance.
- [x] Compatibility bypass guard: `e2e-smoke` leases/resolves each repeat through status; `loop` is scratch-only verify-only; `improve` rejects aggressive search. No prospective-proof or publication-acceptance claim.
- [x] Stop at host-vision, scientific, human authorization, accepted/golden,
  release, and publication boundaries.
- [x] The initial compatibility registry covers only `loop`, `improve`, and `e2e-smoke`; its schema is `figure-agent.compatibility-command-contract-registry.v1`, `write_authority` records the maximum tested mutation boundary, not permission, release, acceptance, or publication authority, and publication acceptance remains unclaimed.
- [x] Preserve exact actor, evidence references, allowed/forbidden scope, and
  `publication_acceptance` through queue and plan-only queue-run projections;
  aggressive candidate search may not cross a human boundary.
- [x] Preserve additive, content-hashed per-step execution artifacts for
  compile, adjudication scaffold, export, and fig-loop runs without changing
  the selected action, command return code, or final stop reason.
- [ ] Give every remaining specialist/internal adapter an explicit canonical
  successor and evidence contract before compacting the surface.
- [ ] Expose a compact default command surface only after compatibility tests
  prove no evidence path is lost.

**Exit:** status drives safe deterministic work to one truthful next actor/action.

### R5 — Cross-family proof and capability promotion
- [x] Require ordered `% Panel <id>` markers; exact-bind only unique rendered literals and leave repeated text ambiguous.
- [x] R5.1–R5.2: exercised hash-bound attribution, bounded repair, rollback-safe materialization, and fresh neighboring/full/print review on the Fig1 failure-first lineage; dated measurements and named outcomes remain in `docs/evidence/r4-r5-implementation-history.md`.
- [x] R5.3: canonical status now hash-binds declared text-boundary and label-path coverage to the current spec/render, exposes declared versus checked counts, and fails readiness closed on missing, stale, invalid, zero, incomplete, or failing evidence without introducing a panel-count grammar.
- [ ] R5.4: deepen A, B, or E semantics from paper authority and prove one prospective real defect.
- [ ] R5.5: transfer the mechanism to maintained Fig3 without Fig1-private imports.
- [ ] Record correction minutes, named human verdicts, defect reduction, new-defect rate, semantic preservation, and reproducibility.
- [ ] Promote only after two materially different figure families show lower correction burden without semantic/relation regression; machine-green and development acceptance never imply publication acceptance.
Fig1 repair evidence and current fixture bindings remain in the linked evidence and `docs/paper_figure_map.yaml`; this authority makes no publication claim.
**Exit:** two families show lower correction burden without reducing open LLM authoring, plus the required named human scaffold/review verdict; otherwise keep the mechanism experimental or retire it.

## 6. Mandatory stop conditions

The workflow must stop and report the required actor when any of these holds:

- the render, crop manifest, critique, adjudication, selector, or parent hash is
  missing or stale;
- attribution is ambiguous, unbound, or resolves to more than one editable
  target;
- protected scientific invariants or the repair budget are incomplete;
- the proposed edit crosses its declared semantic or source boundary;
- compile, semantic, collision, neighboring-region, or visual regression checks
  fail after repair;
- the repair makes another confirmed defect worse or introduces a new one;
- the decision requires scientific interpretation, aesthetic preference,
  accepted/golden promotion, release authority, or publication judgment; or
- the next change would add a renderer, broad grammar, dependency, public API,
  or materially larger product surface without new comparative evidence.

Do not work around a stop by weakening a gate, relabeling a third generation as
repair, estimating retrospective correction time, or claiming that machine
success is publication acceptance.

## 7. Current implementation boundary

Reuse the established compile/export, perception, critique, attribution, repair,
materialization, provenance, and human-review surfaces. The R1-R3 foundation and
several R4 transitions are not a completed autonomous loop. Status and run bind
one hash-identified attempt, fail closed on ambiguity or staleness, and stop at
external host or human boundaries; stale detector evidence is a reported stop,
not an uncaught exception or candidate source.

Repairs require exact attribution, a bound packet and preview, named authorization,
strict materialization or rollback, and fresh post-repair review. Runner and queue
actions revalidate their lease and live plan; evidence uses content hashes, never
follows symlinks, and cannot turn failure into success. Promotion remains human-
gated, and unsupported edit families fail loudly.

Dated R4/R5 chronology, schema inventory, and Fig1 measurements live only in
`docs/evidence/r4-r5-implementation-history.md` and its named validators/tests.
They are non-authoritative and cannot claim visual, release, or publication acceptance.
