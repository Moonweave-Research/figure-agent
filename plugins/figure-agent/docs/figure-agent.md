<!-- FIGURE_AGENT:AUTHORITY -->
# Figure Agent Product Contract and Execution Roadmap

**Status:** Active and authoritative

**Effective date:** 2026-07-16

**Committed baseline:** `c6a28e40` (`codex/figure-agent-closed-loop-reset`)

This is the sole product specification and forward execution authority for Figure Agent. Other specifications, plans, roadmaps, milestone notes, fixture reviews,
and generated packets are implementation references or historical evidence. They
cannot change product direction or the next implementation step.

The baseline names a reproducible starting commit, not a release, quality, or
publication verdict. A clean worktree at this commit passed 235 targeted baseline
tests. Future claims require fresh evidence from the slice that makes the claim.

## 1. Outcome

Figure Agent does not compete with an LLM as a second general drawing model. The
LLM remains free to interpret the scientific narrative, propose a composition,
choose an analogy, and author editable TikZ or another declared representation.

Figure Agent complements that capability where an unconstrained LLM is
reliably weak:

- preserving scientific objects, relations, and forbidden implications;
- seeing the rendered artifact at whole-figure, panel, object, and zoom scales;
- detecting collisions, clipping, broken paths, weak hierarchy, and ownership
  ambiguity;
- attributing a visible defect to an exact semantic object and editable source;
- repairing one bounded region without silently changing neighboring meaning;
- reproducing the result from declared inputs and tool versions; and
- separating machine evidence from human scientific and publication judgment.

The operating rule is: **Let the LLM propose freely.** Make Figure Agent constrain,
observe, localize, repair, reproduce, and prove.

Figure production is not Figure Agent product development. A hand-tuned fixture
becomes a product capability only when the same declared mechanism transfers
across different figure families without fixture coordinates or hidden human edits.

## 2. Product boundaries

### 2.1 Representation roles

- **TikZ/TeX** is the current default editable publication-authoring path.
- **SVG** is a derived export, inspection, interchange, or bounded fragment surface.
  Direct-SVG generation is not an active backend-development target.
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
objects, relations, and protected invariants. They are not LLM prompt plumbing,
prompt-loop revival, generation execution, or automatic physics detection.

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
or stale anchors.

Evidence remains layered:

1. **Machine-valid:** schemas, hashes, compilation, declared assertions, and
   deterministic checks pass.
2. **Visually re-reviewed:** the current render and review crops are fresh, and
   post-repair regression review is complete.
3. **Human development accepted:** a named reviewer accepts the current
   artifact as a development baseline.
4. **Publication accepted:** an external editorial outcome outside Figure
   Agent's authority.

No lower state implies a higher one. Machine gates and model critiques use
`publication_acceptance: not_claimed`; any external record is evidence, not plugin
authority.

Promotion requires two materially different figure families, prospectively recorded correction time,
named human outcomes, no semantic or relation regression,
and reproducible evidence. Rejected and neutral attempts remain failure evidence.

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
- [ ] Next: give each remaining specialist/internal adapter a per-command canonical successor and evidence registry/contract.
- [x] Preserve exact actor, evidence references, allowed/forbidden scope, and
  `publication_acceptance` through queue and plan-only queue-run projections;
  aggressive candidate search may not cross a human boundary.
- [ ] Give every remaining specialist/internal adapter an explicit canonical
  successor and evidence contract before compacting the surface.
- [ ] Expose a compact default command surface only after compatibility tests
  prove no evidence path is lost.

**Exit:** status drives safe deterministic work to one truthful next actor/action.

### R5 — Cross-family proof and capability promotion

- [ ] Replay the closed loop on the maintained complex Fig1 and Fig3 families.
- [ ] Use the same model/task/budget rules for A and B; derive C only from B.
- [ ] Record prospective human correction minutes and blinded named verdicts.
- [ ] Measure defect reduction, new-defect rate, semantic preservation,
  reproducibility, and transfer without fixture-specific imports.
