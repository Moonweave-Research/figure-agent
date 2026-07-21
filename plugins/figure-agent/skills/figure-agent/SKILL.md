---
name: figure-agent
description: Use for paper-figure quality, compile, export, and reproducibility gates around scientific schematics. A human or any LLM/tool may author the figure; figure-agent enforces Style Lock, compiles/exports, runs visual QA checks, and reports stale or unreplayable figure state. Deleted v0.1 prompt/image-gen commands are historical only. Symbolic schematic axes are inside scope; quantitative data plots and measured datasets belong in matplotlib / Graph_making_hub.
---

# figure-agent SKILL

## Plugin Identity

**Scope: schematic quality kernel.** Mechanism diagrams, band structures,
conceptual flows, potential wells, comparison schematics, isometric device
stacks — qualitative figures whose value comes from clarity of concept rather
than precision of numerical data. **Data plots are out of scope** (see
Boundaries below).

Durable responsibilities:

1. **Style Lock** — keep palette, fonts, macro usage, and figure-wide style
   consistent across a manuscript.
2. **Compile/export reliability** — produce PDF/SVG/TIFF/PNG artifacts from
   editable source without stale-output ambiguity.
3. **Visual QA** — run collision and render-based clash checks before manuscript
   use.
4. **Reproducibility** — keep per-figure folders, source, briefing, status, and
   exports auditable months later.

Prompt/image-gen orchestration from v0.1 is historical only in this plugin line.
Do not route users to deleted commands.
Read-only authoring context packs are durable paper-specific knowledge
compilation in scope when they compile explicit paper-local files, Style Lock
tokens, source-anchored rule catalogs, and opt-in semantic claims/invariants.
They are not prompt-loop revival, generation execution, or automatic physics
detection.
Keep superseded rules in catalog provenance, but exclude them from authoring
context so stale hypotheses cannot compete with later human-confirmed rules.
Before product-level work, read `docs/figure-agent.md`. It is the sole active
product specification and forward execution roadmap. Treat other specs, plans,
roadmaps, and milestones as scoped evidence unless that authority explicitly
delegates to them.

## Dogfood routing boundary

For **Figure Agent dogfood** or product-development work, this skill and the
repo-local Figure Agent commands take priority over generic TikZ refinement.
Do not automatically invoke `tikz`, `tikz-refine`, or another external drawing
skill merely because the editable representation is TeX/TikZ. A specialist is
an explicit user-selected tool, not an implicit dependency of Figure Agent.

Keep the authoring model free to redraw or replace constructions. Review the
rendered meaning, attribute a real defect, and constrain the repair boundary;
do not force a reusable primitive or specialist coordinate recipe. If whole,
panel, and print-reduction review finds **no defensible defect**, preserve the
source unchanged and record the review basin. Compile-generated and ignored
build artifacts are verification evidence, not product edits; do not delete,
stage, or count them as the source change required to make a review succeed.

## Runtime Entrypoint

Use `fig-agent ...` for shell commands. If `fig-agent` is not on `PATH`, use
`"${CLAUDE_PLUGIN_ROOT}/bin/fig-agent" ...`.

The installed plugin bundle and user figure workspace are separate. Bundled
tools/styles come from `FIGURE_AGENT_PLUGIN_ROOT` or `CLAUDE_PLUGIN_ROOT`;
figure fixtures come from `FIGURE_AGENT_WORKSPACE` or `CLAUDE_PROJECT_DIR`.

## Workflow shape

`/fig_new` is the shared entry point that scaffolds per-figure folders via
a conversational interview. After scaffolding, author semantic TikZ from the
briefing, optional reference image, and optional coordinate hints.

For reference-conditioned authoring pilots, read
`examples/<name>/authoring_contract.md` and
`examples/<name>/reference/reference_pack.md` before editing TikZ. Write or
refresh `examples/<name>/authoring_plan.md` first, naming the panel/sub-region
patch order, theory-critical decisions, and human checkpoints. The first TikZ
patch must trace back to the plan rather than to chat-only intent.

### Driver rule for agents

Unless the user explicitly asks for a specific low-level command, start every
figure workflow by running `/fig_status <name>` and follow its `Next:` hint.
Do not choose between compile, critique, export, loop, polish, or release from
memory. `/fig_status` is the traffic controller.

Canonical next-action order:

1. If `render_state` is `MISSING` or `STALE`, run `/fig_compile <name>` first.
   Do not request host vision critique against a stale render.
2. If render is `FRESH` and `critique_state` is `MISSING`, `STALE`, or
   `REFERENCE_MISSING`, close that critique/reference gate next.
3. If critique is `FRESH` and `critique_adjudication.yaml` is missing, stale,
   or invalid, run `/fig_adjudicate <name>` or repair the adjudication file.
4. Run `/fig_loop <name> --goal "<goal>"` only after status prerequisites are
   closed enough to record a meaningful verify-only checkpoint.
5. Run `/fig_export`, release, or SVG polish only when `/fig_status` or
   `/fig_drive --dry-run` explicitly routes there.
6. For final submission or "am I done?" checks, use
   `/fig_drive <name> --mode final --goal "final readiness" --dry-run`. This is
   the non-mutating final-readiness preset: it explains the required actor,
   surfaces the strict compile final check, requires a current verify-only
   `/fig_loop` checkpoint before `complete`, and preserves human
   accepted/golden/publication boundaries.

