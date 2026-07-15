<!-- FIGURE_AGENT:LEGACY_EVIDENCE -->
# Authoring Execution Binding Implementation Plan

**Status:** Historical evidence — non-authoritative.

**Superseded by:** `docs/figure-agent.md`.

**Execution warning:** Everything below this boundary is quoted historical
evidence. Its instructions and unchecked tasks MUST NOT be executed as the
current plan; any internal authority language is superseded by
`docs/figure-agent.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a Figure Agent authoring packet the byte-exact prompt authority for ORRO execution, then bind the actual prompt, transcript, generated source, and touched-file scope in additive receipts before any Fig3 comparison is considered eligible.

**Architecture:** Keep `authoring_context_pack.py` read-only and add a separate deterministic execution-packet compiler that consumes its payload. Add one pair preflight and one post-run receipt writer; neither component calls a model. ORRO/witnessd executes the packet-owned prompt, Depone verifies persisted execution evidence, and human review remains the only visual/publication verdict.

**Tech Stack:** Python 3.11+, pytest, PyYAML, existing Figure Agent CLI/runtime paths, SHA-256 canonical JSON, TikZ/LuaLaTeX, ORRO/witnessd/Depone.

---

**Authority boundary:** This is a subordinate implementation checklist for the approved design at `docs/superpowers/specs/2026-07-13-authoring-execution-binding-design.md`. `docs/product-spec.md` and `docs/execution-plan.md` remain the single product and forward-execution authorities.

## File map

- `scripts/authoring_execution_packet.py`: compile and write immutable packet/prompt pairs from a context pack.
- `scripts/authoring_execution_preflight.py`: reject drift or unequal two-arm execution contracts before ORRO.
- `scripts/authoring_execution_receipt.py`: bind actual prompt, transcript, source, touched files, and runtime observations after ORRO.
- `bin/fig-agent`: expose `authoring-packet`, `authoring-preflight`, and `authoring-receipt` without embedding contract logic.
- `tests/test_authoring_execution_packet.py`: packet, path, hash, prompt, and CLI contract tests.
- `tests/test_authoring_execution_receipt.py`: post-run evidence binding and negative tests.
- `tests/test_fig3_resistance_failure_first.py`: additive fixture-level experiment invariants.
- `examples/fig3_resistance_mechanism/review/failure-first/execution-binding-vN/`: versioned packets, prompts, generated sources, receipts, and review artifacts; every prior attempt remains immutable.

### Task 1: Compile an immutable byte-exact authoring packet

**Files:**
- Create: `plugins/figure-agent/scripts/authoring_execution_packet.py`
- Create: `plugins/figure-agent/tests/test_authoring_execution_packet.py`

- [ ] **Step 1: Write the failing canonical packet test**

Create a temporary fixture containing `spec.yaml`, a regular blank-start file,
a regular budget contract, and the Style Lock file required by the existing
context-pack compiler. Exercise this public API:

```python
packet, prompt = compile_authoring_execution_packet(
    "context_demo",
    plugin_root=plugin_root,
    workspace_root=plugin_root,
    model_id="gpt-5.5",
    budget_contract="examples/context_demo/review/budget.yaml",
    blank_start="examples/context_demo/review/blank.txt",
    output_path="examples/context_demo/review/failure-first/execution-binding-v1/control_generated.tex",
)
```

Assert:

```python
assert packet["schema"] == "figure-agent.authoring-execution-packet.v1"
assert packet["prompt"]["utf8"] == prompt
assert packet["prompt"]["sha256"] == sha256_text(prompt)
assert packet["mandatory_source_requirements"] == [
    r"\documentclass[tikz,border=4pt]{standalone}",
    r"\usepackage{tikz}",
    r"\usepackage{polymer-paper-preamble}",
]
assert packet["packet_sha256"] == canonical_packet_sha256(packet)
```

- [ ] **Step 2: Run the test and confirm RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_authoring_execution_packet.py::test_compiles_canonical_packet_and_prompt
```

Expected: collection fails because `authoring_execution_packet` does not exist.

- [ ] **Step 3: Implement canonical hashing and safe input loading**

Implement these exact public constants and helpers:

```python
SCHEMA = "figure-agent.authoring-execution-packet.v1"
MANDATORY_SOURCE_REQUIREMENTS = (
    r"\documentclass[tikz,border=4pt]{standalone}",
    r"\usepackage{tikz}",
    r"\usepackage{polymer-paper-preamble}",
)

class AuthoringExecutionPacketError(ValueError):
    pass

def canonical_packet_sha256(packet: dict[str, object]) -> str:
    payload = {key: value for key, value in packet.items() if key != "packet_sha256"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
```

All selected files must be repository-relative regular files. Reject absolute
paths, empty or `.`/`..` components, symlinks at any path component, missing
files, and resolved paths outside `workspace_root`. Require the output under
`examples/<fixture>/review/failure-first/execution-binding-vN/`, ending in
`.tex`, and absent when the packet is written.

- [ ] **Step 4: Render the prompt in one fixed order**

`render_authoring_prompt(...)` must emit UTF-8 text with a final newline in
this order: output/one-attempt rule; mandatory source requirements; semantic
contracts and forbidden implications; layout directives; optional shape
profile directives; provenance/publication boundary. Include every mandatory
source string literally. Record the context-pack hash from canonical JSON, the
budget and blank-start hashes from bytes, optional layout/profile hashes, the
model ID, `feedback_rounds: 0`, `manual_repairs: 0`, and
`publication_acceptance: not_claimed`.

- [ ] **Step 5: Write packet and prompt once**

Implement:

```python
def write_authoring_execution_packet(
    packet_path: Path,
    prompt_path: Path,
    *,
    packet: dict[str, object],
    prompt: str,
) -> None:
    ...
```

Require adjacent packet/prompt paths inside the attempt directory, reject
existing outputs, write JSON with sorted keys plus one final newline, and
re-read both files to prove their bytes and hashes before returning.

- [ ] **Step 6: Add negative tests**

Cover absolute paths, `..`, intermediate symlinks, output outside the attempt
directory, duplicate mandatory requirements, prompt missing the preamble,
packet hash drift, prompt drift, and a second write to existing files. Each
case must raise `AuthoringExecutionPacketError` with a stable diagnostic.

- [ ] **Step 7: Verify and commit**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_authoring_execution_packet.py
uv run ruff check scripts/authoring_execution_packet.py tests/test_authoring_execution_packet.py
git diff --check
```

Expected: all pass.

Commit:

```bash
git add plugins/figure-agent/scripts/authoring_execution_packet.py plugins/figure-agent/tests/test_authoring_execution_packet.py
git commit -m "feat: compile bound authoring execution packets"
```

### Task 2: Expose packet generation and two-arm preflight

**Files:**
- Create: `plugins/figure-agent/scripts/authoring_execution_preflight.py`
- Modify: `plugins/figure-agent/bin/fig-agent`
- Modify: `plugins/figure-agent/tests/test_authoring_execution_packet.py`

- [ ] **Step 1: Write failing CLI and pair-preflight tests**

Invoke `bin/fig-agent authoring-packet` twice with the same model, budget,
blank start, layout contract, and distinct output paths. The treatment call
also selects `--shape-profile shape_profile_panel_b.yaml`. Assert the JSON and
written prompt contain identical bytes and hashes. Then call:

```python
result = preflight_authoring_pair(control_packet_path, treatment_packet_path)
assert result["schema"] == "figure-agent.authoring-execution-preflight.v1"
assert result["decision"] == "pass"
```

- [ ] **Step 2: Run focused tests and confirm RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_authoring_execution_packet.py -k "cli or preflight"
```

Expected: fail because the CLI commands and preflight module do not exist.

- [ ] **Step 3: Add `authoring-packet` CLI forwarding**

Add these required options to the CLI only; keep all validation in the module:

```text
fig-agent authoring-packet NAME
  --model-id MODEL
  --budget-contract REPO_RELATIVE_PATH
  --blank-start REPO_RELATIVE_PATH
  --output-path REPO_RELATIVE_PATH
  --packet-out REPO_RELATIVE_PATH
  --prompt-out REPO_RELATIVE_PATH
  [--layout-contract FIXTURE_RELATIVE_PATH]
  [--shape-profile FIXTURE_RELATIVE_PATH]
  --json
```

