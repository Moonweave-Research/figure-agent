# Figure Agent Slice 0A Python Render Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Fig1 Python renderer reproduce the tracked SVG byte-for-byte through one explicit, reusable render-toolchain contract, without regenerating or changing the tracked artifact.

**Architecture:** Add a dependency-only module under the experiment's `src/` directory. Both the render-parity fallback and the `pyfig` command wrapper import that module, so they cannot silently resolve different dependency sets. The contract fixes every direct renderer package at the versions that reproduce the tracked SVG and includes every import needed by the Fig1 renderer; a focused test proves both consumers use it.

**Tech Stack:** Python 3, `uv`, drawsvg, Matplotlib 3.10.9, NumPy, RDKit, Shapely, svgelements, svgpathtools, `unittest`.

---

## Scope lock and branch boundary

- Implement only in a clean worktree based on `4f50af8f0679f9997faed01b6581b6742f577fc3` (the Slice 0 SSOT commit on `experiment/python-svg-semantic-fig1`).
- Do not re-render, replace, or edit `experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg`; its SHA-256 must remain `03e51b775bb0dc063e131ecff6f684ab9cb6fd807546df01e01076e5e4d131e1`.
- Do not modify `plugins/figure-agent`, public-main fixtures, or unrelated untracked user files in this worktree.
- Record the verified command output and implementation commit only after the code is complete; Slice 0C owns the SSOT result record.

## File structure

| Path | Responsibility |
| --- | --- |
| `experiments/python_svg_semantic_fig1/src/render_toolchain.py` | The one source of truth for `uv --with` specifications and import names required to reproduce Fig1. |
| `experiments/python_svg_semantic_fig1/src/verify_fig1_render_parity.py` | Uses the shared toolchain contract when the in-process renderer is unavailable. |
| `experiments/python_svg_semantic_fig1/src/test_fig1_render_parity.py` | Proves the fallback and `pyfig` wrapper consume the same contract and keeps the byte-parity test gated on the exact toolchain. |
| `plugins/figure-agent-py/scripts/pyfig.py` | Imports the shared contract before building its `uv run` command. |

### Task 1: Lock the regression tests before implementation

**Files:**
- Create: none
- Modify: `experiments/python_svg_semantic_fig1/src/test_fig1_render_parity.py`
- Test: `experiments/python_svg_semantic_fig1/src/test_fig1_render_parity.py`

- [ ] **Step 1: Add imports and exact-toolchain availability detection.**

  Replace the import block and `RENDER_DEPS_AVAILABLE` declaration with the following. The helper must return `False` when Matplotlib is present but not 3.10.9, because a different Matplotlib version cannot prove byte parity for this artifact.

  ```python
  from __future__ import annotations

  import runpy
  import subprocess
  import tempfile
  import unittest
  from importlib.metadata import PackageNotFoundError, version
  from importlib.util import find_spec
  from pathlib import Path
  from unittest.mock import patch

  from fig1_l1_scene import build_scene
  from render_toolchain import RENDER_DEPENDENCY_SPECS, RENDER_IMPORT_NAMES
  from verify_fig1_render_parity import (
      REPO_ROOT,
      SVG,
      _generated_svg_text_via_uv,
      generated_svg_text,
      render_parity_failures,
  )


  def _render_toolchain_is_available() -> bool:
      try:
          return (
              all(find_spec(module) is not None for module in RENDER_IMPORT_NAMES)
              and version("matplotlib") == "3.10.9"
          )
      except PackageNotFoundError:
          return False


  RENDER_DEPS_AVAILABLE = _render_toolchain_is_available()
  ```

