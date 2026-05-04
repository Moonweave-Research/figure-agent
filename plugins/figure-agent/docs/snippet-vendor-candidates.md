# Snippet Vendor Candidate Registry

**Status:** living document (2026-05-04 onwards)
**Purpose:** track community TikZ/LaTeX assets identified as vendor candidates for the L3 snippet library, plus their license, fitness, and current adoption state.
**Plan:** `architecture-v0.3-snippet-library.md` §2.4 (acceptance gate).
**README catalog:** `styles/snippets/README.md` lists only **vendored** items. This file lists **all** discovered candidates incl. rejected and under-review.

## Status legend

| State | Meaning |
|---|---|
| `candidate` | discovered; license + tool-coverage value not yet verified |
| `under_review` | license verified; matching to a paper-figure type in progress |
| `vendored` | present in `styles/snippets/`; entry mirrored in `README.md` |
| `pattern_only` | not vendored as code, but the pattern/idiom is referenced inside our snippets |
| `rejected_license` | license unrecoverable (null, restrictive); cannot vendor |
| `rejected_unavailable` | source no longer exists (CTAN 404, repo deleted); not retrievable at this time |
| `negative_evidence_for_<topic>` | searched and found nothing for a specific topic; do NOT generalize to "rejected" — re-search for other topics |
| `deferred` | license + value OK; no current snippet needs it, but a future figure type does — kept warm for that trigger |

## Suitability grading (frame: figure-agent tool coverage, not current-fixture fit)

This grading evaluates **tool-level coverage potential** — whether the asset can serve at least one paper-figure type the figure-agent will plausibly handle in the manuscript pipeline. NOT whether it fits the current `golden_trap_depth_picture` fixture. A "wrong domain for this fixture" is NOT a downgrade reason.

- **A** = vendor-quality asset (license clean, paper-grade output) usable as primary source for at least one paper-figure type the tool will eventually handle (chemistry, plotting, schematic, mechanism, energy diagram, etc.)
- **B** = pattern adaptable; idiom can be lifted into a future snippet even if not full vendoring
- **C** = genuinely irrelevant to any paper-figure type (e.g. UI / electrical schematics / billiards) OR license unrecoverable

Frame correction 2026-05-04 (post `/compass`): prior grading used "doesn't fit current fixture" as a downgrade trigger. That confused **figure-agent tool scope** (broad) with **golden_trap_depth_picture scope** (narrow). All `rejected_fitness` entries from the prior frame are reviewed here; entries serving a future figure type are reclassified to `deferred` with the figure type named.

---

## Registry

### Chemistry / molecular

| ID | Source | License | Suitability | Status | Target snippet | Notes |
|----|--------|---------|-------------|--------|----------------|-------|
| C-01 | `chemfig` package + `\polymerdelim` (CTAN) | LPPL 1.3c | A | `vendored` (transitively, via `\usepackage{chemfig}` in preamble) | A1 polymer_chain (current); future polymer_abstract | manual §12.4, six worked examples (homopolymer/PVC/Nylon/PCL/**PPS**/cross-linked). PPS = closest to our sulfur backbone case. URL: https://tug.ctan.org/macros/generic/chemfig/chemfig-en.pdf |
| C-02 | `chemfig` manual §12.4 PPS example (poly(phenylene sulfide)) | LPPL 1.3c | A | `deferred` | future `polymer_abstract.snippet.tex` | Use when briefing requests *abstract* polymer notation `[…]_n`, not monomer-explicit density. Direct vendoring of the manual example is permitted under LPPL. |
| C-03 | jejrogers/chemfig-examples — polystyrene block (`structures.tex` L314-335) | **null** (no LICENSE file) | C | `rejected_license` | — | Pedagogically perfect; cannot vendor. Use as syntax study only. URL: https://github.com/jejrogers/chemfig-examples |
| C-04 | `chemmacros` package (Newman projection, reaction arrow, oxidation) | LPPL 1.3c | A | `deferred` | future `reaction_scheme.snippet.tex` | When/if we draw mechanism/synthesis pathways. CTAN: https://ctan.org/pkg/chemmacros |
| C-05 | `mhchem` (`\ce{S_8}`, `\ce{H_2O}` inline formulas) | LPPL 1.3c | A | `deferred` | caption / label inline formulas | Not a snippet itself; preamble loader. CTAN: https://ctan.org/pkg/mhchem |
| C-06 | `chemobabel` (ChemDraw → chemfig via Open Babel) | LPPL | A | `deferred` | future SMILES/molfile → figure pipeline | When manuscript needs to render molecules from external chemistry tools (ChemDraw, Avogadro, RDKit). Not a snippet itself but a content-import bridge. Reframed from prior `rejected_fitness`. |
| C-07 | `mol2chemfig` (SMILES → chemfig) | LPPL | A | `deferred` | future SMILES → figure import | Same role as C-06 with SMILES input. Useful when scientific data has SMILES strings that need vector rendering. Reframed from prior `rejected_fitness`. |
| C-08 | `xymtex`, `ppchtex`, `streetex` | mixed (verify per-package) | B | `deferred` | future legacy chemistry figure import | Older but still ship in TeX Live; useful for replicating figures from pre-2010 papers if the manuscript cites them. Specific package use case-dependent. Reframed from prior `rejected_fitness`. |