The command writes the pair once and prints the persisted packet JSON. It never
calls a model or edits a generated source.

- [ ] **Step 4: Implement pair preflight**

`preflight_authoring_pair` must revalidate both packet hashes and prompt bytes,
then require equal model IDs, budget hashes, blank-start hashes, mandatory
requirements, context-pack schema, feedback rounds, and manual-repair counts.
Require distinct packet, prompt, and generated-source paths. The only allowed
arm difference is the selected shape-profile payload/directives and the
corresponding prompt/output hashes.

Return a JSON-serializable report containing both packet/prompt hashes,
`filesystem_read_isolation: unavailable`, and `decision: pass`. Raise
`AuthoringExecutionPreflightError` before execution for every mismatch.

- [ ] **Step 5: Add `authoring-preflight` CLI and negative tests**

Add:

```text
fig-agent authoring-preflight --control PACKET --treatment PACKET --json
```

Test unequal model, unequal budget, unequal blank start, reused output path,
prompt byte drift, packet field drift, and a treatment difference outside the
allowed profile fields.

- [ ] **Step 6: Verify and commit**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_authoring_execution_packet.py
uv run ruff check scripts/authoring_execution_packet.py scripts/authoring_execution_preflight.py tests/test_authoring_execution_packet.py
git diff --check
```

Expected: all pass.

Commit:

```bash
git add plugins/figure-agent/bin/fig-agent plugins/figure-agent/scripts/authoring_execution_preflight.py plugins/figure-agent/tests/test_authoring_execution_packet.py
git commit -m "feat: preflight bound authoring arms"
```

### Task 3: Bind actual runtime evidence in an additive receipt

**Files:**
- Create: `plugins/figure-agent/scripts/authoring_execution_receipt.py`
- Create: `plugins/figure-agent/tests/test_authoring_execution_receipt.py`
- Modify: `plugins/figure-agent/bin/fig-agent`

- [ ] **Step 1: Write the failing receipt test**

Create regular packet, prompt, transcript, and source files plus an ORRO touched
files JSON list. Exercise:

```python
receipt = record_authoring_execution_receipt(
    packet_path=packet_path,
    prompt_path=prompt_path,
    transcript_path=transcript_path,
    generated_source_path=source_path,
    touched_files_path=touched_files_path,
    receipt_path=receipt_path,
    actual_model_id="gpt-5.5",
    actual_token_usage=None,
    token_usage_unavailable_reason="adapter_did_not_report_usage",
    forbidden_input_audit="no_forbidden_path_observed_in_transcript",
)
```

Assert schema `figure-agent.authoring-execution-receipt.v1`, hashes for all four
artifacts, exact prompt equality, the packet hash, one declared touched file,
zero feedback/manual repairs, unavailable read isolation, and publication
acceptance not claimed.

- [ ] **Step 2: Run the test and confirm RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_authoring_execution_receipt.py
```

Expected: collection fails because the receipt module does not exist.

- [ ] **Step 3: Implement strict evidence binding**

Re-use packet validation. Require all evidence paths to be regular, non-symlink
repository files. Require actual model equality, exact prompt bytes, generated
source at the packet-declared output, and touched files equal to a one-element
list containing only that output. Require either a non-negative integer token
usage or a non-empty unavailable reason, never both. Record transcript audit as
an observation, not proof of filesystem read isolation.

Reject an existing receipt and re-read the JSON after writing to prove its
canonical hash. Do not write or synthesize the transcript.

- [ ] **Step 4: Add receipt negative tests and CLI**

Cover model mismatch, prompt mismatch, source path mismatch, extra touched
files, missing source, symlinked transcript, ambiguous token usage, and an
existing receipt. Expose the same arguments through
`fig-agent authoring-receipt`; the CLI prints persisted JSON only.

