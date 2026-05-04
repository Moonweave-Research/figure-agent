# Figure-Agent v0.3 Review Blockers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the current review blockers that make v0.3 snippet work, workflow docs, and golden-fixture contracts inconsistent, without claiming the golden fixture is manuscript-ready.

**Architecture:** Keep the active product identity as a paper-figure quality kernel: `/fig_new` scaffolds intent, `/fig_extract` creates reference evidence, semantic TikZ is authored from briefing plus hints, `/fig_compile` and `/fig_export` enforce quality. This plan first fixes release-blocking file ownership and stale public contracts, then promotes `\PolymerChain` into the lint/test surface, then reconciles the golden fixture briefing with the new snippet usage. Strict visual acceptance remains evidence, not a false `accepted: true`.

**Tech Stack:** Python 3.12, pytest, ruff, LuaLaTeX, TikZ/PGF, chemfig, xstring, Claude Code plugin validation.

---

## Preconditions

- Implement in a separate worktree after other active Claude sessions finish or after their branch is merged.
- Do not run this plan directly in a dirty shared checkout.
- Start from `plugins/figure-agent` as the command working directory for tests and plugin validation.
- Preserve unrelated user edits. If a file already differs from this plan because another session landed compatible changes, inspect the diff and adapt without reverting their work.
- Do not mark `examples/golden_trap_depth_picture/spec.yaml` as `accepted: true` in this plan.

Recommended setup:

```bash
git worktree add ~/.config/superpowers/worktrees/figure-agent/fix-v0-3-review-blockers -b fix/v0-3-review-blockers
cd ~/.config/superpowers/worktrees/figure-agent/fix-v0-3-review-blockers/plugins/figure-agent
git status --short
```

Expected baseline status before edits:

```text
```

If baseline status is not clean, stop and identify whether those changes came from a merged Claude branch or from local carry-over.

## File Structure

Create or track:

- `styles/snippets/README.md` — snippet catalog, usage contract, acceptance gate, and `polymer_chain` attribution.
- `styles/snippets/polymer_chain.snippet.tex` — chemfig-based L3 snippet exposing `\PolymerChain`.
- `examples/_snippet_smoke/polymer_chain/polymer_chain_smoke.tex` — standalone compile smoke fixture for the snippet.

Modify:

- `styles/polymer-paper-preamble.sty` — load `xstring` and `chemfig`, set chemfig defaults, and keep atom text under the shared sans-serif style.
- `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex` — input the tracked snippet and use `\PolymerChain` only where it represents Row 3 polymer chains.
- `examples/golden_trap_depth_picture/briefing.md` — reconcile author intent with the actual row and monomer count used by the fixture.
- `scripts/lint_tex.py` — recognize `\PolymerChain` as a flagship macro.
- `tests/test_lint_tex.py` — add focused coverage proving `\PolymerChain` suppresses `flagship_macros_unused`.
- `tests/test_compile_contract.py` — add a smoke compile test for the snippet fixture, or extend the existing golden compile test only if the dedicated fixture is too slow in local timing.
- `commands/fig_new.md` — remove deleted `/fig_prompt` and `/fig_preview_select` handoff language from the active user path.
- `README.md` — remove stale claims that prompt/image-gen helpers remain available; align status with current v0.2/v0.3 direction.
- `skills/figure-agent/SKILL.md` — align description and workflow text with deleted legacy commands.
- `.claude-plugin/marketplace.json` and `pyproject.toml` — update descriptions from prompt/vector wording to quality-kernel wording.
- `tests/test_release_contract.py` — add contract tests so stale deleted-command language cannot return in public docs.

Do not modify:

- `scripts/check_visual_clash.py`
- `scripts/check_layout_drift.py`
- `scripts/check_golden_artifacts.py`
- `examples/golden_trap_depth_picture/spec.yaml`, except if a merged branch already changed non-acceptance metadata and the change is directly required for tests.

## Task 1: Baseline Verification

