# Figure Agent Architecture Overview

**Document status:** Active operational reference. This is not product or
execution authority and is not independently agent-executable. Read the sole
authority, [`docs/figure-agent.md`](figure-agent.md), before changing product
behavior. Document classification is declared in `docs/document-status.yaml`.

## Identity and boundary

Figure Agent is a paper-figure quality kernel. A human, LLM, domain renderer,
or other declared tool may author the source. Figure Agent binds intent and
evidence, renders editable source, checks reproducibility and visible failure
modes, routes bounded work, and stops at scientific, aesthetic, human,
release, and publication decisions.

The current editable schematic path is TikZ/TeX. Python is the control plane,
not an illustration language. SVG is a derived export, inspection, or bounded
interchange surface; the built-in SVG-polish engine is retired. PDF and PNG
are evidence surfaces. No machine-green state implies publication acceptance.

Reference extraction follows this contract:

```text
reference PNG -> OCR + palette clusters + optional vtracer structural hints
coordinate_hints.yaml -> semantic TikZ authoring
```

SVG-to-TikZ path conversion is not the active workflow. Structural hints are
optional authoring evidence and never become scientific or source authority.

## Layer model

```text
Layer 0: Scientific and project inputs
  briefing.md, spec.yaml, references, data/domain authority
                             |
Layer 1: Read-only authoring context
  Style Lock + declared semantic objects/relations/invariants
                             |
Layer 2: Editable source
  free human/LLM TikZ authoring; domain-owned plots/chemistry where required
                             |
Layer 3: Deterministic build
  lint -> LuaLaTeX -> PDF/PNG -> semantic and geometry checks
                             |
Layer 4: Rendered review evidence
  full figure + panel/target/neighbor/seam/print-scale crops
                             |
Layer 4.5: External host vision review
  hash-bound request/receipt/response; no in-plugin model invocation
                             |
Layer 5: Adjudication and exact attribution
  critique_adjudication.yaml + semantic object/relation + source selector
                             |
Layer 5.5: Final Artifact
  external final-artifact handoff; no hidden SVG editor
                             |
Layer 6: Authorized bounded repair
  preview -> named authorization -> materialize -> strict revalidation/rollback
                             |
Layer 7: Fresh post-repair review and human development verdict
  never release/publication acceptance by implication
                             |
Layer 8: Status, driver, queue, and package evidence
  one truthful next actor/action; deterministic work only across safe boundaries
```

Composition exploration is a bounded research surface below the default route.
Its declared families live in `scripts/composition_families.py`; it cannot
silently promote a composition, mutate an accepted/golden artifact, or replace
the canonical evidence lifecycle.

## Canonical runtime surfaces

The public shell entrypoint is `fig-agent`; slash-command documents adapt it
for supported hosts. Runtime roots are explicit:

- `FIGURE_AGENT_PLUGIN_ROOT` or `CLAUDE_PLUGIN_ROOT` locates installed code.
- `FIGURE_AGENT_WORKSPACE` or `CLAUDE_PROJECT_DIR` locates user fixtures.

The runtime entry route is `/fig_status` followed by `/fig_run`. The supported
documented workflow around that entrypoint is:

1. `/fig_new` creates a fixture contract.
2. `/fig_status` is the canonical first read.
3. `/fig_compile` creates deterministic render and check evidence.
4. `/fig_critique` prepares and records external host review evidence.
5. `/fig_adjudicate` records human disposition in
   `critique_adjudication.yaml`.
6. verify-only `/fig_loop` records a bounded checkpoint; `/fig_drive` and
   `/fig_run` choose or execute only the currently allowed deterministic step.
7. `/fig_export` writes declared derived formats.
8. `/fig_closeout` reports remaining machine and human gates.

Compatibility commands remain callable only where their evidence contract is
tested. They are not separate product authorities or permission to revive
retired quality search, prompt orchestration, or SVG-polish machinery.

## Agent context loading

The shipped skill uses progressive disclosure so mechanical operations do not
pay the context cost of the full visual-review contract:

```text
skill metadata
  -> skills/figure-agent/SKILL.md (routing and workflow, always when triggered)
  -> references/vision-critique-rubric.md (visual interpretation only)
  -> context-pack-selected project/paper rule catalogs (fixture work only)
```

