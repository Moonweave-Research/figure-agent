# Issue 16: Editorial Illustration Quality Roadmap

**Date:** 2026-05-21 KST
**Status:** implemented through Issue 16B
**Type:** parent issue / implementation backlog
**Primary spec:** `../specs/2026-05-21-editorial-art-direction-audit-design.md`

## Problem

The plugin can now drive technical quality loops, but top-tier manuscript
illustrations need an additional editorial layer. The remaining question is
not only "is the figure correct?" It is "does the figure have the visual
authority, focal structure, narrative choreography, and polish path expected
from a high-impact journal illustration?"

## Direction

Keep `figure-agent` as a quality kernel, not an autonomous illustrator.
Strengthen the audit contract first, then route SVG polish only after the
figure has a clear art-direction diagnosis.

## Issue Breakdown

### Issue 16A: Editorial Art-Direction Audit v1.5

**Status:** implemented in `a9368e9`

Add `editorial_art_direction` to the critique contract. This forces host
critique to evaluate hero focus, visual narrative, illustration readiness,
abstraction consistency, reference-class fit, visual identity, claim payload,
aesthetic risk, TikZ-vs-SVG polish trigger, and human art-direction gate.

No SVG routing or mutation is included in 16A.

### Issue 16B: SVG Polish Trigger Routing

**Status:** implemented

After 16A lands and is dogfooded, teach `/fig_loop` and
`/fig_drive --mode polish` to consume
`editorial_art_direction.tikz_vs_svg_polish_trigger`.

The goal is to distinguish:

- continue TikZ source repair;
- ready for controlled SVG polish;
- needs human art direction;
- semantic backport required before polish can count.

See `2026-05-21-issue-16b-svg-polish-trigger-routing.md` for the concrete
loop summary and driver routing contract.

## Non-Goals

- No automatic illustration generation.
- No hidden SVG editing.
- No accepted/golden/final-artifact promotion.
- No guarantee of Nature or Science acceptance.
- No migration of existing examples without a future issue.
