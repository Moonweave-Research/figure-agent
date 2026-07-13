# Fig3 Distribution Shape Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether an attempt-scoped qualitative distribution profile reduces the known Fig3 Panel B shape and encoding failures without encoding unresolved physics or creating a general drawing grammar.

**Architecture:** Add one focused validator/directive compiler for `figure-agent.shape-profile.v1`, then expose it as an optional context-pack input. Bind the profile to a new additive TikZ clean-room attempt and preserve ORRO execution evidence; deterministic gates cover contracts, labels, spacing, text, compilation, and provenance, while curve naturalness remains a named human verdict.

**Tech Stack:** Python 3.11+, pytest, PyYAML, existing Figure Agent context-pack and layout checks, TikZ/LuaLaTeX, ORRO/witnessd/Depone, PDF/PNG review evidence.

---

## Locked boundaries

- Do not edit the maintained `fig3_resistance_mechanism.tex` or any prior attempt.
- Do not import Fig1 snippets, coordinates, selectors, or thresholds.
- Do not add a renderer, path language, curve generator, or automatic aesthetic score.
- Do not encode S60 peak count, Gaussian/symmetric/unimodal topology, monotonic disorder, equal-height/area normalization, or `larger n -> slower decay`.
- Use only `increasing sulfur content` as the composition header.
- Machine-valid and ORRO proofcheck do not mean publication acceptance.

### Task 1: Validate a minimal experimental shape profile

**Files:**
- Create: `plugins/figure-agent/scripts/shape_profile.py`
- Create: `plugins/figure-agent/tests/test_shape_profile.py`

- [ ] **Step 1: Write the failing happy-path test**

```python
from scripts.shape_profile import compile_shape_profile


def test_compiles_bounded_distribution_relations() -> None:
    payload = {
        "schema": "figure-agent.shape-profile.v1",
        "status": "experimental_attempt_scoped",
        "objects": [
            {"id": "s60", "role": "discrete_distribution"},
            {"id": "s80", "role": "continuous_broad_distribution"},
        ],
        "relations": [
            {"kind": "wider_than", "subject": "s80", "object": "s60"},
            {"kind": "same_encoding_family", "members": ["s60", "s80"]},
        ],
        "forbidden_claims": ["fixed_peak_count", "monotonic_disorder", "decay_direction"],
        "composition_header": "increasing sulfur content",
    }

    result = compile_shape_profile(payload)

    assert result["authoring_directives"] == [
        "Render [s80] visibly wider in energy than [s60].",
        "Use one shared outline, fill, and stroke encoding family for [s60, s80].",
        "Use composition header [increasing sulfur content] without a curve-to-curve causal arrow.",
        "Do not assert unresolved claims [fixed_peak_count, monotonic_disorder, decay_direction].",
    ]
```

- [ ] **Step 2: Run the test and verify RED**

Run: `uv run pytest -q tests/test_shape_profile.py::test_compiles_bounded_distribution_relations`

Expected: FAIL because `scripts.shape_profile` does not exist.

- [ ] **Step 3: Implement the validator and directive compiler**

Create immutable validation around these exact allowed values:

```python
SCHEMA = "figure-agent.shape-profile.v1"
STATUS = "experimental_attempt_scoped"
ALLOWED_ROLES = {"discrete_distribution", "continuous_broad_distribution"}
ALLOWED_RELATIONS = {"wider_than", "same_encoding_family"}
FORBIDDEN_CLAIMS = {"fixed_peak_count", "monotonic_disorder", "decay_direction"}
REQUIRED_HEADER = "increasing sulfur content"


class ShapeProfileError(ValueError):
    pass


def compile_shape_profile(payload: dict[str, object]) -> dict[str, object]:
    """Validate one experimental qualitative shape profile and emit directives."""
```

Reject duplicate IDs, unknown relation endpoints, missing required relations,
extra forbidden-claim vocabulary, any other header, or any field named
`coordinates`, `control_points`, `gaussian`, `peak_count`, `normalization`, or
`threshold` at any nesting depth. Return the normalized input plus the four
directives asserted above.

- [ ] **Step 4: Add negative tests**

Parametrize invalid payloads for unknown object IDs, `peak_count`, a disorder
header, missing shared encoding, and absent `decay_direction` guard. Each must
raise `ShapeProfileError` with a stable message.

- [ ] **Step 5: Run focused tests and static checks**

Run:

```bash
uv run pytest -q tests/test_shape_profile.py
uv run ruff check scripts/shape_profile.py tests/test_shape_profile.py
git diff --check
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add plugins/figure-agent/scripts/shape_profile.py plugins/figure-agent/tests/test_shape_profile.py
git commit -m "feat: validate experimental shape profiles"
```

### Task 2: Inject a selected profile into context-pack