If the user asks to proceed autonomously on one fixture, use
`/fig_run <name> --mode <mode> --goal "<goal>" --execute` rather than manually
copy-pasting each safe driver command. `/fig_run` is bounded: it executes
compile, missing adjudication scaffold, verify-only loop checkpoint commands,
and non-golden draft export, then stops at host critique, existing adjudication
repair, patch, polish, human, accepted, tracked-golden, force-golden, and
release boundaries. It records non-authoritative `.scratch/fig-run-runs/`
evidence in execute mode. There is no resume command; after any interruption,
run `fig-agent helper fig_run_journal.py <name>` to summarize the prior
stop, then rerun live `/fig_status` or `/fig_drive` before using
`/fig_run --execute` again. Do not replay commands from a journal.

For the first canonical lifecycle state after a fresh real render, require one
explicit `--closed-loop-attempt-manifest <manifest.json>` on `/fig_run`; never
discover it adjacently. The manifest must bind fixture, named authoring-agent
identity/role, source/render paths and hashes, task/model/budget provenance, and
`publication_acceptance: not_claimed`. Plan-only validates and reports the
proposed `authored_rendered` path without writing. Execute revalidates under the
shared transition lock, publishes only that root state, and stops. This is
lifecycle admission, not prospective defect proof, visual acceptance, or
publication acceptance; do not synthesize any critique, review, repair,
authorization, verdict, accepted, or golden evidence in this step.

When canonical status is `repair_bound`, pass all of
`--closed-loop-repair-packet <v4.json>` and
`--closed-loop-candidate-response <response.json>` and
`--closed-loop-materialization-preview <preview.json>` to `/fig_run`. The run
recomputes the preview from this explicit triplet, validates it against the
state binding, and only publishes
`repair_candidate_ready`; it does not discover candidate files, invoke a model,
materialize source, or cross the named-human authorization boundary.
Retired pre-R4.8 candidate leaves cannot restart in place. Use
`fig-agent helper closed_loop_legacy_candidate_quarantine.py --fixture <name> --state <leaf.json> --authorization <record.json> --execute`
only as an explicit preservation step; it moves no evidence until `--execute`,
requires a named-human record bound to the exact leaf path/state/file hashes,
preserves both outside discovery, and re-exposes only its verified `repair_bound`
parent.

If the user asks to "use figure-agent to improve this", "loop 10 times", or
"keep reviewing and polishing until no major issues remain" for one fixture,
use `/fig_status` and then rerun the canonical bounded `/fig_run` after each
host, human, or repair boundary. `/fig_improve` remains a compatibility wrapper
over `/fig_run`; it is not a separate default workflow and does not reactivate
autonomous quality search.

If the user asks to proceed autonomously across multiple fixtures, start with
the queue:

1. `fig-agent queue --mode review --goal "<goal>"`
2. `fig-agent queue --mode review --goal "<goal>" --actor host_llm`
3. `fig-agent queue --mode review --goal "<goal>" --actor workflow_agent --command-plan --json`
4. `fig-agent queue-run --mode review --goal "<goal>" --actor workflow_agent`
5. Add `--execute` only after reading the plan-only queue-run output.

`/fig_queue_run` never executes queue commands directly. It delegates each
planned fixture to `/fig_run`, so live driver revalidation remains the execution
gate. Human, release/golden, host-vision, and SVG-polish rows stay explicit
boundaries. For blocked command-plan rows, read `operator_handoff` for the
required actor, next step, allowed scope, forbidden scope, and closeout checks.

Use modes mentally:

- `authoring`: source edits and `/fig_compile`; rerun `/fig_status <name>`
  between compiles to confirm `render_state: FRESH` before promoting work.
  Forbidden: export, critique, adjudication, accepted/golden mutation, SVG
  polish.
- `review`: close compile, critique, adjudication, and `/fig_loop` evidence,
  one patch target at a time. Forbidden: hidden source editing, automatic host
  critique authoring, final SVG polish, accepted/golden mutation.
- `release`: check accepted/golden/final artifact readiness. Forbidden:
  changing `accepted`, forcing golden overwrite, creating polished SVG, hiding
  unresolved findings.
- `polish`: start only after generated export is current and the remaining
  work is visual-only SVG finalization. Forbidden: editing generated
  `exports/`, treating polish as source repair, setting `accepted: true`,
  bypassing semantic backport.
- `final`: non-mutating final-readiness check. It reuses release gates, shows
  strict compile as the final render check, and emits one plain operator
  instruction. Forbidden: forcing golden, setting accepted state, editing
  source/SVG, or mutating publication evidence.

`/fig_loop` is a verify-only checkpoint. It records state and patch handoff
evidence; it does not compile, export, critique, patch, polish, accept, or
commit. Stop for host LLM critique, missing reference inputs, ambiguous patch
selection, human gates, accepted/golden promotion, `--force-golden`, semantic
polish backport, or actions the current mode forbids.

### Active (quality kernel)

