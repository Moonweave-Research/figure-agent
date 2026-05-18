---
description: Scaffold critique_adjudication.yaml from critique.md findings without editing source or critique output.
---

Create a conservative adjudication scaffold for one figure.

**Usage**: `/fig_adjudicate <name>`

Run from the plugin root:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <name>
```

To intentionally replace an existing adjudication file:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <name> --force
```

The script reads `examples/<name>/critique.md`, parses YAML frontmatter
findings from both `panels[].findings` and top-level `findings`, and writes
`examples/<name>/critique_adjudication.yaml` with the current
`source_critique_hash`.

Default decisions are conservative:

- findings marked `status: resolved` in `critique.md` become `decision: resolved`;
- all other findings become `decision: needs_human`.

It refuses to overwrite an existing `critique_adjudication.yaml` unless
`--force` is passed. It does not edit `<name>.tex`, `critique.md`, exports,
accepted/golden metadata, or `.scratch/` loop runs.

After scaffold creation, review the decisions manually before using
`decision: apply`. `/fig_loop` only allows patch handoff when exactly one fresh
adjudication decision is `apply`.