- [ ] **Step 5: Verify and commit**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_authoring_execution_receipt.py tests/test_authoring_execution_packet.py
uv run ruff check scripts/authoring_execution_packet.py scripts/authoring_execution_preflight.py scripts/authoring_execution_receipt.py tests/test_authoring_execution_packet.py tests/test_authoring_execution_receipt.py
git diff --check
```

Expected: all pass.

Commit:

```bash
git add plugins/figure-agent/bin/fig-agent plugins/figure-agent/scripts/authoring_execution_receipt.py plugins/figure-agent/tests/test_authoring_execution_receipt.py
git commit -m "feat: bind authoring runtime receipts"
```

### Task 4: Prepare a fresh additive Fig3 execution-binding experiment

**Files:**
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v1/budget_contract.yaml`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v1/blank_start.txt`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v1/control_packet.json`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v1/control_prompt.md`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v1/treatment_packet.json`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v1/treatment_prompt.md`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v1/preflight.json`
- Modify: `plugins/figure-agent/tests/test_fig3_resistance_failure_first.py`

- [ ] **Step 1: Write failing additive-fixture tests**

Require the new directory and forbid mutation of every historical
`shape_control_*` and `shape_profiled_*` artifact by asserting their committed
hashes. Require both packets to bind the same context sources, model, budget,
blank start, and zero-repair contract. Require only the treatment packet to
bind `shape_profile_panel_b.yaml`. Require both prompts to contain the exact
mandatory preamble string.

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig3_resistance_failure_first.py -k execution_binding
```

Expected: fail because the additive packet directory does not exist.

- [ ] **Step 3: Create contracts and generate both packet/prompt pairs**

Use the same explicit model ID and one-pass token budget for both arms. Generate
the control packet without a profile and the treatment packet with
`--shape-profile shape_profile_panel_b.yaml`; both select the same existing
layout contract and blank start. Do not hand-edit emitted prompt files.

- [ ] **Step 4: Persist preflight evidence**

Run `fig-agent authoring-preflight` and write its JSON output to
`execution-binding-v1/preflight.json`. If it fails, preserve the failure and
repair only the compiler/configuration, never the historical generated source.

- [ ] **Step 5: Verify and commit**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig3_resistance_failure_first.py -k execution_binding
git diff --check
```

Expected: all pass.

Commit:

```bash
git add plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v1 plugins/figure-agent/tests/test_fig3_resistance_failure_first.py
git commit -m "test: bind fresh Fig3 authoring prompts"
```

### Task 5: Execute exact prompt bytes through ORRO and stop at human review

**Execution amendment:** The v1 packet passed byte/hash preflight but was
blocked before model execution because the rendered prompt omitted the binding
fixture briefing and panel narrative. Preserve v1 as negative control-plane
evidence. Task 5 executes the corrected, additive `execution-binding-v2`
packet only.

**Files:**
- Create locally: `.witnessd/plans/fig3-execution-binding.roles.json`
- Create locally: `.witnessd/plans/fig3-execution-binding.workflow.json`
- Create locally: `.witnessd/runs/fig3-execution-binding-*`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v2/control_generated.tex`
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v2/treatment_generated.tex`
- Create: per-arm transcript, touched-files JSON, receipt, compile logs, PDF, and PNG in the same additive directory
- Create: `plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v2/review_handoff.md`
- Modify: `plugins/figure-agent/tests/test_fig3_resistance_failure_first.py`

- [ ] **Step 1: Initialize and compile the ORRO workflow**

Run from the isolated worktree root:

```bash
orro delegate -- init --home .witnessd --repo . --depone-root /Users/choemun-yeong/.local/share/orro/engines/Depone
orro delegate -- flowplan \
  --root . \
  --lane-adapter codex \
  --role-lane-tier frontier \
  --out .witnessd/plans/fig3-execution-binding.workflow.json \
  --role-lanes-out .witnessd/plans/fig3-execution-binding.roles.json \
  "Execute the approved authoring-execution-binding plan task by task; author lanes must consume the persisted control_prompt.md and treatment_prompt.md bytes exactly and may write only their declared generated TeX source."
```

Inspect the role plan. If it contains inline paraphrased authoring instructions,
replace the role-plan input mechanism with an exact file-byte handoff before
proofrun; do not accept a semantically similar prompt.

- [ ] **Step 2: Run witnessd with disjoint write scopes**