- [ ] **Step 2: Add the two contract-consumer tests to `Fig1RenderParityTests`.**

  ```python
  def test_uv_fallback_uses_canonical_render_toolchain(self) -> None:
      completed = subprocess.CompletedProcess(
          args=[],
          returncode=0,
          stdout="<svg />",
          stderr="",
      )
      with patch(
          "verify_fig1_render_parity.subprocess.run",
          return_value=completed,
      ) as run:
          self.assertEqual("<svg />", _generated_svg_text_via_uv())

      command = run.call_args.args[0]
      resolved_specs = [
          command[index + 1]
          for index, value in enumerate(command[:-1])
          if value == "--with"
      ]
      self.assertEqual(resolved_specs, list(RENDER_DEPENDENCY_SPECS))
      self.assertEqual(command[:2], ["uv", "run"])
      self.assertEqual(command[-2], "-c")
      self.assertEqual(run.call_args.kwargs["cwd"], REPO_ROOT)

  def test_pyfig_wrapper_uses_canonical_render_toolchain(self) -> None:
      module_globals = runpy.run_path(
          str(REPO_ROOT / "plugins" / "figure-agent-py" / "scripts" / "pyfig.py"),
          run_name="pyfig_contract_test",
      )

      self.assertEqual(
          module_globals["RENDER_DEPENDENCY_SPECS"],
          RENDER_DEPENDENCY_SPECS,
      )
  ```

- [ ] **Step 3: Run the focused test to prove the regression is red.**

  Run:

  ```bash
  PYTHONPATH=experiments/python_svg_semantic_fig1/src python -m unittest \
    experiments.python_svg_semantic_fig1.src.test_fig1_render_parity -v
  ```

  Expected: test discovery errors with `ModuleNotFoundError: No module named 'render_toolchain'`. Do not create a local ad-hoc dependency list to make this test pass.

### Task 2: Add the canonical render-toolchain contract and consume it

**Files:**
- Create: `experiments/python_svg_semantic_fig1/src/render_toolchain.py`
- Modify: `experiments/python_svg_semantic_fig1/src/verify_fig1_render_parity.py`
- Modify: `plugins/figure-agent-py/scripts/pyfig.py`
- Modify: `experiments/python_svg_semantic_fig1/src/test_fig1_render_parity.py`
- Test: `experiments/python_svg_semantic_fig1/src/test_fig1_render_parity.py`

- [ ] **Step 1: Create `render_toolchain.py` with the complete contract.**

  ```python
  from __future__ import annotations

  RENDER_DEPENDENCY_SPECS: tuple[str, ...] = (
      "drawsvg==2.4.1",
      "matplotlib==3.10.9",
      "numpy==2.5.1",
      "rdkit==2026.3.3",
      "shapely==2.1.2",
      "svgelements==1.9.6",
      "svgpathtools==1.7.2",
  )

  RENDER_IMPORT_NAMES: tuple[str, ...] = (
      "drawsvg",
      "matplotlib",
      "numpy",
      "rdkit",
      "shapely",
      "svgelements",
      "svgpathtools",
  )
  ```

- [ ] **Step 2: Make the parity fallback import the contract.**

  In `experiments/python_svg_semantic_fig1/src/verify_fig1_render_parity.py`, add the import immediately after the existing standard-library imports and delete the local `UV_RENDER_DEPS` tuple.

  ```python
  from render_toolchain import RENDER_DEPENDENCY_SPECS
  ```

  In `_generated_svg_text_via_uv`, use the shared tuple exactly once:

  ```python
  command = ["uv", "run"]
  for dependency in RENDER_DEPENDENCY_SPECS:
      command.extend(("--with", dependency))
  command.extend(("python", "-c", script))
  ```

- [ ] **Step 3: Make the `pyfig` wrapper import the same contract.**

  In `plugins/figure-agent-py/scripts/pyfig.py`, add `import sys` with the standard-library imports. Immediately after `SRC` is defined, add the experiment source directory to `sys.path` and import the same tuple. Delete the local `RENDER_DEPS` tuple.

  ```python
  if str(SRC) not in sys.path:
      sys.path.insert(0, str(SRC))

  from render_toolchain import RENDER_DEPENDENCY_SPECS
  ```

  In `_uv_python`, iterate `RENDER_DEPENDENCY_SPECS`:

  ```python
  def _uv_python(script: Path) -> list[str]:
      command = ["uv", "run"]
      for dependency in RENDER_DEPENDENCY_SPECS:
          command.extend(("--with", dependency))
      command.extend(("python", str(script)))
      return command
  ```