```
/fig_new <name>          scaffold (briefing + spec)
                         [user saves reference PNG and records it as
                          spec.yaml.reference_image when target matching matters]
                         [for multi-panel target matching, user may save panel
                          reference PNGs under reference/ and record
                          panels[].reference_image plus panels[].bbox_pdf_cm;
                          run `fig-agent helper spec_bbox_helper.py` to compute bboxes]
/fig_extract <name>      reference PNG -> OCR + palette clusters + optional vtracer structural hints
                         -> coordinate_hints.yaml
                         [human/LLM authors semantic TikZ from briefing intent,
                          reference PNG, and coordinate_hints.yaml;
                          SVG-to-TikZ path conversion is not the active workflow]
                         [reference-conditioned pilots: contract/reference pack
                          -> authoring_plan.md -> scoped TikZ patch]
/fig_compile <name>      Style Lock + PDF/PNG build + collision/clash + drift check
                         + perception data pack (extract.yaml + overlay.png)
                         (FIGURE_AGENT_STRICT=1 promotes findings to hard fail)
/fig_critique <name>     required before export when usable reference grounding exists
/fig_ground <name>       author tex/semantic assertions from briefing §6/§7 so a
                         reversed force/bend direction is fail-loud (Layer 2)
/fig_adjudicate <name>   scaffold critique_adjudication.yaml from critique.md
                         after `fig-agent helper critique_lint.py <name>`;
                         unresolved findings default to needs_human
/fig_loop <name> --goal "<goal>"
                         verify-only loop evidence record under .scratch/fig-loop-runs/
/fig_closeout <name>    read-only post-patch checklist for compile, critique,
                         adjudication, export, and loop rerun freshness
/fig_context_pack <name>
                         read-only authoring context pack for explicit
                         briefing/spec/design/style/rule/semantic contracts
/fig_export <name>       PDF / SVG (dvisvgm preserves text) / TIFF / PNG
/fig_e2e_smoke <name>    deterministic compile/export/status/loop smoke harness
/fig_status [<name>]     stage + render/critique/export/acceptance/final_ready state inference
/fig_drive <name> --mode <mode> --goal "<goal>" --dry-run
                         read-only next-action selector
/fig_run <name> --mode <mode> --goal "<goal>" --execute
                         bounded executor for safe mechanical steps; stops at gates
                         and writes non-authoritative .scratch/fig-run-runs/
                         evidence; no resume/replay command exists
/fig_improve <name> --goal "<goal>" --execute --max-loops N
                         compatibility wrapper over /fig_run; not the default route
/fig_queue --mode <mode> --goal "<goal>"
                         read-only multi-fixture driver queue with actor/action
                         filters and optional command plan
/fig_queue_run --mode <mode> --goal "<goal>"
                         plan or execute the queue's workflow-agent subset by
                         delegating each fixture to /fig_run
```

Agent rule: when `coordinate_hints.yaml` exists, read it before authoring or
reviewing `<name>.tex`. Use OCR labels, palette clusters, and optional vtracer
structural hints as evidence for layout and color placement. Do not convert SVG
paths into the final TikZ source; produce semantic TikZ macros and named
drawing constructs that remain editable during manuscript revision. The handoff
is `coordinate_hints.yaml -> semantic TikZ authoring`.

When moving a panel/subregion by a fixed offset, prefer the scoped dry-run
helper over ad-hoc regex scripts:
`fig-agent helper tex_coordinate_shift.py examples/<name>/<name>.tex --line START:END --dx <cm> --dy <cm>`.
Inspect the diff first; add `--write` only after confirming the selected line
range is exactly the intended patch scope. The helper intentionally does not
infer visual scope or parse arbitrary TikZ expressions.

Golden fixtures declare `accepted` + `golden_contract` in `spec.yaml`;
`check_golden_artifacts.py` auto-escalates into accepted mode when the key is
present. Override with `--no-require-accepted` for ad-hoc inspection. Keep
`/fig_compile` report-only during authoring so the PNG/PDF are produced for
human visual review; the perception data pack is always emitted under
`build/perception/` after successful render. Use `FIGURE_AGENT_STRICT=1` for
manuscript/CI checks and `check_golden_artifacts.py --require-accepted` for the
golden hard gate.

For golden fixtures, `reference_image` points to the fixed visual target. Run
`/fig_extract` to create `coordinate_hints.yaml` from that target before
authoring or drift review.

### L4.5 Vision Critique (host-orchestrated)

```
/fig_critique <name>         host Claude reads build/<name>.png + briefing,
                             plus any panel crop/reference pairs declared by
                             panels[].reference_image + panels[].bbox_pdf_cm,
                             writes structured critique.md (YAML + Markdown).
                             Report-only; subscription tokens, zero external API.
```

Keep authoring freedom high and make critique strict about the rendered meaning.
For every curve, distribution, band, well, or waveform named in the brief, inspect
the panel crop and reduction-scale render and compare its morphology with the
declared reference or stable domain convention. Labels and colors are insufficient:
route cusps, lenses, unintended plateaus, truncated lobes, wrong peak count,
wrong relative width/height, or other claim-changing silhouettes to a normal
finding. Do not require one reusable drawing primitive as the remedy; let the LLM
choose a new construction and re-review the pixels.

For chemical skeletal structures, distinguish an implicit atom vertex from a
radical or electron marker. Do not add a filled junction dot merely to make bond
connectivity more visible; continuous bonds already define the skeletal carbon,
while a dot can assert an unpaired electron. Require a filled dot only when the
brief or chemical mechanism explicitly declares that radical/electron state.