### Plotting (axes, curves, fills)

| ID | Source | License | Suitability | Status | Target snippet | Notes |
|----|--------|---------|-------------|--------|----------------|-------|
| P-01 | `pgfplots` core (`\addplot`, `axis`, `loglogaxis`, `xticklabels`) | LPPL 1.3c | A | **`vendored`** (A2 integrated WIP, 2026-05-04) | **A2 log_plot** | Vendored as TikZ style key (`paper loglog/.style`) in `polymer-paper-preamble.sty`. No wrapper macro. Sampling caveat: explicit `coordinates {…}` preferred over `\addplot {f(x)}` on log axes. |
| P-02 | `pgfplots fillbetween` library | LPPL 1.3c | A | `under_review` | **A4 dos_lobes** | Replaces hand-rolled `\SmallLobe` Bézier. `\addplot fill between` over Gaussian fns. |
| P-03 | `pgfplots ticks` library + minor-grid pattern | LPPL 1.3c | A | **`vendored`** (A2) | A2 log_plot (sub) | Folded into `paper loglog` style key (`xminorgrids=true, yminorgrids=true`). DO NOT enable `log ticks with fixed point` — breaks default `10^k` tick label format (G2 spike confirmed). |
| P-04 | janosh/tikz pgfplots examples | MIT | B | `candidate` | A2 reference patterns | TODO: `gh api repos/janosh/tikz/contents` + grep `pgfplots` to enumerate; promote to `pattern_only` if useful idiom found. |
| P-05 | TikZ `decorations.markings` for tick highlights | LPPL 1.3c | B | `deferred` | A2 (optional) | Pattern from chemfig manual §12, also TeXample geometry examples. |

### Band / energy / level diagrams

| ID | Source | License | Suitability | Status | Target snippet | Notes |
|----|--------|---------|-------------|--------|----------------|-------|
| B-01 | `bandplot` package | (was LPPL) | — | `rejected_unavailable` | — | CTAN 404 confirmed 2026-05-04. Package no longer listed; not in TeX Live. Status changed from `candidate` to `rejected_unavailable`. Look in Wayback Machine if ever needed. |
| B-02 | `modiagram` (molecular orbital diagrams) | MIT | A | `deferred` | **future MO diagram figure** (e.g. polymer HOMO-LUMO, photoexcitation schematic) | Confirmed in TeX Live 2026 (`kpsewhich modiagram.sty` ✓). MO diagram is a distinct paper-figure type from semiconductor band diagram; both legitimate manuscript needs. Vendor when manuscript adds MO figure. CTAN: https://ctan.org/pkg/modiagram |
| B-03 | TeXample "Splitting of Hydrogen in different magnetic fields" | CC-BY-SA 4.0 | B | `deferred` | future Zeeman / spectroscopy energy-level figures | Energy-level diagram with magnetic-field splitting. Vendor pattern when paper covers Zeeman / EPR / NMR splittings. https://texample.net/hydrogen-splitting/ |
| B-04 | TeXample "Perrin–Jablonski diagram" | CC-BY-SA 4.0 | B | `deferred` | future photophysics / fluorescence figure | Singlet/triplet level diagram with intersystem crossings. Vendor when paper covers photoluminescence / phosphorescence mechanism. https://texample.net/the-perrin-jablonski-diagram/ |
| B-05 | hand-curated TikZ for semiconductor band diagram (CB/VB rectangles + E_t + trap levels) | own work | A | `under_review` | **A3 band_diagram** (current target) | Existing `\BandDiagram` macro in `polymer-paper-preamble.sty` + dogfood findings (`docs/macros/band-diagram-gaps.md`, 5 gaps). Native option since bandplot unavailable. |