**Files:**
- Modify: `plugins/figure-agent/scripts/authoring_context_pack.py`
- Modify: `plugins/figure-agent/bin/fig-agent`
- Modify: `plugins/figure-agent/tests/test_authoring_context_pack.py`

- [ ] **Step 1: Write a failing context-pack test**

Create a temporary fixture-local `shape_profile.yaml`, call:

```python
payload = build_context_pack(
    "context_demo",
    plugin_root=plugin_root,
    shape_profile="shape_profile.yaml",
)
```

Assert `payload["shape_profile"]["schema"]`, its relative path and SHA-256,
and the four directives from Task 1. Assert the existing context pack is
unchanged when no profile is selected.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `uv run pytest -q tests/test_authoring_context_pack.py -k shape_profile`

Expected: FAIL because `build_context_pack` has no `shape_profile` argument.

- [ ] **Step 3: Implement safe fixture-relative loading**

Reuse the existing layout-contract path boundary: reject absolute paths,
`..`, symlinks, missing files, and paths outside the fixture. Load YAML, call
`compile_shape_profile`, and expose:

```python
{
    "path": relative.as_posix(),
    "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
    "schema": "figure-agent.shape-profile.v1",
    "status": "experimental_attempt_scoped",
    "objects": compiled["objects"],
    "relations": compiled["relations"],
    "forbidden_claims": compiled["forbidden_claims"],
    "composition_header": compiled["composition_header"],
    "authoring_directives": compiled["authoring_directives"],
}
```

- [ ] **Step 4: Add the CLI option**

Add `--shape-profile FIXTURE_RELATIVE_PATH` to both
`scripts/authoring_context_pack.py` and `bin/fig-agent context-pack`, forwarding
it exactly once. Do not select a profile implicitly from `spec.yaml`.

- [ ] **Step 5: Verify GREEN and backward compatibility**

Run:

```bash
uv run pytest -q tests/test_shape_profile.py tests/test_authoring_context_pack.py
uv run ruff check scripts/shape_profile.py scripts/authoring_context_pack.py tests/test_shape_profile.py tests/test_authoring_context_pack.py
git diff --check
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add plugins/figure-agent/bin/fig-agent plugins/figure-agent/scripts/authoring_context_pack.py plugins/figure-agent/tests/test_authoring_context_pack.py
git commit -m "feat: inject attempt-scoped shape profiles"
```

### Task 3: Bind the Fig3 profile and clean-room input packet

**Files:**
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/shape_profile_panel_b.yaml`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/shape_profile_authority_packet.yaml`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/shape_profile_authoring_prompt.md`
- Modify: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/scope_protection.yaml`
- Modify: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/input_packet.yaml`
- Modify: `plugins/figure-agent/tests/test_fig3_resistance_failure_first.py`

- [ ] **Step 1: Write failing fixture tests**

Assert the profile matches the Task 1 schema, contains only the two allowed
relations and three unresolved-claim guards, and hashes into the authority
packet. Assert one shared control packet binds the maintained
briefing/spec/contract/goals, the existing text/ownership/clearance contracts,
one explicit model ID, one token budget, and one blank starting-artifact hash.
Assert a treatment overlay adds only the profile hash and directives. Both must
forbid every previous generated source, render, Fig1 path, and historical Fig3
implementation.

- [ ] **Step 2: Run the fixture test and verify RED**

Run: `uv run pytest -q tests/test_fig3_resistance_failure_first.py -k shape_profile`

Expected: FAIL because the profile and packet do not exist.

- [ ] **Step 3: Create the profile and context pack**

Use the exact payload from Task 1. Generate the context pack with:

```bash
uv run python bin/fig-agent context-pack fig3_resistance_mechanism \
  --layout-contract review/failure-first/region_guided_text_inventory_contract.yaml \
  --shape-profile shape_profile_panel_b.yaml --json