**Files:** none

- [ ] **Step 1: Confirm branch and clean baseline**

Run:

```bash
git branch --show-current
git status --short
```

Expected:

```text
fix/v0-3-review-blockers
```

The second command should print no tracked or untracked changes.

- [ ] **Step 2: Run current tests before edits**

Run from `plugins/figure-agent`:

```bash
uv run pytest -q
```

Expected:

```text
188 passed
```

The exact runtime may differ. If the count differs because another branch added tests, record the new count and continue only if all tests pass.

- [ ] **Step 3: Run current lint**

```bash
uv run ruff check .
```

Expected:

```text
All checks passed!
```

- [ ] **Step 4: Commit checkpoint only if baseline has required generated lock changes**

If no files changed, do not commit. If `uv` or tooling changed a lock file unexpectedly, inspect it and stop before continuing.

## Task 2: Track the L3 Polymer Snippet

**Files:**

- Create: `styles/snippets/README.md`
- Create: `styles/snippets/polymer_chain.snippet.tex`
- Create: `examples/_snippet_smoke/polymer_chain/polymer_chain_smoke.tex`
- Modify: `styles/polymer-paper-preamble.sty`

- [ ] **Step 1: Create `styles/snippets/README.md`**

Write this complete file:

```markdown
# L3 Snippet Library

v0.3 vendored / curated TikZ snippets for paper-grade scientific figures.
Plan: `docs/architecture-v0.3-snippet-library.md`.

## Catalog

| Snippet | Macro | Status | Source / License |
|---|---|---|---|
| `polymer_chain.snippet.tex` | `\PolymerChain{x}{y}{n_monomers}{s_csv}` | A1 (v0.3 first ship) | chemfig (LPPL 1.3) - TeX Live; snippet code MIT-style |
| `log_plot.snippet.tex` | `\LogPlot{...}` | A2 planned | PGFPlots (LPPL 1.3) |
| `band_diagram.snippet.tex` | `\BandSnippet{...}` | A3 planned | hand-curated TikZ |
| `dos_lobes.snippet.tex` | `\DOSLobes{...}` | A4 planned | PGFPlots fillbetween |

## Usage contract

1. Consumer document loads `polymer-paper-preamble.sty`.
2. Consumer `\input`s the snippet file in the preamble.
3. Consumer calls the macro inside any `tikzpicture` scope.
4. Caller may locally override `\setchemfig{...}` per figure if a non-default scale is needed.

## Acceptance gate

A snippet ships only if:

- Compiles standalone with the production preamble and lualatex.
- Remains Style Lock compatible.
- Exposes caller-tuned variations as macro arguments.
- Records source and license attribution in this README.
- Has one smoke fixture in `examples/_snippet_smoke/<name>/`.

## `polymer_chain.snippet.tex`

**Purpose:** Sulfur-rich copolymer chain with monomer-resolved backbone.

**Signature:** `\PolymerChain{anchor_x}{anchor_y}{monomer_count}{s_csv}`

- `anchor_x`, `anchor_y` are TikZ cm coordinates of the chain's leftmost atom anchor.
- `monomer_count` is an integer in the validated range 4..16.
- `s_csv` is a comma-separated list of 1-based monomer indices that carry one downward `-S` branch.

Density encoding:

- sparse: indices spaced about four monomers apart, such as `3,7,11`
- rich: contiguous indices, such as `6,7,8,9`
- mixed: combine sparse and rich regions, such as `3,6,7,8,9,12`

**Smoke fixture:** `examples/_snippet_smoke/polymer_chain/polymer_chain_smoke.tex`

**First production consumer:** `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex` Row 3.

**Known limitation:** chemfig auto-layout positions the leftmost atom slightly below the requested `anchor_y` because `[:30]` zigzag rises upward from the anchor. Drift is consistent and predictable; caller may adjust the anchor when precise centerline alignment with external elements matters.
```