- [ ] **Step 4: Keep the pre-existing byte-parity tests on the exact contract.**

  Leave the two `@unittest.skipUnless` decorators in place, but update their reason to name the fixed toolchain:

  ```python
  @unittest.skipUnless(
      RENDER_DEPS_AVAILABLE,
      "render parity tests require the Fig1 Matplotlib 3.10.9 render toolchain",
  )
  ```

- [ ] **Step 5: Run the focused tests in the fixed environment.**

  Run:

  ```bash
  uv run --with drawsvg==2.4.1 --with matplotlib==3.10.9 --with numpy==2.5.1 \
    --with rdkit==2026.3.3 --with shapely==2.1.2 --with svgelements==1.9.6 \
    --with svgpathtools==1.7.2 \
    python -m unittest discover -s experiments/python_svg_semantic_fig1/src \
    -p 'test_fig1_render_parity.py' -v
  ```

  Expected: every test passes, including the two new contract-consumer tests and the byte-parity tests.

### Task 3: Prove the public command and byte identity without altering the artifact

**Files:**
- Create: none
- Modify: none
- Test: `experiments/python_svg_semantic_fig1/src/run_fig1_gates.py` through the public wrapper

- [ ] **Step 1: Run the public Fig1 verification command.**

  Run:

  ```bash
  uv run --with drawsvg==2.4.1 --with matplotlib==3.10.9 --with numpy==2.5.1 \
    --with rdkit==2026.3.3 --with shapely==2.1.2 --with svgelements==1.9.6 \
    --with svgpathtools==1.7.2 \
    python plugins/figure-agent-py/scripts/pyfig.py verify-fig1
  ```

  Expected: eight `[PASS]` lines followed by `fig1 gates passed: 8/8`.

- [ ] **Step 2: Hash two independent in-memory SVG generations.**

  Run the following command twice, in two separate invocations:

  ```bash
  PYTHONPATH=experiments/python_svg_semantic_fig1/src \
    uv run --with drawsvg==2.4.1 --with matplotlib==3.10.9 --with numpy==2.5.1 \
    --with rdkit==2026.3.3 --with shapely==2.1.2 --with svgelements==1.9.6 \
    --with svgpathtools==1.7.2 \
    python -c 'import hashlib; from verify_fig1_render_parity import generated_svg_text; print(hashlib.sha256(generated_svg_text().encode()).hexdigest())'
  ```

  Expected each time: `03e51b775bb0dc063e131ecff6f684ab9cb6fd807546df01e01076e5e4d131e1`. If either hash differs, stop and diagnose the source of nondeterminism; do not update the tracked SVG.

- [ ] **Step 3: Inspect the worktree boundary.**

  Run:

  ```bash
  git diff --check
  git status --short
  ```

  Expected: no whitespace errors; only the four planned code/test paths are modified or added.

### Task 4: Commit the isolated Python parity repair

**Files:**
- Create: `experiments/python_svg_semantic_fig1/src/render_toolchain.py`
- Modify: `experiments/python_svg_semantic_fig1/src/verify_fig1_render_parity.py`
- Modify: `experiments/python_svg_semantic_fig1/src/test_fig1_render_parity.py`
- Modify: `plugins/figure-agent-py/scripts/pyfig.py`

- [ ] **Step 1: Stage only the planned files.**

  ```bash
  git add experiments/python_svg_semantic_fig1/src/render_toolchain.py \
    experiments/python_svg_semantic_fig1/src/verify_fig1_render_parity.py \
    experiments/python_svg_semantic_fig1/src/test_fig1_render_parity.py \
    plugins/figure-agent-py/scripts/pyfig.py
  ```

- [ ] **Step 2: Commit the repair.**

  ```bash
  git commit -m "fix: pin Fig1 Python render parity toolchain"
  ```

- [ ] **Step 3: Capture the immutable evidence for Slice 0C.**

  Run:

  ```bash
  git rev-parse HEAD
  git status --short
  ```

  Expected: a commit SHA for the Slice 0A result and a clean isolated worktree. Slice 0C will cite this SHA and the `8/8` command output in `FIGURE_AGENT_SPEC.md`.
