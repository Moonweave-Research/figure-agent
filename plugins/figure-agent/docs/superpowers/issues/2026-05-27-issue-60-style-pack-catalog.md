# Issue 60 - Journal and Paper Style Pack Catalog

Status: implemented in branch `codex/issue60-style-pack-catalog`

Depends on: Issue 57 real fixture audit adoption and Issue 59 SVG polish
promotion dogfood

## Problem

The plugin now supports fixture-local aesthetic intent, paper-wide aesthetic
context, and journal art-direction playbooks. Those contracts are useful, but
they are still mostly infrastructure. Without a small catalog of vetted packs,
each figure session must restate the same abstract art-direction vocabulary.

That creates drift: one session says "Nature-like restraint", another says
"not childish", another says "clean but hand-crafted". The plugin needs
reusable pack templates that encode those ideas consistently.

## Goal

Create a small, explicit catalog of reusable style packs for common manuscript
contexts while preserving fixture-level opt-in and avoiding global defaults.

## Order

Run after at least one real adoption pass and after SVG polish route dogfood.
The catalog should encode observed production needs, not speculative taste
rules.

## Scope

In scope:

- Add curated pack templates for:
  - restrained Nature Communications main-text schematics;
  - higher-density Nature Materials style schematics;
  - Science-style compact explanatory schematics;
  - graphical abstract / cover-like expressive variants, clearly separated from
    main-text restraint.
- Keep packs under explicit opt-in directories such as:
  - `examples/_journal_art_direction_playbooks/`;
  - `examples/_paper_aesthetic_contexts/`.
- Add schema/parser tests or fixture tests that prove the packs load.
- Document when each pack should and should not be used.

Out of scope:

- Applying packs globally.
- Rewriting existing figure sources.
- Scraping web references.
- Claiming that a pack guarantees journal acceptance.
- Expanding the critique schema unless a required field is impossible to express
  with v1.12.

## Acceptance

- Each catalog pack validates with existing parsers.
- Each pack has explicit venue context, visual maturity, design center,
  anti-patterns, positive signals, route rules, and human review triggers.
- Main-text packs forbid decorative/cover-style effects by default.
- Expressive packs are opt-in and cannot silently apply to main-text figures.
- Documentation explains how to choose a pack and how it interacts with
  `aesthetic_intent.yaml`.

## Review Questions

1. Are the packs reusable without becoming vague generic taste prose?
2. Do main-text packs remain restrained enough for real journal figures?
3. Are expressive/cover-like packs isolated so they cannot leak into
   manuscript figures?
4. Do pack ids and anchors stay short enough for reliable host-LLM attention?

## Implementation Notes

- Added four opt-in journal art-direction playbooks:
  - `examples/_journal_art_direction_playbooks/nc-main-text.yaml`
  - `examples/_journal_art_direction_playbooks/nature-materials-dense.yaml`
  - `examples/_journal_art_direction_playbooks/science-compact.yaml`
  - `examples/_journal_art_direction_playbooks/graphical-abstract-expressive.yaml`
- Added four opt-in paper-wide aesthetic contexts:
  - `examples/_paper_aesthetic_contexts/nc-main-text-series.yaml`
  - `examples/_paper_aesthetic_contexts/nature-materials-dense-series.yaml`
  - `examples/_paper_aesthetic_contexts/science-compact-series.yaml`
  - `examples/_paper_aesthetic_contexts/graphical-abstract-expressive-series.yaml`
- Added `docs/style-pack-catalog.md` to explain pack choice, explicit opt-in,
  interaction with fixture-local `aesthetic_intent.yaml`, and why expressive
  packs must not leak into main-text figures.
- Added `tests/test_style_pack_catalog.py` to load every catalog pack through
  existing parsers and guard main-text versus expressive isolation.

No new schema, global default, figure source edit, export artifact, accepted
state, golden state, or polished-SVG artifact was introduced.
