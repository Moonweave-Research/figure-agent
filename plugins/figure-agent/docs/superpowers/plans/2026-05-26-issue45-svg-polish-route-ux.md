# Issue 45 SVG Polish Route UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/fig_driver --mode polish` surface the first safe next command in the SVG polish recipe workflow.

**Architecture:** Keep `fig_driver.py` as the dry-run traffic controller. Add small command helpers in `fig_driver_commands.py`, and keep all file-presence probing fixture-local and read-only.

**Tech Stack:** Python 3.12, pytest, ruff, existing figure-agent driver tests.

---

### Task 1: Polish Recipe Route Hints

**Files:**
- Modify: `scripts/fig_driver_commands.py`
- Modify: `scripts/fig_driver.py`
- Modify: `tests/test_fig_driver.py`
- Modify: `commands/fig_drive.md`

- [x] **Step 1: Write failing driver tests**

Add tests covering missing recipe, recipe present, polished SVG present, and
delta manifest present. Also assert semantic backport still takes precedence.

Run:

```bash
uv run pytest -q tests/test_fig_driver.py -k "polish_mode"
```

Expected: new tests fail before implementation.

- [x] **Step 2: Add command helpers**

Add helpers:

```python
def svg_polish_executor_dry_run_command(name: str) -> str:
    return f"uv run python3 scripts/svg_polish_executor.py examples/{name} --dry-run"


def svg_polish_executor_write_command(name: str) -> str:
    return f"uv run python3 scripts/svg_polish_executor.py examples/{name} --write"


def svg_polish_delta_command(name: str) -> str:
    return (
        "PYTHONPATH=scripts uv run python3 -c "
        + shlex.quote(
            "from pathlib import Path; "
            "from svg_polish_delta import build_svg_polish_delta_pack; "
            f"build_svg_polish_delta_pack(Path('examples/{name}'), base_dir=Path('.'))"
        )
    )
```

- [x] **Step 3: Implement read-only polish route hint**

In polish mode, when the ready-for-SVG branch is reached, inspect:

```python
recipe_path = example_dir / "polish" / "svg_polish_recipe.yaml"
polished_svg_path = example_dir / "polish" / f"{name}.polished.svg"
delta_manifest_path = example_dir / "polish" / "aesthetic_delta" / "delta_manifest.json"
```

Return the first applicable hint without writing files.

- [x] **Step 4: Update docs**

Update `commands/fig_drive.md` so the canonical polish sequence is:

```bash
uv run python3 scripts/svg_polish_executor.py examples/<name> --dry-run
uv run python3 scripts/svg_polish_executor.py examples/<name> --write
PYTHONPATH=scripts uv run python3 -c "from pathlib import Path; from svg_polish_delta import build_svg_polish_delta_pack; build_svg_polish_delta_pack(Path('examples/<name>'), base_dir=Path('.'))"
uv run python3 scripts/svg_polish_handoff.py examples/<name> ...
```

- [x] **Step 5: Verify**

Run:

```bash
uv run pytest -q tests/test_fig_driver.py
uv run ruff check scripts/fig_driver.py scripts/fig_driver_commands.py tests/test_fig_driver.py
git diff --check
```

- [x] **Step 6: Review**

Review:

- no mutation in driver;
- no new action vocabulary;
- semantic/human gates still precede polish hints;
- command strings are shell-safe enough for fixture names used by the plugin;
- docs match actual commands.