For sulfur-rich inverse-vulcanization schematics, treat S_x/S_y as variable
polysulfide-rank continuation labels, not measured chain lengths or a unique
constitutional repeat. Treat labels such as S60/S75/S85 as declared sulfur
weight-fraction sample identities unless the source explicitly defines another
meaning. Because poly(S-r-DIB) has a complex/random microstructure, label a
drawn bis(thiocumyl) structure as a representative motif unless the source
provides a fully assigned repeat unit; do not promote an artistic chain-length
count into quantitative chemistry. When the source uses “sulfur rank” or a
statistical sulfur-rank distribution, preserve that terminology; do not silently
normalize it to literal chain length.

Typeset chemical element symbols and sample IDs in upright roman glyphs
(`\mathrm{S}`), reserving italic math for variable indices such as $x$, $y$, or
$E_t$. Do not let a generic math-italic element symbol pass as chemically
correct typography merely because the glyph is collision-free.

When an atom is intentionally written on a bond (for example the S labels in an
S$_8$ crown or a polysulfide chain), a visual-clash detector candidate is not by
itself a defect. First verify that the glyph is the atom identity, the bond is
shortened or interrupted at the glyph, and no stroke visibly runs through the
letter; preserve the label and record the candidate as an intentional chemical
overlay rather than deleting the chemistry.

For skeletal-line adjudication, read short inner parallel strokes on an aromatic
perimeter as Kekulé C=C bonds when the ring is otherwise continuous; read paired
strokes outside the ring as an alkene, and unlabeled branch stubs at an implicit
carbon junction as terminal carbon substituents (for example the two methyl
branches in C(CH$_3$)$_2$). Do not call those stubs cut-through marks, broken
bonds, or radicals without an explicit radical/electron declaration. A wavy
bond at an S$_x$/S$_y$ endpoint is a polymer-continuation cue, not a measured
bond count.

Apply the same pixel-level adjudication to text inside an instrument display,
axis math, or a curve-attached qualifier. A `text_on_path` or `near_miss`
candidate is actionable only when a visible stroke crosses the glyph, the label
loses ownership of its referent, or the full glyph bounds enter a neighboring
semantic lane; a detector hit caused by the intended display bezel, axis shaft,
or curve-following placement is an accounted intentional overlay.

When a repair child, candidate sandbox, or fixture-local override is the current
object under review, status and closeout must say which source/render evidence
they are reading. Do not let a stale canonical root hide a fresh declared repair
candidate, and do not let a fresh repair candidate imply canonical promotion,
human acceptance, or publication acceptance. Treat strict-compile green with
`text_boundary_checks` or `label_path_proximity_checks` at zero checked items as
a coverage gap, not as proof that recurring label/path defects are systemically
guarded.

For every dimension, caliper, interval, or delta annotation, identify both named
referents and verify that each endpoint touches or is visibly projected from its
referent; a floating measurement is a defect. Inspect both endpoint projections
at final reduction: a leader that collapses into a bracket cap, peak, marker, or
boundary does not visibly establish the referent even when the source coordinates
technically meet. When the brief declares relative
peak height, width, slope, count, ordering, or an approximate ratio, verify the
rendered encoding and calculate it from source geometry when practical. Do not
accept a verbally correct claim whose visible ratio says something weaker or
different.

When a caliper crosses category-colored regions, reserve a neutral measurement
lane or otherwise isolate its shaft and label from those fills. Treat placement
that makes the measured interval inherit the wrong category as a normal finding.

For a paper-specific variable or annotation, a paper-local declaration takes
precedence over generic symbol or domain convention. Never infer its semantic
domain from notation alone. If the briefing, semantic contract, and declared
reference authority conflict or remain absent, stop for human scientific review
instead of silently relocating or reinterpreting the mark.

For every comparative curve or response, require visible ownership by the named
sample, material, condition, or control through an adjacent label or unambiguous
legend. Qualifiers such as high/low, fast/slow, or shallow/deep are not specimen
identity when the claim depends on which specimen produced the curve. For a
label rotated to follow a curve, inspect the full glyph bounds against the curve,
markers, axis shaft, and tick marks at final reduction. Move the label along and
normal to the curve until it owns a clear annotation lane; shifting only vertically
can trade a curve collision for an axis or tick collision. Do not mask a measured
data stroke merely to make an inline label fit.

For a schematic log--log power-law comparison, verify that the axes are explicitly
logarithmic, the visible slope ordering matches the stated low/high exponent, and
any common start point is either declared or left unmarked. A neutral shared anchor
may clarify a declared common initial state, but do not add scatter points, fitted
values, or a reference curve when the source only supports symbolic slopes.

For a multi-stage measurement schematic, trace preparation or excitation, acquisition,
transformation, and result in order. Flag an unexplained state such as deposited
charge without a source, and keep process labels/arrows out of data peaks,
calipers, and axis-label lanes.

Preserve the declared transfer agency between measurement stages. Do not turn a
manual transfer or discrete repositioning into an automated scan, conveyor, or
continuous in-line measurement. When the same specimen moves between adjacent
stations, use explicit before/after specimen states or another unambiguous
discrete-transfer encoding.

Do not treat an instrument name or capability display such as V/A as proof of
the variable actually applied, held constant, stepped, or acquired. When the
response depends on an operating condition, require that condition at the
apparatus-to-result handoff. Audit palette-role collisions within and across
panels: a sample-identity color must not also encode unrelated terminal polarity,
wiring, apparatus state, or another category without an explicit legend.

For each apparatus schematic, identify the specimen and every active film, layer,
electrode, or interface needed to interpret the measurement. Instrument names,
wires, and grounds do not establish what material is measured; an unbound or
unlabeled specimen region is missing experimental provenance.

