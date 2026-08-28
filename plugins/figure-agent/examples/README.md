# Figure Agent example workspace

This directory is intentionally flat. A folder name alone does not tell you
whether a figure is current, historical, a regression fixture, or a saved
artifact collection. The flat layout keeps fixture-relative TeX imports,
compile outputs, current-candidate pointers, status lookup, and regression
tests reproducible.

## Start here for the current sulfur-paper schematics

The active development baseline is the `pair001-main-schematics` set:

| Paper role | Fixture | Edit entry point |
|---|---|---|
| Fig1 overview | `fig1_updated_agent_redraw_v1` | `review/current-candidate.json` resolves the active nested source |
| Fig2a mechanism | `fig2_charge_transport_mechanism` | `fig2_charge_transport_mechanism.tex` |
| Fig5 mechanism | `fig5_cantilever_actuation_artifact_v2` | `fig5_cantilever_actuation_artifact_v2.tex` |

Run `fig-agent status <fixture>` before editing. The active baseline means
development focus only; it does not promote a fixture to a paper artifact or a
publication-ready figure.

## How historical material is organized

- `docs/paper_figure_map.yaml` is the machine-readable classification of every
  top-level fixture: active candidate, regression, pilot, reference,
  superseded, SI, sandbox, or bounded non-fixture artifact.
- `docs/current-sulfur-paper-figure-state.md` explains paper roles, source
  authority, and the boundary to the external ResearchOS artifact registry.
- A nested `review/` directory is provenance, not a second active fixture. For
  Fig1, see `fig1_updated_agent_redraw_v1/review/README.md` before interpreting
  older comparative, repair, prospective, or rejected-attempt folders.
- `build/` and routine `exports/` paths are generated evidence. They are not a
  cleanup target during source or legacy classification work.

Do not reorganize active or historical folders based on date/version words.
First update their map classification and prove that live pointer, source,
test, and evidence references have a stable replacement.