### Backbone / chain primitives (non-chemfig)

| ID | Source | License | Suitability | Status | Target snippet | Notes |
|----|--------|---------|-------------|--------|----------------|-------|
| K-01 | PetarV-/TikZ `DNA/dna.tex` `\bond{topcolor}{btmcolor}{x}` macro + `braids` library | MIT | B | `pattern_only` | future disulfide bridge macro | 4-line macro draws tri-segment vertical bond with two colors + dotted middle. Maps to `-S-S-` cross-link or `-C-X-C-` indicator. https://github.com/PetarV-/TikZ |
| K-02 | PetarV-/TikZ `Gene expression` codon-brace annotation | MIT | B | `deferred` | sequence-annotated chain (if briefing requires labeling every Nth monomer) | https://github.com/PetarV-/TikZ |

### Lattice / random patterns

| ID | Source | License | Suitability | Status | Target snippet | Notes |
|----|--------|---------|-------------|--------|----------------|-------|
| L-01 | janosh/tikz `basis-plus-lattice` triptych template | MIT | B | `deferred` | future `polymer_synthesis_triptych.snippet.tex` | "(monomer) + (repeat) = (polymer)" educational figure. https://github.com/janosh/tikz |
| L-02 | janosh/tikz `high-entropy-alloy` `\foreach` random-color sphere lattice | MIT | B | `deferred` | future `random_copolymer_matrix.snippet.tex` | Uses `pgfmathrandomitem` — paper-grade random pattern. |
| L-03 | janosh/tikz `organic-molecule` `pgfonlayer{background}` ball-and-stick | MIT | B | `pattern_only` | reference idiom | Bonds drawn first on background layer, atoms on default layer over them — standard ball-and-stick trick. |

### Document/diagram structure

| ID | Source | License | Suitability | Status | Target snippet | Notes |
|----|--------|---------|-------------|--------|----------------|-------|
| D-01 | `schemabloc` (block diagrams) | LPPL | A | `deferred` | future `flow_diagram.snippet.tex` | Flow / block diagrams. Vendor when manuscript adds methodology pipeline / control-system / signal-flow figure. Reframed from B → A: paper figures often need block diagrams, this is the standard vendor. |
| D-02 | `smartdiagram` (list → diagram) | LPPL | B | `deferred` | future bullet → graphic transformation | Restrictive layout vocabulary, but useful for "list → quick visualization" Conference poster / supplementary Fig. Reframed from `rejected_fitness` → `deferred`. |
| D-03 | `circuitikz` (electrical schematics) | LPPL | A | `deferred` | future device circuit diagram | If manuscript covers measurement setup with electrical components (probe stations, transimpedance amplifiers, dielectric test cells), this IS the standard vendor. Reframed from `rejected_fitness` → `deferred`: many polymer-electronics papers ship circuit diagrams. CTAN: https://ctan.org/pkg/circuitikz |

### Mineable corpora (bulk-search candidates)

| ID | Source | License | Suitability | Status | Target snippet | Notes |
|----|--------|---------|-------------|--------|----------------|-------|
| M-01 | AutomaTikZ DaTikZv2 (~360k human-created TikZ figures) | MIT (curation), individual entries vary | varies | `candidate` | future bulk mining | https://github.com/potamides/AutomaTikZ — only mine when a specific snippet has no curated source. |
| M-02 | TeX.SE high-vote answers | CC-BY-SA 4.0 (with attribution) | varies | `candidate` | future per-need search | Agents could not fetch directly; manual review when a specific need arises. Filter pre-2018 answers (chemfig API drift). |