```

Copy only the emitted directives and bound hashes into the treatment overlay.
Create two prompts from the same control packet: `shape_control` contains no
shape-profile directives; `shape_profiled` adds exactly the emitted profile
directives. Both request a new standalone TikZ source, one pass, no prior
generated-artifact inspection, no manual repair, and no publication claim.

- [ ] **Step 4: Update scope hashes and verify GREEN**

Recompute the SHA-256 for `scope_protection.yaml` and update only its bound
entry in `input_packet.yaml`.

Run:

```bash
uv run pytest -q tests/test_fig3_resistance_failure_first.py -k shape_profile
git diff --check
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/examples/fig3_resistance_mechanism plugins/figure-agent/tests/test_fig3_resistance_failure_first.py
git commit -m "test: bind Fig3 shape profile experiment"
```

### Task 4: Execute a controlled two-arm clean generation through ORRO

**Files:**
- Create: `.witnessd/runs/fig3-shape-profile-*` locally; do not commit keys
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/shape_control_generated.tex`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/shape_profiled_generated.tex`
- Create after render: per-arm PDF, PNG, transcript, and render receipt

- [ ] **Step 1: Compile the ORRO workflow plan**

Run `orro delegate -- flowplan` with two isolated author lanes and one verifier
lane. Both author lanes use the same adapter/model, budget, blank starting
artifact, and control packet. The control lane may write only
`shape_control_generated.tex`; the treatment lane receives the additional
profile overlay and may write only `shape_profiled_generated.tex`. The verifier
lane compiles and reports but does not repair source.

- [ ] **Step 2: Run witnessd once**

Run `orro delegate -- proofrun` with the compiled workflow plan, local
`.witnessd`, explicit `--allow` for the two new sources only, and fail-fast
enabled. Preserve the run directory and command receipt. If either authoring or
compilation lane fails, preserve both arm states and skip source repair; do not
silently compare a successful arm with a missing arm.

- [ ] **Step 3: Compile from the required working directory**

From `plugins/figure-agent` run:

```bash
for arm in shape_control shape_profiled; do
  bash scripts/compile.sh "examples/fig3_resistance_mechanism/review/failure-first/${arm}_generated.tex"
  set +e
  FIGURE_AGENT_STRICT=1 bash scripts/compile.sh "examples/fig3_resistance_mechanism/review/failure-first/${arm}_generated.tex"
  printf '%s strict_exit=%s\n' "$arm" "$?"
  set -e
done
```

Record the strict exit code and named findings. Do not convert a strict failure
into a pass by editing the generated source.

- [ ] **Step 4: Run existing layout reports**

Evaluate text budgets, Panel B label ownership, and S60/S80 label clearance
against both new PDFs using `scripts/checks/check_layout_drift.py`. Store
arm-specific reports without overwriting prior reports.

- [ ] **Step 5: Run Depone verification**

Run `orro delegate -- proofcheck --home .witnessd <run-dir>` and preserve
`proofcheck-verdict.json`. A passing verdict verifies persisted execution
evidence only.

- [ ] **Step 6: Commit only repository artifacts**

Do not stage `.witnessd/keys`. Stage the new source, render outputs, transcript,
receipts, and reports only after their hashes are bound by Task 5.

### Task 5: Bind outcome and prepare human review

**Files:**
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/shape_profile_comparison.yaml`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/shape_profile_adversarial_review.yaml`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/shape_profile_handoff.md`
- Modify: `plugins/figure-agent/tests/test_fig3_resistance_failure_first.py`
- Modify: `plugins/figure-agent/docs/execution-plan.md`

- [ ] **Step 1: Write failing receipt tests**

Require both sources, prompts, transcripts, PDFs, PNGs, layout reports, the
shared input/model/budget/start hashes, profile overlay hash, ORRO run receipt,
and Depone verdict hash. Require:

```yaml
comparison_eligibility: controlled_shape_profile_experiment_not_product_ablation
shape_naturalness: pending_human_review
publication_acceptance: not_claimed
```

- [ ] **Step 2: Create the additive attempt manifest and adversarial review**

Record machine findings separately from unresolved scientific claims and human
visual questions. The review must ask whether the two distributions share one
encoding family, whether S80 reads wider without implying a measured function,
whether `n` and `rho_60s` remain distinct, and whether the panel looks suitable
for a contemporary paper.

- [ ] **Step 3: Run ORRO handoff and report**

After proofcheck exists, run:

```bash
orro delegate -- handoff <run-dir> --out <run-dir>/handoff.json --json
orro delegate -- report <run-dir> --home .witnessd --out <run-dir>/report.json --json
```

Copy only non-secret evidence paths and verdict summaries into the repository
handoff. Do not describe the report as assurance or publication approval.

- [ ] **Step 4: Verify the complete slice**

Run:

```bash
uv run pytest -q tests/test_shape_profile.py tests/test_authoring_context_pack.py tests/test_fig3_resistance_failure_first.py tests/test_generation_receipt.py tests/test_failure_ablation.py
uv run ruff check scripts/shape_profile.py scripts/authoring_context_pack.py tests/test_shape_profile.py tests/test_authoring_context_pack.py
uv run ruff check --select I tests/test_fig3_resistance_failure_first.py
git diff --check
```

Expected: all pass; human verdict remains pending unless the named reviewer has
actually reviewed the new render.

- [ ] **Step 5: Commit**

```bash
git add plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first plugins/figure-agent/tests/test_fig3_resistance_failure_first.py plugins/figure-agent/docs/execution-plan.md
git commit -m "test: run bounded Fig3 shape profile experiment"
```

## Stop condition

Stop at `pending_human_review` after producing a reproducible review packet.
Do not promote the profile, infer correction minutes, modify the attempt, or
claim publication acceptance. A future promotion decision requires a second
materially different figure family and a second backend under the product spec.