Run `orro delegate -- proofrun` with the persisted workflow/role-lane plans,
`--fail-fast`, and explicit `--allow` entries only for the plan-declared code,
tests, additive fixture directory, and non-secret `.witnessd` evidence. Preserve
the observer receipt and run log. witnessd executes; ORRO only exposes the
workflow.

- [ ] **Step 3: Bind each actual execution**

For each arm, use the real ORRO transcript and touched-files record with
`fig-agent authoring-receipt`. If ORRO used bytes different from the prompt
file, record `execution_unbound` and do not compile that arm. Never synthesize a
clean transcript after the fact.

- [ ] **Step 4: Compile eligible sources without repair**

From `plugins/figure-agent` run:

```bash
bash scripts/compile.sh examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v2/control_generated.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v2/control_generated.tex
bash scripts/compile.sh examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v2/treatment_generated.tex
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v2/treatment_generated.tex
```

Preserve normal and strict exit codes/logs. A generated source missing the
mandatory preamble remains immutable negative evidence.

- [ ] **Step 5: Run Depone proofcheck and ORRO handoff/report**

Run:

```bash
orro delegate -- proofcheck --home .witnessd --out <run-dir>/proofcheck-verdict.json --json <run-dir>
orro delegate -- handoff --out <run-dir>/handoff.json --json <run-dir>
orro delegate -- report --home .witnessd --out <run-dir>/report.json --json <run-dir>
```

Depone verifies persisted execution evidence only. A pass does not establish
visual quality, scientific correctness, or publication acceptance.

- [ ] **Step 6: Write fixture tests for the final evidence state**

Require packet/prompt/transcript/source/touched-files/receipt hashes, compile
receipts where eligible, and the Depone verdict hash. The handoff must record
one of:

```yaml
execution_state: execution_unbound
comparison_eligibility: ineligible
```

or:

```yaml
execution_state: bound
comparison_eligibility: review_ready
shape_naturalness: pending_human_review
publication_acceptance: not_claimed
```

- [ ] **Step 7: Verify the complete implementation**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_authoring_execution_packet.py tests/test_authoring_execution_receipt.py tests/test_authoring_context_pack.py tests/test_fig3_resistance_failure_first.py tests/test_generation_receipt.py tests/test_failure_ablation.py
uv run ruff check scripts/authoring_execution_packet.py scripts/authoring_execution_preflight.py scripts/authoring_execution_receipt.py tests/test_authoring_execution_packet.py tests/test_authoring_execution_receipt.py
uv run ruff check --select I tests/test_fig3_resistance_failure_first.py
git diff --check
```

Expected: all pass. If both sources render, stop at
`shape_naturalness: pending_human_review`.

- [ ] **Step 8: Commit repository evidence only**

Do not stage `.witnessd/keys`, Codex auth/config databases, or unrelated run
state. Stage only source-controlled code/tests and the additive Fig3 artifacts
whose hashes are bound in receipts.

```bash
git add plugins/figure-agent/bin/fig-agent plugins/figure-agent/scripts plugins/figure-agent/tests plugins/figure-agent/examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v2
git commit -m "test: execute bound Fig3 authoring experiment"
```

## Stop condition

The implementation stops when the packet compiler, pair preflight, receipt
binding, targeted tests, ORRO execution evidence, and Depone proofcheck are
persisted. If renderable, the outcome is only `review_ready`; a named human must
judge shape naturalness and contemporary-paper suitability before any product
promotion or publication claim.

## Execution amendment: bind the repository-to-plugin working directory

The first `execution-binding-v2` control proofrun exposed a path-frame defect.
The packet output was relative to the Figure Agent plugin workspace, while the
ORRO lane launched the model at the repository worktree root. The model created
exactly one source, but at repository-root `examples/...` rather than
`plugins/figure-agent/examples/...`. The lane also reached the fixed adapter
timeout and ORRO correctly reported `blocked-explicit`.

Preserve the v2 source and evidence as immutable negative evidence. Do not move,
repair, compile, or compare that source, and do not execute the v2 treatment arm.
`execution-binding-v3` must add one equal-arm `execution_cwd` contract, bind it
into the exact prompt bytes and packet hash, and instruct the model to change
from the repository root into `plugins/figure-agent` before resolving the
plugin-relative output path. Only v3 is eligible for execution and comparison.
