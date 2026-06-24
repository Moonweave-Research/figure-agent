# Issue 44E - SVG Polish Recipe Dogfood

**Status:** completed with route-precondition caveat
**Fixture:** `fig1_overview_v2_pair_001_vault`
**Date:** 2026-05-25
**Branch:** `codex/issue44-svg-polish-recipe`

## Scope

This dogfood validates the Issue 44 recipe executor, delta pack, and handoff
surface on a real exported SVG. It does not mutate TeX source, generated
exports, accepted state, or golden artifacts.

The available `origin/main` fixture set did not contain a clean
`ready_for_svg_polish` fixture. The only fixture with an explicit
`ready_for_svg_polish` aesthetic trigger, `fig1_overview_v2_pair_001_vault`,
started with:

- `render_state: STALE` at first status check, later `FRESH` after unrelated
  fixture-side edits already present in the worktree;
- `critique_state: STALE`;
- `audit_evidence: needs_action` because `crop_audit_log` was missing required
  visual-clash crop ids;
- `final_artifact_state: NONE` because the fixture currently uses generated
  export final artifact state, not polished-SVG opt-in state.

That means this run proves the toolchain behavior on a real fixture, but it is
not a clean release-route proof that `/fig_driver --mode polish` would proceed
from an already fresh loop checkpoint.

## Recipe Used

Temporary dogfood input:

```yaml
schema: figure-agent.svg-polish-recipe.v1
fixture: fig1_overview_v2_pair_001_vault
source_svg: exports/fig1_overview_v2_pair_001_vault.svg
target_svg: polish/fig1_overview_v2_pair_001_vault.polished.svg
recipe_input_hash: sha256:9e1bfdd28a4b14aad21a51261b561d4882640ea49718a0235248ad74516ca4b0
operations:
  - id: R001
    class: label_micro_position
    selector:
      kind: text_exact
      value: Sulfur-richpolymer
    action:
      type: translate
      dx: 0.6
      dy: -0.4
      unit: px
    rationale: Dogfood a bounded compound-label micro-position polish operation.
    semantic_guard:
      allowed: true
      reason: Moves only the existing sulfur-rich polymer label without changing scientific meaning.
```

The initial selector `text_exact: a` was rejected because dvisvgm produces both
`<text>` and nested `<tspan>` nodes with the same visible text. This is the
desired broad-selector safety behavior. The recipe was narrowed to a unique
compound label.

## Commands And Results

```bash
uv run python3 scripts/status.py examples/fig1_overview_v2_pair_001_vault
```

Result: status was not polish-ready. The first blocker was stale render/stale
critique, followed by tracked-golden and human publication gates.

```bash
uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault \
  --goal "svg polish recipe dogfood" --json
```

Result: loop reported `audit_evidence.evaluation_state: needs_action` and
`crop_audit_log is missing required crop ids`.

```bash
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault \
  --mode polish --goal "svg polish recipe dogfood" --dry-run
```

Result: driver returned `action: run_compile`, not polish handoff, because the
fixture was not fresh.

```bash
uv run python3 scripts/svg_polish_executor.py \
  examples/fig1_overview_v2_pair_001_vault --dry-run
```

Result after CLI fix and selector narrowing:

```text
dry-run: would write polish/fig1_overview_v2_pair_001_vault.polished.svg
dry-run: R001 label_micro_position translate matched=1
```

```bash
uv run python3 scripts/svg_polish_executor.py \
  examples/fig1_overview_v2_pair_001_vault --write --force
```

Result:

```text
wrote polish/fig1_overview_v2_pair_001_vault.polished.svg
```

```bash
PYTHONPATH=scripts uv run python3 - <<'PY'
from pathlib import Path
from svg_polish_delta import build_svg_polish_delta_pack
example = Path("examples/fig1_overview_v2_pair_001_vault")
print(build_svg_polish_delta_pack(example, base_dir=Path(".")).relative_to(example))
PY
```

Result:

```text
polish/aesthetic_delta/delta_manifest.json
```

```bash
uv run python3 scripts/svg_polish_handoff.py \
  examples/fig1_overview_v2_pair_001_vault \
  --reviewer codex-dogfood \
  --editor agent_assisted \
  --toolchain svg_polish_executor.py:recipe-v1 \
  --edit-class label_micro_position \
  --reviewed-at 2026-05-25T10:40:00Z \
  --notes "Issue 44E dogfood: bounded recipe moved one existing label; semantic guard false." \
  --write
```

Result:

```text
wrote polish/svg_polish_audit.md
wrote polish/svg_polish_manifest.yaml
```

```bash
uv run python3 scripts/critique_brief.py \
  examples/fig1_overview_v2_pair_001_vault |
  rg "SVG Polish Aesthetic Delta|before:|after:|diff:|operation_ids|Did journal polish improve|scientific semantics"
```

Result: the critique brief included:

```text
## SVG Polish Aesthetic Delta
- before: `polish/aesthetic_delta/before.png`
- after: `polish/aesthetic_delta/after.png`
- diff: `polish/aesthetic_delta/diff.png`
- operation_ids: R001
- Did journal polish improve?
- Did any scientific semantics change?
```

## Defects Found And Fixed

1. `svg_polish_executor.py --dry-run` was documented but not accepted by the
   CLI. Fixed by adding an explicit no-op `--dry-run` flag and a regression
   test.
2. `svg_polish_executor.py --write` failed after writing when `example_dir` was
   passed as a relative path. Fixed by normalizing both paths before printing
   the fixture-relative output path and adding a regression test.
3. Broad text selector behavior was confirmed: ambiguous text selection is
   rejected instead of silently editing multiple SVG nodes.

## Mutation Check

Generated dogfood artifacts were not staged for commit:

- `examples/fig1_overview_v2_pair_001_vault/polish/svg_polish_recipe.yaml`
- `examples/fig1_overview_v2_pair_001_vault/polish/fig1_overview_v2_pair_001_vault.polished.svg`
- `examples/fig1_overview_v2_pair_001_vault/polish/aesthetic_delta/*`
- `examples/fig1_overview_v2_pair_001_vault/polish/svg_polish_audit.md`
- `examples/fig1_overview_v2_pair_001_vault/polish/svg_polish_manifest.yaml`

No source TeX, generated export, accepted state, or golden artifact was staged
as part of Issue 44E.

## Judgment

The recipe executor, delta pack, critique brief delta surfacing, and handoff
manifest path worked on a real SVG after two CLI usability defects were fixed.
The current fixture set still lacks a clean polish-ready example on this branch,
so future release-route dogfood should start from a fixture whose
`render_state`, `critique_state`, and audit evidence are already fresh.