- [ ] **Step 2: Create `styles/snippets/polymer_chain.snippet.tex`**

Write this complete file:

```tex
%% polymer_chain.snippet.tex
%% Sulfur-rich copolymer chain with monomer-resolved backbone (chemfig-based).
%% License: snippet code MIT-style; chemfig is LPPL 1.3 (TeX Live).
%% Author origin: figure-agent v0.3.
%%
%% Usage:
%%   \usepackage{polymer-paper-preamble}
%%   \input{styles/snippets/polymer_chain.snippet.tex}
%%   \PolymerChain{x_anchor}{y_anchor}{monomer_count}{s_csv}
%%
%% Args:
%%   #1 = anchor_x (TikZ cm)
%%   #2 = anchor_y (TikZ cm)
%%   #3 = monomer_count (integer 4..16)
%%   #4 = comma-separated 1-based monomer indices that carry a single -S branch

% Dependencies: chemfig, xstring, tikz/pgfmath. The production preamble loads them.

\makeatletter
\newcommand{\PolymerChain}[4]{%
  \begingroup
  \def\PCsidecsv{,#4,}%
  \xdef\PCchainstr{[:30]}%
  \pgfmathtruncatemacro{\PCnmono}{#3}%
  \foreach \PCi in {1,...,\PCnmono} {%
    \edef\PCneedle{,\PCi,}%
    \IfSubStr{\PCsidecsv}{\PCneedle}%
      {\xdef\PCchainstr{\PCchainstr-[:-30](-[:-90]S)-[:30]}}%
      {\xdef\PCchainstr{\PCchainstr-[:-30]-[:30]}}%
  }%
  \node[anchor=west, inner sep=0pt] at (#1,#2)
    {\expandafter\chemfig\expandafter{\PCchainstr}};
  \endgroup
}
\makeatother
```

- [ ] **Step 3: Modify `styles/polymer-paper-preamble.sty`**

Ensure the package block includes:

```tex
\usepackage{xstring}
\usepackage{chemfig}
```

After the palette/font setup and before custom drawing macros, ensure the chemfig defaults include:

```tex
\setchemfig{
  atom sep=0.30cm,
  bond style={line width=0.32pt, cBrown},
  cram width=1.5pt,
  cram dash width=0.3pt,
  cram dash sep=0.5pt
}
\renewcommand*\printatom[1]{\sffamily\scriptsize\textcolor{cBrown}{#1}}
```

Keep existing palette colors and existing macros intact.

- [ ] **Step 4: Create the smoke fixture**

Create `examples/_snippet_smoke/polymer_chain/polymer_chain_smoke.tex`:

```tex
% Smoke fixture: prove polymer_chain.snippet.tex compiles standalone with
% the production preamble + chemfig at the validated scale.
% Acceptance: 3 chains visible, middle chain has S-rich cluster inside dashed box.
\documentclass[border=4pt]{standalone}
\usepackage{polymer-paper-preamble}

\input{../../../styles/snippets/polymer_chain.snippet.tex}

\begin{document}
\begin{tikzpicture}[x=1cm, y=1cm]
  \draw[gray!60, dashed, rounded corners=2pt, line width=0.4pt]
    (3.50,0.85) rectangle (5.10,2.60);
  \node[font=\tiny\sffamily, anchor=north, text=gray] at (4.30,0.83)
    {S-rich cluster (mid chain monomers 6-9)};

  \PolymerChain{1.20}{2.20}{14}{3,7,11}
  \PolymerChain{1.20}{1.40}{14}{3,6,7,8,9,12}
  \PolymerChain{1.20}{0.60}{14}{4,8,12}
\end{tikzpicture}
\end{document}
```

- [ ] **Step 5: Compile the smoke fixture**

Run:

```bash
bash scripts/compile.sh examples/_snippet_smoke/polymer_chain/polymer_chain_smoke.tex
```

Expected:

```text
OK: wrote examples/_snippet_smoke/polymer_chain/build/polymer_chain_smoke.pdf
OK: wrote examples/_snippet_smoke/polymer_chain/build/polymer_chain_smoke.png
```

Additional visual-clash warnings are acceptable for this smoke fixture only if compile returns exit code 0.

- [ ] **Step 6: Commit Task 2**

```bash
git add styles/snippets/README.md styles/snippets/polymer_chain.snippet.tex examples/_snippet_smoke/polymer_chain/polymer_chain_smoke.tex styles/polymer-paper-preamble.sty
git commit -m "feat(snippets): add polymer chain L3 snippet"
```

## Task 3: Promote `\PolymerChain` into Style Lock

**Files:**

- Modify: `scripts/lint_tex.py`
- Modify: `tests/test_lint_tex.py`

- [ ] **Step 1: Add failing test**

Append this test near the existing WARN-tier flagship tests in `tests/test_lint_tex.py`:

```python
def test_polymer_chain_counts_as_flagship_macro(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\PolymerChain{0}{0}{14}{3,6,7,8,9}" + "\n")
    violations = lint(tex)
    assert not any(v.category == "flagship_macros_unused" for v in violations)
```

- [ ] **Step 2: Verify the test fails before implementation**

Run:

```bash
uv run pytest tests/test_lint_tex.py::test_polymer_chain_counts_as_flagship_macro -q
```

Expected before implementation:

```text
FAILED
```

The failure should show `flagship_macros_unused` is still emitted.

- [ ] **Step 3: Update flagship macro registry**

In `scripts/lint_tex.py`, add `\\PolymerChain` to `FLAGSHIP_MACROS`:

```python
FLAGSHIP_MACROS: frozenset[str] = frozenset(
    {
        "\\IsoBlock",
        "\\IsoCharge",
        "\\GradSlab",
        "\\IsoConeTip",
        "\\BellCurve",
        "\\WavyChain",
        "\\BandDiagram",
        "\\LogLogPlot",
        "\\PolymerChain",
    }
)
```

Update `_RE_FLAGSHIP_CALL` to include `PolymerChain`:

```python
_RE_FLAGSHIP_CALL = re.compile(
    r"\\(IsoBlock|IsoCharge|GradSlab|IsoConeTip"
    r"|BellCurve|WavyChain|BandDiagram|LogLogPlot|PolymerChain)\b"
)
```

- [ ] **Step 4: Verify the focused test passes**

Run:

```bash
uv run pytest tests/test_lint_tex.py::test_polymer_chain_counts_as_flagship_macro -q
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Run lint test module**

```bash
uv run pytest tests/test_lint_tex.py -q
```

Expected: all tests in the module pass.

- [ ] **Step 6: Commit Task 3**

```bash
git add scripts/lint_tex.py tests/test_lint_tex.py
git commit -m "test(lint): recognize polymer chain macro"
```

## Task 4: Wire the Golden Fixture to the Tracked Snippet

**Files:**

- Modify: `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex`
- Modify: `examples/golden_trap_depth_picture/briefing.md`
- Modify: `tests/test_compile_contract.py`

- [ ] **Step 1: Confirm the golden source inputs the tracked snippet**

In `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex`, the preamble should include exactly this relative input after the production preamble import:

```tex
\input{../../styles/snippets/polymer_chain.snippet.tex}
```

Keep the existing `\PolymerChain` calls only in the Row 3 polymer-chain region.

- [ ] **Step 2: Reconcile briefing intent**

In `examples/golden_trap_depth_picture/briefing.md`, update the author-intent section so it says Row 3 uses polymer chains. Use this wording for the invariant:

```markdown
- Row 3 polymer chain: three sulfur-rich copolymer chains must show monomer-level texture, with sulfur atoms visually distinct from the carbon backbone. The production fixture uses 11 chemfig monomers per chain to preserve layout fit against the reference target.
```

Remove or replace any conflicting line that says Row 1 uses the polymer chain or that the accepted requirement is at least 14 segments for the production fixture.

- [ ] **Step 3: Add dedicated compile coverage for the snippet smoke fixture**

Append this test to `tests/test_compile_contract.py` near the golden compile test:

```python
@pytest.mark.skipif(
    shutil.which("lualatex") is None
    or shutil.which("pdftocairo") is None
    or shutil.which("pdftotext") is None
    or shutil.which("pdftoppm") is None,
    reason="requires lualatex, pdftocairo, pdftotext, and pdftoppm",
)
def test_polymer_chain_snippet_smoke_fixture_compiles() -> None:
    tex_path = (
        REPO_ROOT
        / "examples"
        / "_snippet_smoke"
        / "polymer_chain"
        / "polymer_chain_smoke.tex"
    )

    result = subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (
        REPO_ROOT
        / "examples"
        / "_snippet_smoke"
        / "polymer_chain"
        / "build"
        / "polymer_chain_smoke.pdf"
    ).exists()