### Negative survey results (search-and-found-nothing)

These are **negative-evidence audit trails** — sources searched exhaustively where polymer-chain content was not found at the time of survey (2026-05-04). They are NOT permanently rejected sources; if a future paper figure type is searched (MO diagrams, mechanisms, electronics), these sources should be re-searched in that frame. Status: `negative_evidence_for_polymer_chain` (not `rejected`).

| ID | Source | License | Polymer search result | Re-search trigger |
|----|--------|---------|------------------------|-------------------|
| R-01 | TeXample.net (1043 examples) | CC-BY-SA 4.0 | 0 polymer-relevant; chemistry category = 13 entries, all polymer-irrelevant | Re-search for any future figure type — site is broad; search by specific need |
| R-02 | TikZ.net | CC-BY-SA 4.0 | 0 polymer entries; chemfig not indexed | Re-search for energy / band / circuit figures |
| R-03 | xinychen/awesome-latex-drawing | MIT | 100% ML/Bayes/tensor — 0 chemistry | Re-search if manuscript adds ML methods figure (genuine match scope) |
| R-04 | Overleaf chemistry templates (8 enumerated) | CC-BY (typical) | All journal-style boilerplate, 0 figure source | Re-search Overleaf for non-template gallery items per future need |
| R-05 | Mathcha.io | unknown | GUI tool — coordinate-soup TikZ, non-parametric | Use only as last-resort sketch tool, not vendor source |
| R-06 | LaTeX Templates (latextemplates.com) | varies | No chemistry/physics category | Document-template directory; not a figure source |
| R-07 | walmes/Tikz, f0nzie/tikz_favorites, MartinThoma/LaTeX-examples | varies | License: null OR no polymer content | License re-check on future revisits if maintainers add LICENSE files |
| R-08 | Stefan Kottwitz blog/book/cookbook | varies | 0 polymer figures across 4 sources | Re-search for any other figure type — Kottwitz publishes broadly |
| R-09 | arXiv inverse-vulcanization papers | varies | 0 results — field publishes on ChemRxiv (PDF-only) | Re-search arXiv for other domains the manuscript covers |

---

## Adoption decision rules

1. **A-grade + license-clean** → schedule for vendoring at the next snippet step that targets it.
2. **B-grade + license-clean** → keep as `pattern_only` reference inside the snippet code (cite in snippet header comment).
3. **C-grade** → keep entry for negative-evidence audit trail; do not revisit unless requirements shift.
4. **license unclear / null** → never vendor; reference as inspiration only with explicit citation.
5. **before opening A2/A3/A4**: filter this registry for `candidate`/`under_review` entries with the matching `Target snippet` field; promote to `vendored` after smoke fixture passes.

## Update protocol

When new candidates surface during snippet authoring:

1. Append a row in the appropriate category table with `candidate` status.
2. Verify license (read repo `LICENSE`, manual title page, CTAN topic line).
3. Promote to `under_review` once license confirmed.
4. Promote to `vendored` once snippet files land in `styles/snippets/` and smoke fixture compiles.
5. If rejected, set status `rejected_license` or `rejected_fitness` with one-line reason.

This registry is append-only for the candidate set; status field is the only mutable column.

## Survey provenance

Registry initialized 2026-05-04 from a 4-agent parallel sweep:

- TeXample + TikZ.net + awesome-latex-drawing crawl
- janosh/tikz + PetarV-/TikZ + GitHub topic search
- chemfig manual + CTAN chemistry/physics topic enumeration + Stefan Kottwitz blog/book ecosystem
- Overleaf + LaTeX Templates + Mathcha + arXiv supplementary + ChemRxiv + TeX.SE adjacent

Each agent confirmed exhaustive scan of its assigned sources; negative results (rejected categories above) are part of the audit trail, not omissions.