Audit projection grammar within each apparatus. Do not mix a flat cross-section
with an undeclared perspective wedge, oblique side face, or pseudo-3D shadow on
only one layer. Require a declared depth-bearing relation or redraw the stack in
one coherent projection so layer identity and contact order remain unambiguous.

When a concrete instrument family or sensing principle is declared, compare the
sensing-head silhouette, orientation, target standoff, and cable/control topology
with its source authority. Renaming a generic icon does not repair geometry that
still depicts a different or confusable measurement method.

When the declared method is an induction-type electrostatic surface voltmeter
(ESVM, including an SK-family head), preserve a fixed non-contact standoff and
the head-to-meter cable path. Do not import Kelvin-probe or KPFM cues such as a
vibrating fork, modulation arcs, a gap-capacitance symbol, or a grid electrode;
also keep charging-state and measurement-state grounding distinct when the
experimental sequence declares that only the latter uses a grounded substrate.

For a floating charged cantilever driven by a nearby electrode, keep the
cantilever mechanically clamped but electrically isolated. A ground symbol on
the high-voltage source belongs to the driven-electrode return circuit; it must
not silently connect to the cantilever, trapped-charge path, or air-gap force
arrow unless the source explicitly declares that electrical boundary.

Preserve the declared evidence granularity for instrument identity. Family-level
authority supports the family name and topology, not unverified model-specific
features, controls, or dimensions; keep those schematic unless a model is declared.

Inventory every guide, construction line, alignment rail, field-like trace,
halo, and bracket that remains in publication-visible pixels. Require each mark
to bind to a named variable, boundary, material, or physical relation; repeated
geometry is not self-explanatory. Remove an unbound mark instead of preserving
it merely because a reusable component emitted it.

For a region declared disordered, amorphous, tangled, or heterogeneous, inspect
repeated paths and particles for unintended periodicity, equal phase, alignment,
or spacing that would imply lamellae, energy levels, or an ordered phase. When
categories are declared co-located in one specimen, inspect their coordinates;
systematic top/bottom or left/right color clustering invents phase segregation.
Three or more long, nearly parallel paths with regular vertical spacing are a
defect even when their phases differ: at figure scale they read as lamellae or
surface wrinkles, not a random-coil matrix. Redraw with varied orientation,
span, and amplitude while keeping any declared trap-to-host anchors intact.

For localized traps, sites, defects, or charge states drawn inside a host
material, verify that each colored core or halo is visibly embedded in the
declared host network, layer, or matrix. A large standalone circle in an empty
field reads as a particle, inclusion, or droplet unless the source declares that
morphology. Prefer bounded host geometry, local contact segments, or restrained
contours that show localization without inventing a second phase.

When localized-state contours are repeated, keep category size comparable but
vary orientation and contour asymmetry enough to avoid a row of identical
flattened ovals. At print reduction the host must still read as a material
matrix; if low-contrast traces disappear, add a few non-periodic host paths or
slightly raise their neutral contrast rather than enlarging the colored traps.

Panel C-style amorphous-host regression rule: for a real-space polymer host next
to an energy diagram, use a small number of non-periodic traces whose combined
coverage reads as one disordered host field. Vary orientation, span, curvature,
and local amplitude, keep every trace bounded inside the film, and do not freeze
the repair to an exact trace count. Allow longer or visually entangled paths when
isolated short fragments would look unfinished, but if a long smooth path reads
as a surface wrinkle, lamella, or specimen-spanning sine wave at reduction,
replace it with shorter, differently oriented matrix fragments. Place each
equal-size shallow/deep core directly on a continuous host trace or local kink.
Do not over-correct into many isolated worm-like fragments: if the texture reads
as biological worms, cracks, scratches, or loose debris instead of a single
amorphous polymer host, restore fewer smooth irregular paths with enough shared
visual span to bind the matrix.
The core alone may carry the category; if extra localization emphasis is truly
needed, change color or weight over only a short asymmetric section of that same
path. Do not add a colored path section by default when the neutral host already
remains legible at reduction scale. A repeated dot centered between two short host arms,
a separate bridge stroke behind the dot, or a flattened pastel halo is a
winged-dot defect: it reads as an icon rather than a localized state. If a
contour is physically necessary, keep it compact, asymmetric, and subordinate.

Treat a few low-contrast, non-periodic paths bounded inside an amorphous film as
matrix-chain texture, not surface wrinkles or measured topography by default.
Flag them only when they are periodic/aligned, extend beyond the declared film,
or are presented with an unearned height axis/legend that changes their meaning.
Do not enlarge localized trap envelopes merely to make the host texture look
busier.

Audit the whole host field, not only the immediate trap neighborhoods. Several
otherwise valid short traces can still read as isolated trap icons when most of
the specimen is empty and every trace exists only to flank a colored core. Give
the neutral matrix enough irregular span and spatial coverage to read first as
one disordered material, while keeping it sparse enough that it cannot be
mistaken for a molecular structure, lamellar texture, or measured topography.
Do not satisfy amorphousness only by making each local curve non-periodic: the
traces must also form a coherent specimen-scale texture rather than a collection
of unrelated placeholder strokes. If a full-width host panel feels visually
oversized because the matrix is sparse, first check whether the host field has
enough specimen-spanning coverage at print reduction; repairing sparse matrix
occupancy is preferred to shrinking the panel when the neighboring energy
diagram and correspondence marks still need the available row height.