```

- [ ] **Step 4: Verify compile coverage**

Run:

```bash
uv run pytest tests/test_compile_contract.py::test_polymer_chain_snippet_smoke_fixture_compiles -q
```

Expected:

```text
1 passed
```

- [ ] **Step 5: Compile the golden fixture**

Run:

```bash
bash scripts/compile.sh examples/golden_trap_depth_picture/golden_trap_depth_picture.tex
```

Expected:

```text
OK: wrote examples/golden_trap_depth_picture/build/golden_trap_depth_picture.pdf
OK: wrote examples/golden_trap_depth_picture/build/golden_trap_depth_picture.png
```

Visual clash and layout drift reports may still find issues. This task only fixes dependency and briefing consistency.

- [ ] **Step 6: Commit Task 4**

```bash
git add examples/golden_trap_depth_picture/golden_trap_depth_picture.tex examples/golden_trap_depth_picture/briefing.md tests/test_compile_contract.py
git commit -m "fix(golden): make polymer snippet dependency reproducible"
```

## Task 5: Remove Deleted Legacy Workflow Drift from Public Contracts

**Files:**

- Modify: `commands/fig_new.md`
- Modify: `README.md`
- Modify: `skills/figure-agent/SKILL.md`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `pyproject.toml`
- Modify: `tests/test_release_contract.py`

- [ ] **Step 1: Add contract tests for deleted command drift**

Append this test to `tests/test_release_contract.py`:

```python
def test_public_docs_do_not_route_to_deleted_legacy_commands() -> None:
    docs_by_path = {
        "README.md": (REPO_ROOT / "README.md").read_text(),
        "skills/figure-agent/SKILL.md": (
            REPO_ROOT / "skills" / "figure-agent" / "SKILL.md"
        ).read_text(),
        "commands/fig_new.md": (REPO_ROOT / "commands" / "fig_new.md").read_text(),
    }
    forbidden_strings = [
        "/fig_prompt",
        "/fig_preview_select",
        "prompt/image-gen orchestration remains available",
        "Prompt/image-gen orchestration from v0.1 remains available",
        "The earlier prompt/image-gen orchestration helpers remain available",
        "v0.1 line is active",
    ]

    for doc_path, doc_text in docs_by_path.items():
        for forbidden in forbidden_strings:
            assert forbidden not in doc_text, f"{doc_path} still contains {forbidden!r}"
```

Append this test to the same file:

```python
def test_package_descriptions_name_quality_kernel_direction() -> None:
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    marketplace = json.loads((REPO_ROOT.parents[1] / ".claude-plugin" / "marketplace.json").read_text())

    texts = [
        plugin["description"],
        pyproject["project"]["description"],
        marketplace["description"],
        marketplace["plugins"][0]["description"],
    ]

    for text in texts:
        assert "quality" in text.lower()
        assert "prompt intent control" not in text