- [ ] Promote only the narrow mechanisms supported by both families.

**Exit:** evidence shows lower correction burden without reducing open-ended LLM
authoring; otherwise retain the mechanism as experimental or retire it.

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
materialization, provenance, and human-review surfaces.

The code is an R1-R3 foundation with several R4 canonical transitions, not a
completed loop. Its attempt state binds identity, append-only lineage, freshness,
evidence roles, actors, legal transitions, and terminal development outcomes.
Default status/run finds one current attempt without mtime, projects exact
actor/path/hash, and stops instead of selecting a legacy loop. Evidence-role
presence is not domain validation or actor authentication; adapters validate each
receipt against recorded identity.

One adjudicated binding crosses packet compilation, authorized materialization,
rollback, and finalization. New packets use v4 authority; stored v3 packets need
explicit compatibility and cannot enter post-repair review. Finalization and
rollback revalidate v4 authority and hash-bound failure evidence under recovery.

The binding now hash-binds declared semantic object and relation references to
the same editable selector as the repair target. Missing semantic authority,
ambiguous attribution, or missing references can emit only a named
`human_attributor` handoff; they cannot create a repair binding or packet.

Default `run` consumes an explicit bound packet/response/preview at `repair_bound`, human authorization at `repair_candidate_ready`, the same response again at `repair_authorized`, and one state-bound named human verdict at `visually_re_reviewed`. That verdict can accept the development baseline, reject the artifact, or require a separately authorized repair attempt. Materialize/strict-finalize/rollback publishes
`machine_repaired` or `repair_required`; completed receipts recover state publication. `repair_failure_record` is a schema-heterogeneous reason-for-repair role, so consumers must validate its referenced schema and decision rather than assume a machine failure.
Pre-R4.8 candidate-ready v1 states without response evidence fail closed and cannot restart in place; a named human must authorize the exact leaf path/state/file hashes, then explicitly run `python3 scripts/closed_loop_legacy_candidate_quarantine.py --fixture <name> --state <leaf.json> --authorization <record.json> --execute` to preserve the retired leaf and authorization outside canonical discovery before restarting its verified `repair_bound` parent. They are never auto-migrated or discarded.
Canonical state publishers share one recoverable transition lock and temporarily dual-lock legacy paths. Root `run` admission accepts only one explicit hash-bound `figure-agent.root-attempt-manifest.v1` while current resolution is absent; plan-only is write-free and execute publishes only `authored_rendered` before stopping. It discovers no other input, invokes no host, admits no legacy packet, and claims no publication acceptance. It advances `machine_repaired` to `post_review_requested`,
stops at `host_llm`, binds the response, and closes only the named development outcome. Maintained-Fig3 controlled-fault replay is mechanism evidence,
not an actual defect or publication verdict; prospective proof and R4-R5 remain.
Direct legacy `fig_loop` shares a recoverable fixture-root admission lease with root admission: it holds that lease from canonical resolution through scratch evidence writing, and rejects current, invalid, ambiguous, or busy resolution before creating `.scratch/fig-loop-runs/` output.

Closed-loop handoffs use these contracts rather than another workflow shell:
`figure-agent.repair-materialization-preview.v1`, `figure-agent.repair-materialization-receipt.v2`,
`figure-agent.repair-execution-packet.v4`, `figure-agent.repair-authority-contract.v1`,
`figure-agent.closed-loop-attempt-state.v1`, `figure-agent.closed-loop-current-state.v1`, `figure-agent.legacy-candidate-quarantine-authorization.v1`,
`figure-agent.adjudicated-repair-binding.v1`, `figure-agent.semantic-finding-attribution.v1`,
`figure-agent.attribution-handoff.v1`, `figure-agent.post-repair-visual-review-request.v1`,
`figure-agent.host-review-execution-receipt.v1`, `figure-agent.post-repair-visual-review-response.v1`,
`figure-agent.post-repair-visual-review-receipt.v1`, and `figure-agent.closed-loop-development-verdict.v1`.