For a floating charged dielectric/cantilever near a driven electrode, distinguish
the neutral Maxwell-attraction baseline from the charge-mediated Coulomb result
with a thin, low-contrast baseline arrow versus a stronger, named Coulomb arrow.
An electric field is not intrinsically "inward": its direction depends on the
declared polarity. If polarity is absent, field traces may be shown only as
thin, labeled, direction-neutral guides; never invent arrow direction or a
ground connection to the floating specimen.

Keep apparatus wiring and bias-source housings in a neutral structural tone when
blue/red already carry shallow/deep or force-result meaning elsewhere in the
figure. A conventional colored wire is still a palette-role collision if it can
be read as a scientific category; use color only when the electrical polarity or
terminal identity is explicitly declared and visually owned.

Apply a visual-budget check to mechanism overlays: field guides are supporting
context, not a second result curve. Keep them to the minimum number of thin
traces needed to establish the field, keep their label outside the force-arrow
lane, and reserve the strongest stroke and clearest label for the claimed
force/result. When the claimed result arrow uses a category or result color,
its label should share that role cue unless the color would collide with a
different declared variable; generic gray labels are acceptable for apparatus
parts and neutral baselines, not for the primary force result. Likewise, a
disordered host should use a few legible paths with controlled contrast; adding
more faint scribbles is not a substitute for material identity.

Force labels need endpoint anchoring, not just geometric non-overlap: place the
label beside the arrowhead or along a clearly dedicated annotation lane, never
centered over the source body, trapped charge, or competing result arrow. If a
force name is too long for that lane, line-break or shorten it before reducing
the font; preserve the visual binding to the arrow.

Do not retain a polarity-neutral field trace merely to fill the mechanism scene.
When a named Maxwell baseline arrow already communicates the field-mediated
attraction, remove redundant pale curves and a floating $\mathbf{E}$ label unless
they encode a separate declared measurement or geometry.

Within and across panels, require the same physical process to reuse one arrow
and line-style grammar unless a legend or brief-declared contrast explains the
difference. Treat an unexplained solid/dashed or arrowhead change as a possible
second mechanism, not harmless styling.

Inspect repeated categorical markers for unintended size encoding. When marker
area varies, require the difference to bind to a declared quantitative variable;
otherwise normalize co-equal sites, states, and samples so category is not
mistaken for magnitude, population, or physical extent.

For each mechanism arrow, verify that the arrow tail touches its declared source
state and the arrowhead touches the named destination boundary or state. Treat a
path that stops short and relies on visual proximity as an unbound mechanism.

When the same population, specimen, or state is shown in multiple representations,
require visible correspondence through aligned anchors, identifiers, color, or
leaders. Keep an equivalence connector out of plot axes and avoid arrowheads or
path styling that would falsely imply transport, causality, or chronology.

Inspect every crossing between two semantic paths, or between a mechanism path
and a state/reference line. Require an explicit junction, transition, or declared
relation when the crossing carries meaning; otherwise route the accidental
crossing to a clear lane. Audit named boundaries, thresholds, baselines, and
reference levels for semantic aliases: two names for the same physical quantity
must bind to one visible referent, not separate lines or regions that invent a
second state. Review labels both in panel crops and at the actual
full-figure print reduction. If a specimen or mechanism label works only in the
crop, preserve the claim by shortening or restructuring it rather than repeatedly
shrinking the font.

Derive panel-audit crop boxes from declared canvas coordinates, panel bboxes, or
separator rules rather than approximate image fractions. Check each crop for
neighbor-panel content before using it as evidence; a crop that includes a sibling
axis, label, or rule is a packaging defect and must be regenerated at the exact
panel boundary.

Also inspect for workflow-metadata leakage. Terms such as `HERO`, priority,
draft, iteration, reviewer notes, or approval state belong in comments/specs and
must not appear in publication-visible pixels unless explicitly declared as
reader-facing scientific text.

Treat panel containers as semantic marks, not default decoration. Repeated
rounded frames that only partition a grid can make a scientific figure read as
UI cards; require a scientific boundary role, otherwise prefer an open canvas,
whitespace, or restrained separator rules and re-check the full-figure hierarchy.
An open canvas still has panel lanes: infer them from separator rules, aligned
headings, whitespace gutters, and neighboring content, then flag labels that
cross into a sibling lane or beyond the shared canvas. Do not treat the absence
of a closed rectangle as the absence of a boundary.

Audit panel proportions from both allocated area and rendered content occupancy;
do not infer importance from area alone or reward an equal grid by default. A hero
panel may be larger when it integrates multiple necessary representations, but
flag size created mainly by empty header bands, unused margins, or decorative
containers. Before resizing, verify that the proposed boundary change enlarges
claim-bearing marks at final reduction rather than merely moving whitespace between
rows. Treat a dense panel as undersized only when its labels, axes, or semantic
separation fail at reduction scale.

Treat a clean content-to-divider gutter as intentional whitespace when sibling
panels retain comparable breathing room and no claim-bearing mark is clipped or
illegible. Never add filler text, decorative shapes, or invented mechanism content
solely to occupy that gutter; resize only when the empty area is caused by a
misallocated panel boundary or a real reduction-scale legibility failure.

