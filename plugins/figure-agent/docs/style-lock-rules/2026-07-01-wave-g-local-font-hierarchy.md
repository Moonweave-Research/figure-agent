# Wave G Style Lock Rule: Local Font Hierarchy

Date: 2026-07-01

Rule id: `style_lock_typography`

Deterministic check:

- `lint_tex.py` warns on local `\tiny`, `\scriptsize`, `\huge`, and `\Huge`
  font-size overrides in fixture source.

Evidence source:

- Wave C style benchmark pack names `style_lock_typography` as a measurable
  check and requires "no new local tiny/scriptsize/huge overrides".
- Wave F comparison packet carries the same measurable check before any
  source, SVG, release, export, or golden mutation is allowed.

Boundary:

- This is not a broad aesthetic score.
- This does not reject human art direction.
- This does not authorize source mutation.
- This only prevents future candidates from bypassing a repeated print-scale
  hierarchy issue with unreviewed local font-size overrides.
