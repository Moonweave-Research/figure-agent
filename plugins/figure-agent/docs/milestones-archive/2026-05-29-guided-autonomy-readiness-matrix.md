# Guided Autonomy Readiness Matrix

Date: 2026-05-29

Related issue:
`docs/superpowers/issues/2026-05-29-issue-70a-guided-autonomy-readiness-matrix.md`

Status: completed

## Goal

Check whether the next large plugin-development slice should expand
`/fig_run` autonomy, or whether the current real-fixture state points to
boundary clarity, closeout freshness, fixture adoption, patch freshness, or
SVG-polish evidence first.

This pass used read-only planning and dry-run commands. It did not execute
compile/export/loop/adjudication commands and did not create generated
artifacts.

## Commands

From repo root:

```bash
python3 - <<'PY'
import json, subprocess
from pathlib import Path

root = Path('plugins/figure-agent')
fixtures = sorted(
    p.name for p in (root / 'examples').iterdir() if (p / 'spec.yaml').exists()
)

for name in fixtures:
    proc = subprocess.run(
        [
            'uv',
            'run',
            'python3',
            'scripts/fig_run.py',
            name,
            '--mode',
            'review',
            '--goal',
            'guided-autonomy-readiness',
            '--max-steps',
            '3',
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(proc.stdout)
    step = payload['steps'][0]
    driver = step['driver']
    status = driver['status']
    print(
        name,
        status['render_state'],
        status['critique_state'],
        status['export_state'],
        status['acceptance_state'],
        status['final_artifact_state'],
        driver['action'],
        driver['stop_boundary'],
        payload['final_stop_reason'],
        payload['executed_count'],
        step['would_execute'],
        sep='\t',
    )
PY
```

Mode sweep:

```bash
python3 - <<'PY'
import json, subprocess
from collections import Counter, defaultdict
from pathlib import Path

root = Path('plugins/figure-agent')
fixtures = sorted(
    p.name for p in (root / 'examples').iterdir() if (p / 'spec.yaml').exists()
)
counts = Counter()
examples = defaultdict(list)

for name in fixtures:
    for mode in ['authoring', 'review', 'release', 'polish']:
        proc = subprocess.run(
            [
                'uv',
                'run',
                'python3',
                'scripts/fig_driver.py',
                name,
                '--mode',
                mode,
                '--goal',
                'guided-autonomy-readiness',
                '--dry-run',
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(proc.stdout)
        key = (mode, payload['action'], payload.get('stop_boundary'))
        counts[key] += 1
        examples[key].append(name)

for key, count in sorted(counts.items()):
    print(f'{key}\t{count}\t{examples[key][:3]}')
PY
```

## Review-Mode Matrix

| Fixture | render | critique | export | acceptance | final artifact | action | stop boundary | run stop | executed | would execute |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| `fig1_overview_v2` | FRESH | STALE | FRESH | NOT_ACCEPTED | NONE | `run_critique` | `host_llm_critique_required` | `host_boundary` | 0 | false |
| `fig1_overview_v2_pair_001_vault` | FRESH | STALE | TRACKED_GOLDEN | ACCEPTED | NONE | `run_critique` | `host_llm_critique_required` | `host_boundary` | 0 | false |
| `fig3_trapping_concept` | FRESH | NOT_REQUIRED | FRESH | NOT_DECLARED | NONE | `run_fig_loop` | `closeout_required` | `not_executable_action` | 0 | false |
| `fig5_floating_clip_mechanism` | FRESH | NOT_REQUIRED | MISSING | NOT_ACCEPTED | NONE | `run_export` | `closeout_required` | `not_executable_action` | 0 | false |
| `golden_trap_depth_picture` | FRESH | STALE | TRACKED_GOLDEN | NOT_ACCEPTED | NONE | `run_critique` | `host_llm_critique_required` | `host_boundary` | 0 | false |
| `n3_trial_01_trap_depth` | FRESH | STALE | MISSING | NOT_DECLARED | NONE | `run_critique` | `host_llm_critique_required` | `host_boundary` | 0 | false |
| `n3_trial_02_actuation_sequence` | FRESH | STALE | FRESH | NOT_DECLARED | NONE | `run_critique` | `host_llm_critique_required` | `host_boundary` | 0 | false |
| `smoke_trap_demo` | FRESH | NOT_REQUIRED | FRESH | NOT_DECLARED | NONE | `run_fig_loop` | `closeout_required` | `not_executable_action` | 0 | false |

## Stop-Shape Summary

Review mode produced three stop/action shapes:

| Shape | Count | Meaning |
| --- | ---: | --- |
| `run_critique` + `host_llm_critique_required` + `host_boundary` | 5 | Host vision critique is the dominant stop. This is manual by design. |
| `run_fig_loop` + `closeout_required` + `not_executable_action` | 2 | `/fig_run` refuses a closeout-bound loop state even though a safe command string exists. |
| `run_export` + `closeout_required` + `not_executable_action` | 1 | Export is mechanically possible in some modes, but closeout state blocks review-mode execution. |

Across all four modes, the distinct driver shapes were:

| Mode/action/boundary | Count | Example fixtures |
| --- | ---: | --- |
| authoring / `complete` / none | 8 | all fixtures |
| review / `run_critique` / `host_llm_critique_required` | 5 | `fig1_overview_v2`, `_vault`, `golden_trap_depth_picture` |
| review / `run_fig_loop` / `closeout_required` | 2 | `fig3_trapping_concept`, `smoke_trap_demo` |
| review / `run_export` / `closeout_required` | 1 | `fig5_floating_clip_mechanism` |
| release / `release_blocked` / `accepted_or_final_ready_required` | 2 | `fig3_trapping_concept`, `smoke_trap_demo` |
| release / `run_export` / none | 1 | `fig5_floating_clip_mechanism` |
| polish / `run_fig_loop` / `mode_forbidden_action` | 2 | `fig3_trapping_concept`, `smoke_trap_demo` |
| polish / `run_export` / none | 1 | `fig5_floating_clip_mechanism` |

## Closeout Probe

The pass also sampled `fig_closeout.py --json` on six representative fixtures:

| Fixture | closeout complete | blocking steps | next action summary |
| --- | --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | false | `critique`, `adjudication`, `export`, `loop_rerun` | `run_critique`, allowed scope `critique.md` and audit crops |
| `golden_trap_depth_picture` | false | `critique`, `adjudication`, `export`, `loop_rerun` | `run_critique`, allowed scope `critique.md` and audit crops |
| `fig1_overview_v2` | false | `critique`, `adjudication`, `export`, `loop_rerun` | `run_critique`, allowed scope `critique.md` and audit crops |
| `fig3_trapping_concept` | false | `loop_rerun` | `run_fig_loop`, allowed scope `.scratch/fig-loop-runs/` |
| `fig5_floating_clip_mechanism` | false | `export`, `loop_rerun` | `run_export`, allowed scope `exports/` |
| `n3_trial_02_actuation_sequence` | false | `critique`, `adjudication`, `export`, `loop_rerun` | `run_critique`, allowed scope `critique.md` and audit crops |

This confirms that the current closeout layer already has a useful
`next_action_summary`, but `/fig_run` does not yet lift that summary into a
compact operator-facing boundary packet.

## Coverage Gaps

The current real fixture set did not exercise these Issue 70A requested shapes:

- patch handoff;
- pending patch closeout;
- SVG polish readiness;
- stale-polish or semantic-backport polish gate.

Per the 70A contract, this is not a clean pass for resume/journal work. It is a
blocking evidence gap for any child issue that assumes those shapes are already
understood.

## Go/No-Go Judgment

Proceed selectively, with a conservative priority order:

1. **70C is the strongest next implementation candidate.**
   Patch/source mutation is the highest-risk path, and the current fixture set
   did not exercise patch handoff or pending closeout. Before any UX makes patch
   work more visible, the patch executor should refuse stale loop checkpoints
   and pending-closeout states.

2. **70B is allowed only as a small non-patch UX slice.**
   Host critique, force/manual release, closeout, and mode-forbidden boundaries
   are real enough to justify a small explanatory packet. 70B must stay
   mechanical, must not emit executable resume commands, and must omit
   patch/source-mutation scope until 70C lands.

3. **No-go for 70D/70E resume or runner journal for now.**
   This pass did not show a persistent multi-session continuity gap that
   requires a journal or resume feature. Existing output is stdout-only, but the
   stronger near-term signal is boundary clarity and patch freshness.

4. **Record SVG-polish evidence as missing for this roadmap.**
   Positive SVG-polish promotion evidence remains an independent follow-up; it
   should not block 70B/70C, but it does block any claim that Issue 70 fully
   covers polish-mode autonomy.

## Review Notes

- No generated build/export artifacts were intentionally created.
- `/fig_run --execute` was not used because review-mode plan output had
  `would_execute=false` for all eight fixtures.
- The current state suggests the next implementation should be 70C patch
  freshness hardening, or a deliberately small 70B non-patch boundary packet if
  operator-facing clarity is prioritized. Resume/replay remains unjustified.

## Verification

- `git status --short --branch` before the pass showed only untracked Issue 70
  docs/spec files.
- Read-only `fig_driver.py --dry-run` and plan-mode `fig_run.py` commands
  completed for eight fixtures.
- Docs hygiene check over Issue 70 files passed: no trailing whitespace, no
  conflict markers, final newline present.
- `claude plugin validate .` passed from `plugins/figure-agent`.
