---
description: Scaffold critique_adjudication.yaml from critique.md findings without editing source or critique output.
---

Create a conservative adjudication scaffold for one figure.

**Usage**: `/fig_adjudicate <name>`

Run from the plugin root:

```bash
uv run python3 scripts/critique_lint.py <name>
```

Stop and repair `critique.md` if lint returns non-zero. The lint preflight
catches duplicate finding ids, malformed critique frontmatter, and missing
top-tier finding links before the scaffold can become loop state.
The scaffold command enforces the same critique contract again, so a skipped
or stale lint run cannot promote malformed critique evidence into
`critique_adjudication.yaml`.

```bash
uv run python3 scripts/critique_adjudication.py scaffold <name>
```

To intentionally replace an existing adjudication file:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <name> --force
```

To opt into deterministic policy-assisted adjudication:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <name> --force --policy conservative-v1
```

`conservative-v1` can auto-dismiss accepted simplifications, auto-defer
non-gateable thumbnail polish, and select at most one safe `NIT` local style
finding as `apply`. It does not auto-resolve physics, structural,
target-journal, high-impact, accepted/golden/export, final-artifact, or
semantic-backport questions.

To refresh only the adjudication hash after a freshly regenerated critique:

```bash
uv run python3 scripts/critique_adjudication.py sync <name>
```

`sync` first verifies that `critique.md` is already fresh against the current
`critique_input_hash`, `generator_version`, and `rubric_version`. It refuses
stale critique metadata and tells you to rerun `/fig_critique <name>` instead.
When the existing adjudication has the same finding ids, it preserves the
decisions and updates only `source_critique_hash`. If finding ids changed, use
`scaffold <name> --force` after reviewing that a new decision scaffold is
appropriate.

The script reads `examples/<name>/critique.md`, parses YAML frontmatter
findings from both `panels[].findings` and top-level `findings`, and writes
`examples/<name>/critique_adjudication.yaml` with the current
`source_critique_hash`.

Default decisions are conservative:

- findings marked `status: resolved` in `critique.md` become `decision: resolved`;
- all other findings become `decision: needs_human`.

This default stays unchanged unless `--policy conservative-v1` is passed.
Policy-assisted decisions still validate under the same
`figure-agent.critique-adjudication.v1` schema and remain visible to
`/fig_loop`.

It refuses to overwrite an existing `critique_adjudication.yaml` unless
`--force` is passed. It does not edit `<name>.tex`, `critique.md`, exports,
accepted/golden metadata, or `.scratch/` loop runs.

After scaffold creation, review the decisions manually before using
`decision: apply`. `/fig_loop` only allows patch handoff when exactly one fresh
adjudication decision is `apply`.