When the declared target is Nature Communications, audit against its current
figure guidance: lower-case bold panel letters, clear sans-serif lettering at an
approximately common size, a white background, restrained boxing/color/decorative
effects, and no final printed line below 1 pt. Size every panel for the same
reduction factor rather than inventing a hero exception. Recheck the official
Nature Communications author page before final compliance work because journal
requirements can change.

Treat panel letters as navigation markers, not focal scientific content. At the
declared final width, compare their visible cap height with adjacent panel titles
and labels; bold weight may distinguish them, but materially oversized letters
that dominate the first visual fixation are a hierarchy defect unless the journal
or paper-wide style explicitly requires that scale.

Compare equivalent axis titles, variables, units, and endpoint labels across
panels at the final reduction. Keep scientifically co-equal axes on a common
typographic floor; do not demote a crowded panel's claim-bearing axes to an
annotation tier when spacing or layout should be repaired instead.

Treat `thin_stroke` warnings on claim-bearing curves, marker outlines, leaders,
and apparatus boundaries as normal print-legibility findings even when compile
remains green. Raise them to the declared stroke floor or remove a redundant
outline; do not preserve a sub-floor stroke merely because it is visible when
zoomed in.

When a usable figure-level reference image or panel reference+bbox pair exists,
`/fig_status` and `/fig_export` promote missing/stale `critique.md` to a
pre-export checkpoint. Use `fig-agent export <name> --skip-critique` only
for intentional draft exports.

`/fig_loop <name> --goal "<goal>"` records a single verify-only loop checkpoint
under `.scratch/fig-loop-runs/`. It shares `/fig_status` state inference and
records `critique_adjudication.yaml` as missing, fresh, stale, or invalid when
present. It does not patch source, compile, export, accept artifacts, or mutate
git state.

Use `fig-agent helper critique_lint.py <name>` after `/fig_critique
<name>` and before `/fig_adjudicate <name>` when `critique_adjudication.yaml`
is missing or stale. The lint preflight catches duplicate finding ids,
malformed critique frontmatter, and missing top-tier finding links before they
become loop state. `/fig_adjudicate` then scaffolds every panel-level and
top-level critique finding, stamps the current critique hash, and defaults
unresolved findings to `needs_human` so the loop cannot silently drop reviewer
findings.

For schema v1.8+ critiques, treat intra-instrument label failures as named
micro-defects rather than generic polish comments: use
`label_backdrop_overflows_outline` when a label fill/backdrop protrudes outside
its enclosing box, and `label_glyph_overlaps_internal_drawing` when a label or
backdrop crosses an internal display, axis, needle, or separator in the same
box. Use `label_crosses_column_rule`, `label_crosses_panel_boundary`, and
`label_overflows_row_box` for declared text-boundary candidates from
`build/text_boundary_clash.json`. Author or refresh verbose
`spec.yaml.text_boundary_checks` from `spec.yaml.text_boundary_layout` with
`fig-agent text-boundary <name> --write`
after adding row boxes, column rules, horizontal rules, or forbidden internal
rectangles. `BLOCKER` and `MAJOR` instances must link to a normal finding or
be explicitly marked `accept_simplification`. When the brief lists Visual Clash
Candidates, every `VC###` id must appear in exactly one
`micro_defects[].visual_clash_ref` entry; accepted candidates still need an
explicit `accept_simplification` rationale. When the brief lists Text Boundary
Clash Candidates, every `TB###` id must appear in exactly one
`micro_defects[].text_boundary_ref` entry. For schema v1.10+ critiques, every
accepted visual-clash candidate must also set `accept_simplification_reason` to
one of `false_positive`, `intentional_schematic`, `outside_target_region`,
`convention_acceptable`, or `decorative_background`, plus a non-empty
`accept_simplification_rationale`.
The critique must also fill `crop_audit_log` with exactly one entry for every
`build/audit_crops/manifest.json.required_crop_ids` item; uncertain crop
verdicts must remain explicit rather than being treated as pass.
When the initial-review manifest includes `full_center_vertical` or
`full_center_horizontal`, inspect those seam-spanning views as first-class
evidence. Quadrant coverage alone is not evidence that a semantic unit crossing
a crop boundary was reviewed as a whole; keep its verdict uncertain until a
view containing the complete unit has been inspected.
When `critique_reference_pack.yaml` exists, `/fig_critique` uses it as the
project-specific top-tier calibration source and includes its target journal,
reference class, must-match traits, must-avoid traits, and calibration
questions in the brief.
When `spec.yaml.paper_aesthetic_context` is declared, `/fig_critique` resolves
`examples/_paper_aesthetic_contexts/<paper_id>.yaml` and emits a
`Paper-Wide Aesthetic Context` section. The critique must cite exact paper-wide
anchors in `top_tier_audit.cross_panel_semantic_grammar`,
`top_tier_audit.aesthetic_coherence`, and
`editorial_art_direction.visual_identity`; generic art-direction prose is
invalid once the fixture opts in.
When `spec.yaml.journal_art_direction_playbook` is declared, `/fig_critique`
resolves `examples/_journal_art_direction_playbooks/<playbook_id>.yaml` and
emits a `Journal Art-Direction Playbook` section. The critique must fill
`journal_art_direction_playbook_audit`, cite exact playbook anchors in the
required top-tier/editorial/journal assessment rationale slots, and tie those
anchors to current-artifact evidence; generic "looks polished" prose is
invalid once the fixture opts in.
When `aesthetic_intent.yaml` uses schema v2, `/fig_critique` emits an
`Aesthetic Lever Grammar` section and the critique must fill
`aesthetic_lever_audit` exactly once for every declared lever. The host critique
must cite exact aesthetic-intent anchors with current-artifact evidence in the
required top-tier/editorial slots and route each non-passing lever through a
visible TikZ patch, SVG polish, semantic backport, or human art-direction path;
generic "improve polish" prose is invalid. Non-passing levers must name concrete
anti-pattern evidence; active routes must match the declared `default_route`;
`svg_polish` requires `ready_for_svg_polish`, `semantic_backport` requires
`semantic_backport_required`, and `human_art_direction` must cite the explicit
human art-direction gate.
For schema v1.17 grounded critiques, `/fig_critique` must also fill
`aesthetic_antipattern_audit`, `weakest_panel_coherence`, and
`reference_learning_accountability`. These fields convert softer top-tier
design risks into route-aware evidence: generic template feel, childish or
cartoonish language, weak eye path, weakest-panel mismatch, reference
over-copying, and reference under-learning must be explicitly classified as
`none`, `tikz_patch`, `svg_polish`, `semantic_backport`, or
`human_art_direction`. They are audit/accountability fields, not permission for
hidden source edits or release-gate bypass.

