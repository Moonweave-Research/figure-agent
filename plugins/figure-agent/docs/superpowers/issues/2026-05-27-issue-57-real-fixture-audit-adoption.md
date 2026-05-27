# Issue 57 - Real Fixture Audit Adoption

Status: proposed

Depends on: Issue 56 journal art-direction playbook completion

## Problem

The plugin now has strong audit layers, but many of them only run when a
fixture explicitly opts in through `spec.yaml` or companion packs. A fixture can
therefore look "covered" by the plugin while still missing the declarations
that activate text-boundary, label-path, aesthetic, paper-wide, or journal
art-direction accountability.

The main risk is not missing detector code. The risk is silent non-adoption:
the plugin is capable, but a real figure does not declare the inputs that make
the capability run.

## Goal

Create and execute a fixture-by-fixture adoption pass that makes audit coverage
explicit for real examples, starting with the highest-risk fixtures and keeping
each opt-in narrow enough to avoid false-positive workflow noise.

## Order

Run this before Issue 58. The single-next-action UX should be designed against
real fixture states after audit opt-ins are known, not against idealized docs.

## Scope

In scope:

- Build an adoption matrix for real fixtures under `examples/`.
- For each fixture, decide whether it needs:
  - `text_boundary_layout` / `text_boundary_checks`;
  - `label_path_proximity_checks`;
  - `critique_reference_pack.yaml`;
  - `aesthetic_intent.yaml`;
  - `spec.yaml.paper_aesthetic_context`;
  - `spec.yaml.journal_art_direction_playbook`.
- Add fixture-local declarations only when the current render can be compiled
  and the resulting candidate reports are accounted for.
- Add focused tests that lock each adopted fixture contract.
- Record dogfood evidence for every fixture whose opt-in changes critique
  freshness or loop routing.

Out of scope:

- Editing figure source for art direction.
- Adding new detector algorithms.
- Adding external model calls.
- Promoting any fixture to accepted/golden.
- Making global default aesthetic or journal packs.

## Acceptance

- A milestone document lists all real fixtures, their audit opt-in state, and
  the reason for each "not adopted" decision.
- At least the highest-risk active fixtures are checked for boundary/path
  hazards.
- Any new `TB###` or `LP###` candidate is either zero in the current render or
  has an explicit critique/accounting path.
- Any newly declared aesthetic, paper-wide, or journal playbook pack
  participates in critique freshness.
- Tests cover the exact adopted fixture declarations.
- No generated build/export artifacts are committed.

## Review Questions

1. Did any fixture remain silently under-audited because it lacks declarations?
2. Are new checks narrow enough to avoid false positives on intentional idioms?
3. Does each adoption produce useful evidence, or only workflow friction?
4. Are active figure source edits kept out of this plugin-adoption slice?

## Recommended First Pass

Start with fixtures that already demonstrated real dogfood value or repeated
manual catching:

1. `fig1_overview_v2_pair_001_vault`
2. `fig1_overview_v2`
3. `golden_trap_depth_picture`
4. `n3_trial_01_trap_depth`
5. `n3_trial_02_actuation_sequence`

Then sweep smaller/smoke fixtures only for low-noise deterministic checks.