Authoring, visual critique, rendered-defect adjudication, and final render
inspection load the vision rubric completely. Status, compile, export,
packaging, and other mechanical-only work stop at the entry skill unless visual
interpretation is also part of the task. The reference remains subordinate to
this architecture and to the sole product authority; it does not introduce a
second workflow or bypass context-pack source selection.

## Source and evidence ownership

One fixture lives under `examples/<name>/`. Its editable authority and evidence
roles are distinct:

- `briefing.md`: scientific intent and declared unknowns;
- `spec.yaml`: fixture and gate configuration;
- `<name>.tex`: canonical editable source, unless a current-candidate pointer
  explicitly selects a contained repaired child;
- `semantic_regions.yaml` and semantic contracts: stable object/relation and
  source-attribution declarations;
- `build/`: generated compile, render, detector, perception, and receipt data;
- `critique.md` and adjudication: review evidence, not scientific truth;
- `exports/`: derived delivery artifacts;
- acceptance records: explicit human or release decisions only.

The current candidate and canonical root must never be silently conflated.
Status reports the selected source and freshness. Symlinks, path escape,
ambiguous lineage, stale hashes, or multiple current leaves fail closed.

## Compile and validation

`scripts/compile.sh` orchestrates the build. Important checks include:

- `scripts/checks/check_collisions.py`
- `scripts/checks/check_visual_clash.py`
- `scripts/checks/check_text_boundary_clash.py`
- `scripts/checks/check_label_path_proximity.py`
- `scripts/checks/check_physics_grounding.py`
- `scripts/checks/check_golden_artifacts.py`

Strict mode promotes declared blocking findings without weakening detector
thresholds. A check with no declared coverage is not equivalent to a checked,
clean surface. Mechanism figures should declare semantic and physics intent;
labels and paths with known collision risk should declare deterministic checks.

The perception pack is descriptive only. It helps a host inspect the render but
does not infer topology, aesthetics, or physics. Host critique is likewise
review evidence: unresolved or conflicting findings route to a human gate.

## Repair and state lifecycle

The canonical repair path is lineage- and hash-bound:

```text
authored render
  -> initial review requested
  -> reviewed/adjudicated finding
  -> exact semantic and source attribution
  -> repair packet and dry-run preview
  -> named human authorization
  -> materialize and strict re-render
  -> fresh target/neighbor/full/print review
  -> named development verdict
```

Every transition validates the expected fixture, source, current state, actor,
and evidence hashes. Recovery preserves prior evidence. A failed repair rolls
back or publishes a repair-required state; it does not overwrite the canonical
source or advance by best effort.

`/fig_run --execute` may perform only allowlisted deterministic work. It stops
before external host review, scientific interpretation, source-patch choice,
human authorization, accepted/golden mutation, release, and publication. Queue
execution delegates to the same live validation instead of replaying a stale
plan.

## Documentation and package governance

`docs/document-status.yaml` assigns every governed document one class:

- `authority`: sole active product/execution contract; ships and can instruct;
- `reference`: current operational explanation; ships but cannot set direction;
- `project_state`: current paper-local state; executable only in its project and
  never shipped in the generic Cowork bundle;
- `evidence`: decision, experiment, or run record; preserved but not executable;
- `historical`: superseded proposal/specification; preserved but not executable.

Unclassified documents fail closed: they neither ship nor instruct an agent.
The Cowork package includes only documents whose policy has `ship: true` and
rejects personal absolute paths. Paper-local handoffs, drafts, trials, plans,
issues, and historical architecture records stay out of the generic package.

## Change map

| Change | Canonical place |
|---|---|
| Product direction or roadmap | `docs/figure-agent.md` |
| Operational architecture explanation | this file |
| Document status/ship semantics | `docs/document-status.yaml` |
| Public command contract | `commands/fig_*.md` and `bin/fig-agent` |
| Agent routing and visual-review context | `skills/figure-agent/SKILL.md` and `skills/figure-agent/references/vision-critique-rubric.md` |
| Build/check behavior | `scripts/compile.sh`, `scripts/checks/` |
| Figure-specific intent | `examples/<name>/briefing.md`, `spec.yaml` |
| Paper-local current state | declared `project_state` documents |
| Historical proposal or experiment | declared `evidence`/`historical` documents |

Do not turn a successful fixture edit into a reusable product primitive without
cross-family evidence. Do not weaken a gate to make a candidate green. Do not
claim that compilation, strict checks, model critique, or development acceptance
establishes publication acceptance.