Use `/fig_closeout <name>` after a human or outer agent patches one loop-selected
target. It reports which closeout steps are still stale, missing, blocked, or
passed without running those steps itself. It withholds the final loop-rerun
action until prerequisites are closed and keeps golden roll-forward as manual
approval.

Replaces the v0.1 HALT-then-paste review surface via rename + extend
(`scripts/review_brief.py` → `scripts/critique_brief.py`,
`commands/fig_review.md` → `commands/fig_critique.md`). The old prompt-template,
redaction, preview-selection pipeline, and selected-preview stage gate were
deleted in PR #8a + #8b. See `docs/architecture-v0.2-proposal.md`.

**Status check** (canonical first step — see Driver rule for agents above): /fig_status <name> — infers stage plus render/critique/export/acceptance/final_ready state from filesystem + spec.yaml; with no arg, summarizes all figures. It is read-only (no persistent state written), but it is the workflow entry point, not a passive query.

## Per-figure folder convention

```
examples/<name>/
├── spec.yaml          # scope/panels/style profile (lightweight, NOT single source of truth)
├── briefing.md        # human's intent in prose (used to seed prompt)
├── reference/         # optional saved reference PNGs for target matching
├── coordinate_hints.yaml # /fig_extract authoring hints from reference_image
├── previews/          # user-generated draft images saved under examples/<name>/previews/
├── <name>.tex         # human/LLM-authored TikZ source
├── build/             # compile artifacts (gitignored)
└── exports/           # final PDF/SVG/TIFF/PNG (gitignored — checked in only on release)
```

`selected/` and selected-preview metadata are v0.1 legacy surfaces, not part of
the active workflow.

## Boundaries

- **No data plots.** Quantitative axes (n vs composition, measured I(t) curves, DOS spectra, etc.),
  measurement curves derived from real data, error bars → out of scope. Redirect user to
  matplotlib or Graph_making_hub. *Schematic mockups* of symbolic axes are inside scope
  when the axis labels are conceptual, tick values are illustrative or absent, and no
  measured numeric values are encoded. If the user names
  numerical sweep ranges (S60-S85), peak positions (S70-S75), or specific measurement values,
  that is the data-plot signal and belongs elsewhere.
- **No image-gen API call** in any step. If user asks for one, decline and remind them this
  plugin is gen-tool-agnostic.
- **No reference image retrieval** (Crossref/Semantic Scholar/PaperBanana paths deprecated).
- **No "single source of truth" YAML spec.** spec.yaml is lightweight (panels + style
  profile). Meaning lives in briefing.md and the .tex source.

### Scope-drift signals during interview

When `/fig_new` is collecting the briefing, watch for these red flags in user answers and
**ask the user to confirm intent before continuing** ("data figure → reframe to schematic, or
redirect to matplotlib?"):

- Quantitative variable symbols tied to measured values or fitted datasets: `n`, `τ`, `V`, `I`, `T`, `t`, `E_t`, `g(E_t)`, etc.
- Sweep / vs phrasing: "vs composition", "vs time", "ratio", "sweep S60..S85"
- Measurement keywords: "raw + fit", "error bar", "peak position", "RLM MM", "ISPD curves"
- Real-data axes: any axis whose tick values would matter to a reader

## Asset references

- Cowork path rule: run the automated pipeline from the source plugin root
  (`plugins/figure-agent`) or another workspace where `scripts/`, `styles/`,
  and `examples/` are siblings. If those directories are missing from the
  current working directory, treat it as a mount/working-directory issue, not as
  a missing installed-plugin bundle.
- Style Lock source: `styles/polymer-paper-preamble.sty` (\IsoCharge, \GradSlab, \IsoBlock, \IsoConeTip)
- Compile chain: `scripts/compile.sh` (lualatex; optional `FIGURE_AGENT_STRICT=1`
  hard gate)
- Checks: `fig-agent helper check_collisions.py`, `fig-agent helper check_visual_clash.py`
- Perception pack: `scripts/perception_pack.py` writes
  `build/perception/extract.yaml` and `build/perception/overlay.png`
- Export: `scripts/export_svg.sh`, `scripts/svg_to_png.sh`
