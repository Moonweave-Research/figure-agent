# Boundary Handoff Dogfood Evidence

Date: 2026-05-29

Related issue:
`docs/superpowers/issues/2026-05-29-issue-70b-mechanical-boundary-handoff-packet.md`

Status: completed

## Goal

Verify that `/fig_run` boundary handoff packets are useful in live fixture
states without enabling hidden execution, source mutation, export mutation, or
release/accepted/golden mutation.

## Fixture Queue

Eight spec-backed fixtures were checked:

- `fig1_overview_v2`
- `fig1_overview_v2_pair_001_vault`
- `fig3_trapping_concept`
- `fig5_floating_clip_mechanism`
- `golden_trap_depth_picture`
- `n3_trial_01_trap_depth`
- `n3_trial_02_actuation_sequence`
- `smoke_trap_demo`

The dogfood used plan mode only. No run used `--execute`.

## Commands

Review-mode sweep:

```bash
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

root = Path("plugins/figure-agent")
fixtures = sorted(p.name for p in (root / "examples").iterdir() if (p / "spec.yaml").exists())

for name in fixtures:
    proc = subprocess.run(
        [
            "uv",
            "run",
            "python3",
            "scripts/fig_run.py",
            name,
            "--mode",
            "review",
            "--goal",
            "boundary-handoff-dogfood",
            "--max-steps",
            "3",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(proc.stdout)
    handoff = payload.get("boundary_handoff") or {}
    print(name, payload.get("final_action"), handoff.get("required_actor"))
PY
```

Mode sweep and contract assertions:

```bash
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

root = Path("plugins/figure-agent")
fixtures = sorted(p.name for p in (root / "examples").iterdir() if (p / "spec.yaml").exists())
modes = ["authoring", "review", "release", "polish"]

non_complete = 0
complete = 0
actor_counts = {}
action_counts = {}
violations = []

for name in fixtures:
    for mode in modes:
        proc = subprocess.run(
            [
                "uv",
                "run",
                "python3",
                "scripts/fig_run.py",
                name,
                "--mode",
                mode,
                "--goal",
                "boundary-handoff-dogfood",
                "--max-steps",
                "3",
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode:
            violations.append(f"{name}/{mode}: returncode {proc.returncode}: {proc.stderr.strip()}")
            continue

        payload = json.loads(proc.stdout)
        action = payload.get("final_action")
        action_counts[action] = action_counts.get(action, 0) + 1
        handoff = payload.get("boundary_handoff")

        if action == "complete":
            complete += 1
            if handoff is not None:
                violations.append(f"{name}/{mode}: complete payload unexpectedly has boundary_handoff")
            continue

        non_complete += 1
        if not isinstance(handoff, dict):
            violations.append(f"{name}/{mode}: non-complete payload missing boundary_handoff")
            continue

        actor = handoff.get("required_actor")
        actor_counts[actor] = actor_counts.get(actor, 0) + 1
        guidance = handoff.get("continuation_guidance")
        if not isinstance(guidance, dict):
            violations.append(f"{name}/{mode}: continuation_guidance missing or not object")
        elif "command" in guidance:
            violations.append(f"{name}/{mode}: continuation_guidance exposes command")

        if action == "patch_handoff_stop" and handoff.get("allowed_scope") != ["read-only"]:
            violations.append(f"{name}/{mode}: patch handoff leaked editable scope")

print(f"fixtures={len(fixtures)} modes={len(modes)} payloads={len(fixtures) * len(modes)} complete={complete} non_complete={non_complete}")
print("action_counts=" + json.dumps(action_counts, sort_keys=True))
print("actor_counts=" + json.dumps(actor_counts, sort_keys=True))
if violations:
    for item in violations:
        print(" - " + item)
    raise SystemExit(1)
print("assertions=passed")
PY
```

## Results

Review-mode sweep:

| Fixture | Action | Stop Boundary | Required Actor | Allowed Scope |
| --- | --- | --- | --- | --- |
| `fig1_overview_v2` | `run_critique` | `host_llm_critique_required` | `host_llm` | `critique.md`, `build/audit_crops/` |
| `fig1_overview_v2_pair_001_vault` | `run_critique` | `host_llm_critique_required` | `host_llm` | `critique.md`, `build/audit_crops/` |
| `fig3_trapping_concept` | `run_fig_loop` | `closeout_required` | `workflow_agent` | `.scratch/fig-loop-runs/` |
| `fig5_floating_clip_mechanism` | `run_export` | `closeout_required` | `workflow_agent` | `exports/` |
| `golden_trap_depth_picture` | `run_critique` | `host_llm_critique_required` | `host_llm` | `critique.md`, `build/audit_crops/` |
| `n3_trial_01_trap_depth` | `run_critique` | `host_llm_critique_required` | `host_llm` | `critique.md`, `build/audit_crops/` |
| `n3_trial_02_actuation_sequence` | `run_critique` | `host_llm_critique_required` | `host_llm` | `critique.md`, `build/audit_crops/` |
| `smoke_trap_demo` | `run_fig_loop` | `closeout_required` | `workflow_agent` | `.scratch/fig-loop-runs/` |

All-mode assertion summary:

```text
fixtures=8 modes=4 payloads=32 complete=8 non_complete=24
action_counts={"complete": 8, "release_blocked": 2, "run_critique": 15, "run_export": 3, "run_fig_loop": 4}
actor_counts={"host_llm": 15, "release_operator": 2, "workflow_agent": 7}
assertions=passed
```

## Findings

- `boundary_handoff` appeared on all 24 non-complete payloads.
- `boundary_handoff` was omitted on all 8 `complete` payloads.
- `continuation_guidance` did not expose an executable `command` in any of the
  24 non-complete payloads.
- Host critique handoffs route to `host_llm` with critique/audit-crop scope.
- Export and loop closeout handoffs route to `workflow_agent`.
- Release stops route to `release_operator` with `read-only` scope.
- No source, export, accepted, golden, or generated artifact mutation occurred.

## Independent Verification

A separate verifier reran the same 8-fixture x 4-mode plan-mode matrix and
reported:

- all 32 commands exited 0;
- the 8 complete authoring runs omitted `boundary_handoff`;
- the 24 non-complete runs included `boundary_handoff`;
- no handoff exposed an executable `continuation_guidance.command`;
- `executed_count` stayed 0 in every run;
- hashing all files under the eight example directories before/after produced
  `mutation_count=0`.

The verifier found no defect in the observed 70B contract.

## Review

### Contract/schema/freshness

The packet remains a projection of the final driver state. It does not replace
`final_action`, `final_stop_boundary`, `next_action_summary`, or `safe_command`.
Stops with `stop_boundary: null` can still produce a handoff when the final
action is non-complete; the handoff records the action and closeout reason
without inventing a synthetic boundary.

### Backward compatibility and scope

The run payload schema remains `figure-agent.run.v1`. The new packet is
additive and non-complete only. Plan mode preserved the old no-mutation
behavior across all checked fixtures and modes.

### Operator readiness

The packet is sufficient for the next operator to distinguish:

- host-vision critique work;
- workflow closeout/export work;
- release/accepted/golden operator work.

It remains intentionally non-resumable. Issue 70E can add resume UX only after
live status/currentness checks are explicit.

### Coverage limits

This live matrix did not exercise `required_actor: human`, `required_actor:
svg_editor`, or a deferred patch handoff boundary. Those shapes remain covered
by unit tests, but not by this fixture dogfood pass.

## Verdict

No code change is required from this dogfood pass.

No known Issue 70B dogfood blocker remains.