```

- [ ] **Step 2: Verify the new tests fail before doc edits**

Run:

```bash
uv run pytest tests/test_release_contract.py::test_public_docs_do_not_route_to_deleted_legacy_commands tests/test_release_contract.py::test_package_descriptions_name_quality_kernel_direction -q
```

Expected before edits:

```text
FAILED
```

- [ ] **Step 3: Update `commands/fig_new.md` workflow handoff**

Replace the opening block with:

```markdown
> **Shared entry point.** `/fig_new` scaffolds a per-figure folder for the active
> quality-kernel workflow. After this command, the user or an LLM authors
> semantic TikZ from `briefing.md`, optional `reference_image`, and optional
> `coordinate_hints.yaml`, then runs `/fig_compile`.
>
> See `docs/architecture-overview.md` for the layer model.
```

Replace the Step 4 handoff with:

```markdown
> "briefing 완료 - examples/<name>/briefing.md 에 기록됨. 필요하면 reference PNG를 저장하고
> spec.yaml.reference_image를 기록한 뒤 /fig_extract <name>을 실행하세요. 이후 briefing,
> reference, coordinate_hints.yaml을 근거로 semantic TikZ를 작성하고 /fig_compile <name>으로
> 검증합니다."
```

Replace the final line with:

```markdown
Next: author semantic TikZ from `briefing.md`; if target matching matters, run `/fig_extract <name>` first.
```

- [ ] **Step 4: Update `README.md`**

Use these text changes:

```markdown
The earlier prompt/image-gen orchestration helpers were removed from the active
plugin surface. Historical design notes remain under `docs/historical/`, but the
maintained product direction is `docs/quality-kernel-goal.md`.
```

Replace:

```markdown
v0.1 line is active; latest shipped plugin version is recorded in
`.claude-plugin/plugin.json`.
```

with:

```markdown
The latest shipped plugin version is recorded in `.claude-plugin/plugin.json`.
The active line is the v0.2 quality-kernel release with v0.3 authoring
grounding work in progress.
```

Replace the history sentence:

```markdown
The v0.1 prompt workflow remains available, but post-v0.1.7.2 development pivots toward a
durable quality kernel
```

with:

```markdown
The v0.1 prompt workflow is preserved only in historical docs; active
development is the durable quality kernel
```

- [ ] **Step 5: Update `skills/figure-agent/SKILL.md`**

In the YAML description, replace the sentence about frozen prompt/image-gen helpers with:

```yaml
description: Use for paper-figure quality, compile, export, and reproducibility gates around scientific schematics. A human or any LLM/tool may author the figure; figure-agent enforces Style Lock, compiles/exports, runs visual QA checks, and reports stale or unreplayable figure state. Deleted v0.1 prompt/image-gen commands are historical only. Symbolic schematic axes are inside scope; quantitative data plots and measured datasets belong in matplotlib / Graph_making_hub.
```

Replace:

```markdown
Prompt/image-gen orchestration from v0.1 remains available but frozen.
```

with:

```markdown
Prompt/image-gen orchestration from v0.1 is historical only in this plugin line.
Do not route users to deleted commands.
```

- [ ] **Step 6: Update marketplace and pyproject descriptions**

In repository root `.claude-plugin/marketplace.json`, use:

```json
"description": "Local marketplace for the figure-agent plugin (paper-figure quality kernel)."
```

and:

```json
"description": "Paper-figure quality kernel for semantic TikZ compile, checks, export, and reproducibility."
```

In `plugins/figure-agent/pyproject.toml`, use:

```toml
description = "Claude Code plugin: paper-figure quality kernel for semantic TikZ compile, checks, export, and reproducibility."
```

- [ ] **Step 7: Verify release contract tests pass**

Run:

```bash
uv run pytest tests/test_release_contract.py -q
```

Expected: all tests in the file pass.

- [ ] **Step 8: Commit Task 5**

From repository root:

```bash
git add plugins/figure-agent/commands/fig_new.md plugins/figure-agent/README.md plugins/figure-agent/skills/figure-agent/SKILL.md .claude-plugin/marketplace.json plugins/figure-agent/pyproject.toml plugins/figure-agent/tests/test_release_contract.py
git commit -m "docs: remove deleted legacy command drift"
```

## Task 6: Verify Golden Fixture Status Honestly

**Files:**

- Modify: none unless commands generate ignored build artifacts.

- [ ] **Step 1: Check figure status**

Run from `plugins/figure-agent`:

```bash
uv run python3 scripts/status.py examples/golden_trap_depth_picture
```

Expected status must still identify the fixture as not accepted unless a separate human visual acceptance process happened:

```text
stage 4/4 (not accepted)
```

- [ ] **Step 2: Run accepted-mode artifact checker**

Run:

```bash
uv run python3 scripts/check_golden_artifacts.py examples/golden_trap_depth_picture --min-svg-elements 80 --min-png-width 1600
```

Expected current outcome may still fail because `accepted: false`, stale audit, or unresolved visual clashes are real known gaps. Record the exact output in the PR or final handoff. Do not suppress the failure unless the figure was actually accepted by a separate visual QA pass.

- [ ] **Step 3: Run strict visual checkers for evidence**

Run:

```bash
uv run python3 scripts/check_collisions.py --strict examples/golden_trap_depth_picture/build/golden_trap_depth_picture.pdf
uv run python3 scripts/check_visual_clash.py --strict examples/golden_trap_depth_picture/build/golden_trap_depth_picture.pdf
uv run python3 scripts/check_layout_drift.py --strict examples/golden_trap_depth_picture
```

Expected:

- collision checker should pass if no text overlaps exist.
- visual clash and layout drift may fail until the actual figure geometry is improved.

Record exact counts in the handoff.

- [ ] **Step 4: Leave evidence output uncommitted in this plan**

This task should only generate ignored build artifacts and terminal output. Do not commit
anything for Task 6. Put exact checker output in the final handoff instead.

## Task 7: Full Verification and Merge Handoff

**Files:** none, except generated caches ignored by git.

- [ ] **Step 1: Run full tests**

Run from `plugins/figure-agent`:

```bash
uv run pytest -q
```

Expected:

```text
passed
```

Exact count should be 190+ if Tasks 3-5 added the tests above.

- [ ] **Step 2: Run lint**

```bash
uv run ruff check .
```

Expected:

```text
All checks passed!
```

- [ ] **Step 3: Check lock consistency**

```bash
uv lock --check
```

Expected:

```text
Resolved
```

- [ ] **Step 4: Run plugin validation**

Run from `plugins/figure-agent`:

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all three validation commands pass.

- [ ] **Step 5: Check whitespace and status**

Run from repository root:

```bash
git diff --check HEAD
git status --short
```

Expected:

```text
```

`git status --short` should show no uncommitted tracked or untracked files except intentionally ignored build outputs.

- [ ] **Step 6: Merge handoff**

Write the final implementation handoff with:

- branch name
- commit list
- exact test results
- exact golden strict-gate failures that remain
- statement that `accepted: true` was not set

Merge only after the other Claude session's branch has landed or after its dirty files are reconciled:

```bash
cd /Users/choemun-yeong/workspace/ResearchOS/[figure-agent]
git fetch --all --prune
git status --short
git merge fix/v0-3-review-blockers
```

If conflicts occur, resolve only the files listed in this plan unless the conflicting branch modified the same contract surface.

## Completion Criteria

- Snippet files are tracked and no tracked TeX source depends on untracked local files.
- `\PolymerChain` is recognized by Style Lock.
- Golden fixture compiles from tracked files.
- Public docs do not route users to deleted `/fig_prompt` or `/fig_preview_select` commands.
- Package and marketplace descriptions name the quality-kernel direction.
- Golden fixture remains honestly marked not accepted until visual strict gates are resolved and human visual acceptance happens.
- Full pytest, ruff, lock check, plugin validation, and diff whitespace checks have recorded outputs.
