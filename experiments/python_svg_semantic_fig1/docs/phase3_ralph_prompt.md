# Phase 3 Ralph Loop Prompt

Paste the block below as the user message. Re-fire the same prompt each iteration; the loop converges when all five phases are committed.

---

You are continuing Phase 3 of the Fig1 semantic SVG renderer on branch `experiment/python-svg-semantic-fig1`.

The single source of truth is:
`/Users/choemun-yeong/workspace/ResearchOS/[figure-agent-py]/experiments/python_svg_semantic_fig1/docs/phase3_plan.md`

## What you do this iteration

1. Read the plan file end-to-end. Do not skim. Pay attention to section 0 (goals), section 1 (commit discipline), and the "Tasks" checklist of every phase.
2. Determine the current phase by scanning the per-phase task lists from 3-A → 3-E in order. The current phase is the first one that has at least one unchecked `[ ]` task.
3. Pick exactly one task: the first unchecked `[ ]` item under the current phase.
4. If the task is a verification or commit step (gate run, test run, render, hash update, commit), execute it and verify the result before ticking the box.
5. If the task is a code edit, perform the edit with `Edit` or `Write`. Then run any verification the plan demands for that task. Then tick the box.
6. After the task is done, edit the plan file to:
   - Replace the matching `[ ]` with `[x]` on that one line.
   - If the task adds new audit info (e.g., a grep result, a density reading, a deferral note), append it to section 7 with a short header `### 3-X.Y — <topic>` and the data.
   - Update section 8 status if a phase just closed (e.g., `Phase 3-A: complete` and `Phase 3-B: in progress`).
7. Stop after one task. Do not chain into the next task. The loop will re-fire and pick up the next unchecked box.

## Hard rules

- Never amend an existing commit. New commits only.
- Never skip pre-commit hooks (no `--no-verify`).
- Never run `git reset --hard`, `git push --force`, `rm -rf`, or any destructive command. If the plan seems to require one, stop and report instead.
- Never edit files outside the paths listed in the current phase's "Touched paths" section. If a task forces you outside, stop and report.
- Always prefer the dispatcher for render and gate runs:
  - render: `uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools --with rdkit python plugins/figure-agent-py/scripts/pyfig.py render-fig1`
  - gates: `uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools --with rdkit python plugins/figure-agent-py/scripts/pyfig.py verify-fig1`
  - tests: `cd experiments/python_svg_semantic_fig1 && uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools --with rdkit python -m unittest discover -s src -p 'test_fig1_*.py' -v`
- A phase commit is only made by a task that explicitly says "Commit: ..." in the plan.
- Commit messages must match the exact string in the plan (e.g., `SEMANTIC.fig1: phase 3-A — commit library-fragment scaffolding + drop dead pe_hysteresis`).
- Stage explicitly. Use `git add <path> <path>` per the touched paths in the current phase. Never `git add -A` or `git add .`.
- If a gate fails or a test fails, do not tick the box. Stop and report the failure with the gate/test name and the last lines of stderr. The loop will re-fire after a human has responded.
- If you discover that a path the plan tells you to edit does not exist, stop and report. Do not invent a path.

## Stop condition

Stop the loop when:
- All `[ ]` boxes in the plan file are `[x]`, or
- A blocker prevents progress (gate failure, missing path, ambiguity in the plan), or
- The next task explicitly requires a human decision (e.g., the plan says "stop and ask").

When stopping for any reason, output one short paragraph: which task you just finished (or which one is blocked), the verification result you observed, and what the next box says.

## Tone

Korean text for explanations to the user. Tool calls and code as usual. Do not narrate plans you have already written down — just announce the one task you are about to execute, do it, and report the verification.
