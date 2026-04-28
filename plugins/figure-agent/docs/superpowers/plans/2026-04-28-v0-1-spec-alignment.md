# figure-agent v0.1 Spec Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align implementation, command docs, and tests with the approved v0.1 identity: intent-controlled prompt generation plus human/LLM-in-the-loop vector finishing.

**Architecture:** Keep the plugin source-only and script-oriented for v0.1. Preserve existing script entrypoints, but change the prompt processing contract from security-first redaction to prompt normalization, and make `examples/<name>/build/` the canonical compile artifact path used by compile, checks, and export.

**Tech Stack:** Python 3.12 stdlib, pytest, ruff, bash, lualatex, Poppler tools (`pdftocairo`, `pdftotext`, `pdftoppm`), Claude plugin manifests.

---

## File Map

- Modify: `plugins/figure-agent/README.md`
  - Align public repo summary with v0.1 spec.
  - Remove automatic preview-to-vector reconstruction claims.
  - Document source-only/plugin-root execution policy.

- Modify: `plugins/figure-agent/skills/figure-agent/SKILL.md`
  - Align authoritative skill workflow with prompt normalization and human/LLM vector finishing.
  - Keep schematic/data-plot boundaries.

- Modify: `plugins/figure-agent/commands/fig_prompt.md`
  - Replace redaction/security wording with normalization/intent-control wording.
  - Document direct script invocation from plugin root.

- Modify: `plugins/figure-agent/commands/fig_compile.md`
  - Replace preview reconstruction wording with human/LLM-authored TikZ compile/check wording.
  - Make `build/<name>.pdf` the single check target.
  - Set plugin-root cwd as command convention.

- Modify: `plugins/figure-agent/commands/fig_export.md`
  - Make paths plugin-root-relative and consume `examples/<name>/build/<name>.pdf`.

- Modify: `plugins/figure-agent/commands/fig_new.md`
  - Change "Forbidden" framing to "Normalization / avoid literal overfit".
  - Remove optional `_reference_original/` from the default scaffold contract.

- Modify: `plugins/figure-agent/commands/fig_preview_select.md`
  - Set plugin-root cwd convention.

- Modify: `plugins/figure-agent/scripts/redact.py`
  - Keep the filename and `redact()` API for compatibility.
  - Change behavior to prompt normalization with audit events.
  - Normalize counts, sulfur-style sample labels/ranges, unitless geometry, units, composition ratios.
  - Preserve known domain terms and warn on data-plot drift signals.

- Modify: `plugins/figure-agent/scripts/prompt_gen.py`
  - Update user-facing labels from redacted prompt/audit to normalized prompt/audit.
  - Preserve direct script invocation as the v0.1 contract.

- Modify: `plugins/figure-agent/scripts/compile.sh`
  - Compile into `examples/<name>/build/`.
  - Do not create root-level generated PDF/PNG next to the source.

- Modify: `plugins/figure-agent/tests/test_redact.py`
  - Update old redaction expectations to normalization expectations.
  - Add coverage for `4 dots`, `three layers`, `S60-S85`, and `width 200 by 50 pixels`.
  - Preserve bilingual coverage and add negative tests for legitimate domain tokens such as `C60`.

- Modify: `plugins/figure-agent/tests/test_prompt_gen.py`
  - Update prompt/audit wording expectations if needed.
  - Add one test that `generate_for()` returns normalized count/sample/geometry details.

- Create: `plugins/figure-agent/tests/test_compile_contract.py`
  - Fixture-driven smoke test for canonical build output.
  - Skip cleanly when external LaTeX/Poppler binaries are missing.

- Modify: `plugins/figure-agent/pyproject.toml`
  - Mark Python packaging as source-only / no importable package discovery.

---

### Task 1: Lock v0.1 Documentation Contract

**Files:**
- Modify: `plugins/figure-agent/README.md`
- Modify: `plugins/figure-agent/skills/figure-agent/SKILL.md`
- Modify: `plugins/figure-agent/commands/fig_prompt.md`
- Modify: `plugins/figure-agent/commands/fig_compile.md`
- Modify: `plugins/figure-agent/commands/fig_export.md`
- Modify: `plugins/figure-agent/commands/fig_new.md`
- Modify: `plugins/figure-agent/commands/fig_preview_select.md`

- [ ] **Step 1: Search stale contract terms**

Run:

```bash
rg -n "redacted|redaction|security|vector reconstruct|reconstructs selected|selected preview →|inside examples|human-authored|_reference_original|automatic redaction" plugins/figure-agent/README.md plugins/figure-agent/skills/figure-agent/SKILL.md plugins/figure-agent/commands
```

Expected before changes: matches in README, SKILL, and command docs.

- [ ] **Step 2: Update README identity**

Replace the current responsibility block with this wording:

```markdown
**Plugin responsibility (two only):**
1. **Prompt intent control** — turn research intent into image-gen-ready schematic prompts. Preserve scientific mechanism and visual intent; normalize literals that make image-gen overfit to counts, sample codes, dimensions, or experimental conditions.
2. **Human/LLM-in-the-loop vector finishing** — selected preview is visual inspiration only. The final TikZ source is authored by a human, an LLM, or both; the plugin provides deterministic compile, Style Lock, collision/visual-clash checks, and export.
```

Replace workflow lines with:

```markdown
/fig_prompt                → normalized prompt (copy → external tool → save to previews/)
/fig_compile               → compile human/LLM-authored TikZ + Style Lock + clash checks
```

Add under `Status`:

```markdown
v0.1 is source-only as a Claude Code plugin. Use `claude plugin validate`, `uv run pytest`, and `uv run ruff`; `uv build` is not a release gate.
```

- [ ] **Step 3: Update SKILL identity**

Replace responsibility lines with:

```markdown
1. **Prompt intent control** — produce one prompt block that preserves the author's scientific mechanism and visual hierarchy while normalizing distracting literals such as exact counts, sample labels, dimensions, and experimental conditions.
2. **Human/LLM-in-the-loop vector finishing** — selected preview is inspiration only. v0.1 does not automatically vectorize preview images; it compiles/checks/exports TikZ authored by a human, an LLM, or both.
```

Replace `/fig_prompt` workflow wording:

```markdown
   → applies prompt normalization (not security-first redaction)
   → outputs ONE prompt block + normalization audit
```

Replace `/fig_compile` workflow wording:

```markdown
   → compiles examples/<name>/<name>.tex into examples/<name>/build/
   → runs check_collisions.py + check_visual_clash.py on build/<name>.pdf
```

Replace "What the prompt must contain" bullets:

```markdown
- Domain vocabulary and mechanism terms that must be preserved
- Style block (Nature schematic, white background, minimal labels, balanced composition)
- Composition hint (panel layout, flow direction, arrow semantics)
- Normalization policy (generalize distracting literals; preserve schematic intent)
- Normalization audit (what was generalized, kept, or warned)
```

Replace "What the compile must guarantee" with:

```markdown
- Selected preview is inspiration only, not copied verbatim.
- Final `.tex` source remains editable and independent.
- Compile/check/export all use `examples/<name>/build/<name>.pdf` as the canonical PDF.
- Labels precise enough for clash checks.
- Style Lock honored (no ad-hoc font/color unless explicitly justified).
```

- [ ] **Step 4: Update command docs cwd and scope**

Apply these command-level rules:

```markdown
**Usage**: run from the plugin root.
```

For `/fig_prompt`, use:

```markdown
Run: `uv run python3 scripts/prompt_gen.py examples/<name>`
```

For `/fig_compile`, use:

```markdown
Run: `bash scripts/compile.sh examples/<name>/<name>.tex`
Check target: `examples/<name>/build/<name>.pdf`
```

For `/fig_export`, use:

```markdown
Run: `bash scripts/export_svg.sh examples/<name>/build/<name>.pdf examples/<name>/exports/<name>.svg`
Run: `pdftocairo -tiff -r 600 -singlefile examples/<name>/build/<name>.pdf examples/<name>/exports/<name>`
```

For `/fig_new`, change question 4 to:

```markdown
4. **§4 Normalize / avoid literal overfit** — "외부 imagegen이 숫자/샘플명/조건에 과하게 끌려가면 안 되는 항목은? (예: 정확 수치, sample code, dimension, count)"
```

Remove this default scaffold bullet:

```markdown
- (optional) `_reference_original/` if the user provides a benchmark figure to compare against
```

- [ ] **Step 5: Verify docs no longer overclaim**

Run:

```bash
rg -n "security-first|automatic redaction|vector reconstruct|reconstructs selected|selected preview →|inside examples/<name>|_reference_original" plugins/figure-agent/README.md plugins/figure-agent/skills/figure-agent/SKILL.md plugins/figure-agent/commands
```

Expected: no matches, except intentional "does not automatically vectorize/reconstruct" wording if present.

- [ ] **Step 6: Commit documentation contract**

Run:

```bash
git add plugins/figure-agent/README.md plugins/figure-agent/skills/figure-agent/SKILL.md plugins/figure-agent/commands
git commit -m "docs: align figure-agent v0.1 contract"
```

If the user has requested no commits in the active session, skip the commit and report the staged file list instead.

---

### Task 2: Add Prompt Normalization Tests

**Files:**
- Modify: `plugins/figure-agent/tests/test_redact.py`
- Modify: `plugins/figure-agent/tests/test_prompt_gen.py`

- [ ] **Step 1: Replace old redaction assertions with normalization assertions**

In `tests/test_redact.py`, update helper names and expectations:

```python
def _categories(audit) -> list[str]:
    return [ev.category for ev in audit]
```

Keep the helper, but assert normalized replacements instead of `[REDACTED:*]`.

- [ ] **Step 2: Add count normalization tests**

Append:

```python
def test_numeric_count_phrase_normalized():
    out, audit = redact("Use 4 dots for trapped electrons.")
    assert "a few dots" in out
    assert "4 dots" not in out
    assert "count" in _categories(audit)


def test_english_count_word_normalized():
    out, audit = redact("Show three layers with arrows.")
    assert "stacked layers" in out
    assert "three layers" not in out
    assert "count_word" in _categories(audit)
```

- [ ] **Step 3: Add sample label normalization test**

Append:

```python
def test_sample_label_range_normalized():
    out, audit = redact("Compare S60-S85 trapping behavior.")
    assert "different material compositions" in out
    assert "S60" not in out
    assert "S85" not in out
    assert "sample_label" in _categories(audit)


def test_non_sample_domain_tokens_are_kept():
    out, audit = redact("C60 fullerene, E11 transition, and T90 label remain domain text.")
    assert "C60 fullerene" in out
    assert "E11 transition" in out
    assert "T90 label" in out
    assert "material composition label" not in out
    assert all(ev.category != "sample_label" for ev in audit)
```

- [ ] **Step 4: Add unitless geometry normalization test**

Append:

```python
def test_unitless_geometry_phrase_normalized():
    out, audit = redact("Gate width 200 by 50 pixels near the center.")
    assert "general geometry" in out
    assert "200 by 50" not in out
    assert "geometry" in _categories(audit)
```

- [ ] **Step 5: Add thin-film, bilingual, and ratio tests**

Append:

```python
def test_thin_film_dimension_normalized_to_visual_role():
    out, audit = redact("Use a 200 nm film under the electrode.")
    assert "thin film" in out
    assert "200 nm" not in out
    assert "length" in _categories(audit)


def test_ratio_generalized_but_audited():
    out, audit = redact("PVDF-TrFE 70/30 copolymer")
    assert "copolymer material" in out
    assert "70/30" not in out
    assert "composition_ratio" in _categories(audit)


def test_korean_count_unit_normalized():
    out1, audit1 = redact("trapped electrons (4개 점)")
    assert "a few visual elements" in out1
    assert any(ev.category == "count" for ev in audit1)

    out2, audit2 = redact("두 종 dielectric")
    assert out2 == "두 종 dielectric"
    assert audit2 == []
```

- [ ] **Step 6: Add KEPT/WARN audit tests**

Append:

```python
def _actions(audit) -> list[str]:
    return [getattr(ev, "action", "NORMALIZED") for ev in audit]


def test_domain_terms_are_audited_as_kept():
    out, audit = redact("Use CB, VB, HOMO, LUMO, E_t, and kT in the schematic.")
    assert "CB" in out and "VB" in out
    assert "HOMO" in out and "LUMO" in out
    assert "E_t" in out and "kT" in out
    assert "KEPT" in _actions(audit)


def test_data_plot_signal_warns_without_rewriting():
    out, audit = redact("Plot n vs composition with error bars.")
    assert "vs composition" in out
    assert "error bars" in out
    assert "WARN" in _actions(audit)
```

- [ ] **Step 7: Add prompt generator integration test**

Append to `tests/test_prompt_gen.py`:

```python
def test_generate_for_normalizes_prompt_literals(tmp_path):
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    (example_dir / "spec.yaml").write_text(
        "name: demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: S60-S85 comparison\n"
        "style_profile: polymer-default\n"
        "selected_preview: null\n",
        encoding="utf-8",
    )
    (example_dir / "briefing.md").write_text(
        "## 1. Topic\n\n"
        "Show S60-S85 charge retention mechanism.\n\n"
        "## 2. Vocabulary\n\n"
        "deep trap, shallow trap, CB, VB\n\n"
        "## 3. Composition\n\n"
        "Use 4 dots in three layers. Gate width 200 by 50 pixels.\n\n"
        "## 4. Forbidden\n\n"
        "skip\n\n"
        "## 5. Style notes\n\n"
        "skip\n",
        encoding="utf-8",
    )
    prompt, audit = generate_for(example_dir)
    assert "deep trap" in prompt
    assert "different material compositions" in prompt
    assert "a few dots" in prompt
    assert "stacked layers" in prompt
    assert "general geometry" in prompt
    assert "S60" not in prompt
    assert "200 by 50" not in prompt
    assert {ev.category for ev in audit} >= {"sample_label", "count", "count_word", "geometry"}
```

- [ ] **Step 8: Run tests and confirm they fail before implementation**

Run:

```bash
cd plugins/figure-agent
uv run pytest tests/test_redact.py tests/test_prompt_gen.py -q
```

Expected: failures showing current `redact.py` still emits `[REDACTED:*]`, leaves new literals unchanged, or lacks KEPT/WARN audit actions.

---

### Task 3: Implement Prompt Normalization

**Files:**
- Modify: `plugins/figure-agent/scripts/redact.py`
- Modify: `plugins/figure-agent/scripts/prompt_gen.py`

- [ ] **Step 1: Update module docstring and event wording**

Replace the `redact.py` module docstring with:

```python
"""Normalize prompt literals that make external image-gen overfit.

The filename and `redact()` API are kept for v0.1 compatibility, but the design
contract is prompt normalization / intent control:
- preserve scientific mechanism terms;
- generalize counts, sample labels, dimensions, and exact conditions that tend
  to make image-gen produce cluttered or data-plot-like drafts;
- return an audit of what changed.
"""
```

- [ ] **Step 2: Add normalization pattern tables**

Add an `action` field to `RedactionEvent` so the audit can distinguish normalized, kept, and warning entries:

```python
@dataclass
class RedactionEvent:
    original: str
    replacement: str
    category: str
    span: tuple[int, int]
    action: str = "NORMALIZED"
```

Existing tests that read `ev.category` should keep working.

Add below imports:

```python
_NUMBER_WORDS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen"
)

_COUNT_NOUNS = (
    "dots?|points?|particles?|electrons?|charges?|layers?|panels?|arrows?|"
    "bands?|levels?|blocks?|stacks?"
)

_NORMALIZATION_PATTERNS: list[tuple[str, str, str]] = [
    (r"\b\d+(?:\.\d+)?\s*(?:µm|um|nm|mm|cm|m|Å)\s+film\b", "thin film", "length"),
    (rf"\b(?:{_NUMBER_WORDS})\s+layers?\b", "stacked layers", "count_word"),
    (rf"\b(?:{_NUMBER_WORDS})\s+panels?\b", "multi-panel layout", "count_word"),
    (rf"\b(?:{_NUMBER_WORDS})\s+(?:{_COUNT_NOUNS})\b", "a few visual elements", "count_word"),
    (rf"\b\d+\s+dots?\b", "a few dots", "count"),
    (rf"\b\d+\s+electrons?\b", "a few electrons", "count"),
    (rf"\b\d+\s+layers?\b", "stacked layers", "count"),
    (rf"\b\d+\s+panels?\b", "multi-panel layout", "count"),
    (rf"\b\d+\s+(?:{_COUNT_NOUNS})\b", "a few visual elements", "count"),
    (r"\bS\d{2,3}\s*[-–]\s*S?\d{2,3}\b", "different material compositions", "sample_label"),
    (r"\bS\d{2,3}\s*/\s*S?\d{2,3}\b", "different material compositions", "sample_label"),
    (r"\bS\d{2,3}\b", "material composition label", "sample_label"),
    (
        r"\b(?:width|height|depth|diameter|radius|length|spacing|thickness)\s+"
        r"\d+(?:\.\d+)?(?:\s+by\s+\d+(?:\.\d+)?)?(?:\s*[A-Za-zµ°%]+)?\b",
        "general geometry",
        "geometry",
    ),
    (r"\b\d+\s*[:/]\s*\d+\s+copolymer\b", "copolymer material", "composition_ratio"),
    (r"\b\d+\s*[:/]\s*\d+\b", "relative composition ratio", "composition_ratio"),
]

_DOMAIN_TERMS = ("CB", "VB", "HOMO", "LUMO", "E_t", "kT")
_WARN_PATTERNS: list[tuple[str, str]] = [
    (r"\bvs\s+(?:composition|time|temperature|voltage|frequency)\b", "data_plot_signal"),
    (r"\b(?:raw\s*\+\s*fit|error bars?|peak position|sweep)\b", "data_plot_signal"),
]
```

- [ ] **Step 3: Replace `redact()` body with ordered normalization**

Use this implementation shape:

```python
def redact(text: str) -> tuple[str, list[RedactionEvent]]:
    """Normalize prompt literals and return (normalized_text, audit)."""
    audit: list[RedactionEvent] = []
    normalized = text

    for term in _DOMAIN_TERMS:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", text):
            audit.append(
                RedactionEvent(
                    original=term,
                    replacement=term,
                    category="domain_term",
                    span=(-1, -1),
                    action="KEPT",
                )
            )

    for src, category in _WARN_PATTERNS:
        for match in re.finditer(src, text, flags=re.IGNORECASE):
            audit.append(
                RedactionEvent(
                    original=match.group(0),
                    replacement=match.group(0),
                    category=category,
                    span=match.span(),
                    action="WARN",
                )
            )

    for src, replacement, category in _NORMALIZATION_PATTERNS:
        pattern = re.compile(src, re.IGNORECASE)

        def _replace(match: re.Match[str]) -> str:
            audit.append(
                RedactionEvent(
                    original=match.group(0),
                    replacement=replacement,
                    category=category,
                    span=match.span(),
                    action="NORMALIZED",
                )
            )
            return replacement

        normalized = pattern.sub(_replace, normalized)

    out_chunks: list[str] = []
    last = 0
    for m in _COMBINED.finditer(normalized):
        out_chunks.append(normalized[last : m.start()])
        for i, (_, cat) in enumerate(_UNIT_PATTERNS):
            if m.group(f"g{i}"):
                rep = _unit_replacement(cat, m.group(0))
                out_chunks.append(rep)
                audit.append(RedactionEvent(m.group(0), rep, cat, m.span(), "NORMALIZED"))
                break
        last = m.end()
    out_chunks.append(normalized[last:])
    return "".join(out_chunks), audit
```

Add `_unit_replacement()` before `redact()`:

```python
def _unit_replacement(category: str, original: str) -> str:
    lowered = original.lower()
    if category == "length" and "film" in lowered:
        return "thin film"
    replacements = {
        "composition": "material composition",
        "voltage": "applied voltage condition",
        "current": "current condition",
        "frequency": "frequency condition",
        "length": "general dimension",
        "temperature": "thermal condition",
        "time": "time condition",
        "pressure": "pressure condition",
        "force": "force condition",
        "energy_power": "energy/power condition",
        "resolution": "export resolution",
        "count": "a few visual elements",
    }
    return replacements.get(category, f"generalized {category}")
```

- [ ] **Step 4: Update audit formatter**

Replace `format_audit()` with:

```python
def format_audit(audit: list[RedactionEvent]) -> str:
    if not audit:
        return "(no normalizations)"
    lines = []
    for ev in audit:
        if ev.action == "KEPT":
            lines.append(f"  KEPT [{ev.category}]: {ev.original!r}")
        elif ev.action == "WARN":
            lines.append(f"  WARN [{ev.category}]: {ev.original!r} (review intent)")
        else:
            lines.append(f"  NORMALIZED [{ev.category}]: {ev.original!r} -> {ev.replacement!r}")
    return "\n".join(lines)
```

- [ ] **Step 5: Update `prompt_gen.py` labels**

Replace:

```python
print("=== REDACTED PROMPT (copy below for external tool) ===")
print("\n=== Redaction audit ===", file=sys.stderr)
"\n⚠️  Review the prompt for any remaining sensitive content before "
"sending to an external service.",
```

with:

```python
print("=== NORMALIZED PROMPT (copy below for external tool) ===")
print("\n=== Normalization audit ===", file=sys.stderr)
"\nReview the prompt for intent drift before sending it to an external image-gen tool.",
```

- [ ] **Step 6: Run focused tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest tests/test_redact.py tests/test_prompt_gen.py -q
```

Expected: all focused tests pass.

- [ ] **Step 7: Commit prompt normalization**

Run:

```bash
git add plugins/figure-agent/scripts/redact.py plugins/figure-agent/scripts/prompt_gen.py plugins/figure-agent/tests/test_redact.py plugins/figure-agent/tests/test_prompt_gen.py
git commit -m "feat: normalize schematic prompts"
```

If the user has requested no commits in the active session, skip the commit and report the changed file list.

---

### Task 4: Make `build/` the Canonical Compile Output

**Files:**
- Modify: `plugins/figure-agent/scripts/compile.sh`
- Create: `plugins/figure-agent/tests/test_compile_contract.py`

- [ ] **Step 1: Write the compile contract test**

Create `tests/test_compile_contract.py`:

```python
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("lualatex") is None, reason="lualatex not installed")
@pytest.mark.skipif(shutil.which("pdftocairo") is None, reason="pdftocairo not installed")
def test_compile_writes_only_to_build_dir(tmp_path):
    fig_dir = tmp_path / "demo"
    fig_dir.mkdir()
    tex_path = fig_dir / "demo.tex"
    tex_path.write_text(
        r"""\documentclass[border=2pt]{standalone}
\usepackage{polymer-paper-preamble}
\begin{document}
\begin{tikzpicture}
\node at (0,0) {demo};
\end{tikzpicture}
\end{document}
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (fig_dir / "build" / "demo.pdf").exists()
    assert (fig_dir / "build" / "demo.png").exists()
    assert not (fig_dir / "demo.pdf").exists()
    assert not (fig_dir / "demo.png").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd plugins/figure-agent
uv run pytest tests/test_compile_contract.py -q
```

Expected: failure because current `compile.sh` writes next to `demo.tex`.

- [ ] **Step 3: Update `compile.sh`**

Replace lines after file existence validation with:

```bash
TEX_INPUT="$(cd "$(dirname "$TEX_INPUT")" && pwd)/$(basename "$TEX_INPUT")"
ENGINE="${LATEX_ENGINE:-lualatex}"

SRC_DIR="$(dirname "$TEX_INPUT")"
FILE="$(basename "$TEX_INPUT")"
BASE="${FILE%.tex}"
BUILD_DIR="${SRC_DIR}/build"
mkdir -p "$BUILD_DIR"

cd "$SRC_DIR"
"$ENGINE" -interaction=nonstopmode -output-directory="$BUILD_DIR" "$FILE"
pdftocairo -png -r 600 -singlefile "${BUILD_DIR}/${BASE}.pdf" "${BUILD_DIR}/${BASE}"

echo "Generated: ${BUILD_DIR}/${BASE}.pdf, ${BUILD_DIR}/${BASE}.png (engine: $ENGINE)"
```

- [ ] **Step 4: Run compile contract test**

Run:

```bash
cd plugins/figure-agent
uv run pytest tests/test_compile_contract.py -q
```

Expected: pass or skip only if LaTeX/Poppler is unavailable. A skip is acceptable for regular unit-test portability, but final v0.1 verification still requires a real compile/check/export smoke command in Task 7.

- [ ] **Step 5: Clean stale root artifacts from dogfood example**

Remove tracked generated root artifacts if they are not intentional release artifacts:

```bash
git rm plugins/figure-agent/examples/fig3_trapping_concept/fig3_trapping_concept.pdf plugins/figure-agent/examples/fig3_trapping_concept/fig3_trapping_concept.png
```

Do not remove source files, previews, or `.gitkeep` files.

- [ ] **Step 6: Commit compile contract**

Run:

```bash
git add plugins/figure-agent/scripts/compile.sh plugins/figure-agent/tests/test_compile_contract.py
git commit -m "fix: compile figures into build directory"
```

If dogfood root artifacts were removed:

```bash
git add -u plugins/figure-agent/examples/fig3_trapping_concept
git commit -m "chore: remove stale root figure artifacts"
```

If the user has requested no commits in the active session, skip commits and report the changed file list.

---

### Task 5: Add Export and Analyzer Smoke Coverage

**Files:**
- Modify: `plugins/figure-agent/tests/test_compile_contract.py`

- [ ] **Step 1: Extend the compile test with analyzer checks**

Append to `tests/test_compile_contract.py`:

```python
@pytest.mark.skipif(shutil.which("lualatex") is None, reason="lualatex not installed")
@pytest.mark.skipif(shutil.which("pdftocairo") is None, reason="pdftocairo not installed")
@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext not installed")
@pytest.mark.skipif(shutil.which("pdftoppm") is None, reason="pdftoppm not installed")
def test_checks_and_export_consume_build_pdf(tmp_path):
    fig_dir = tmp_path / "demo"
    fig_dir.mkdir()
    tex_path = fig_dir / "demo.tex"
    tex_path.write_text(
        r"""\documentclass[border=2pt]{standalone}
\usepackage{polymer-paper-preamble}
\begin{document}
\begin{tikzpicture}
\node at (0,0) {demo};
\end{tikzpicture}
\end{document}
""",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert compile_result.returncode == 0, compile_result.stderr + compile_result.stdout

    build_pdf = fig_dir / "build" / "demo.pdf"
    collision_result = subprocess.run(
        ["uv", "run", "python3", "scripts/check_collisions.py", str(build_pdf)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert collision_result.returncode == 0, collision_result.stderr + collision_result.stdout

    visual_result = subprocess.run(
        ["uv", "run", "python3", "scripts/check_visual_clash.py", str(build_pdf), "--dpi", "150"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert visual_result.returncode == 0, visual_result.stderr + visual_result.stdout

    export_dir = fig_dir / "exports"
    export_dir.mkdir()
    svg_path = export_dir / "demo.svg"
    export_result = subprocess.run(
        ["bash", "scripts/export_svg.sh", str(build_pdf), str(svg_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert export_result.returncode == 0, export_result.stderr + export_result.stdout
    assert svg_path.exists()
```

- [ ] **Step 2: Run smoke coverage**

Run:

```bash
cd plugins/figure-agent
uv run pytest tests/test_compile_contract.py -q
```

Expected: pass or skip only when external binaries are absent. A skip is acceptable for regular unit-test portability, but final v0.1 verification still requires a real compile/check/export smoke command in Task 7.

- [ ] **Step 3: Commit smoke coverage**

Run:

```bash
git add plugins/figure-agent/tests/test_compile_contract.py
git commit -m "test: cover compile check export path"
```

If the user has requested no commits in the active session, skip the commit and report the changed file list.

---

### Task 6: Declare Source-only Python Packaging Policy

**Files:**
- Modify: `plugins/figure-agent/pyproject.toml`
- Modify: `plugins/figure-agent/README.md`

- [ ] **Step 1: Add setuptools discovery suppression**

Add below `[project]` dependencies in `pyproject.toml`:

```toml
[tool.setuptools]
packages = []
py-modules = []
```

- [ ] **Step 2: Confirm `uv build` no longer fails due flat-layout discovery**

Run:

```bash
cd plugins/figure-agent
uv build
```

Expected: no `Multiple top-level packages discovered in a flat-layout` error.

If `uv build` succeeds, remove generated `dist/` after noting the result:

```bash
rm dist/.gitignore 2>/dev/null || true
rmdir dist 2>/dev/null || true
```

Use non-recursive removal only.

- [ ] **Step 3: Update README build policy**

Ensure README contains:

```markdown
## Build policy

This repo is a Claude Code plugin source tree, not a PyPI package. `uv` is used for dependency management, tests, and script execution. Release validation is `claude plugin validate`, `uv run pytest`, and `uv run ruff`; `uv build` is not a release artifact.
```

- [ ] **Step 4: Commit source-only packaging policy**

Run:

```bash
git add plugins/figure-agent/pyproject.toml plugins/figure-agent/README.md
git commit -m "chore: declare source-only plugin packaging"
```

If the user has requested no commits in the active session, skip the commit and report the changed file list.

---

### Task 7: Final Verification Sweep

**Files:**
- Read/verify only unless a failure points to a direct fix.

- [ ] **Step 1: Run Python tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q
```

Expected: all tests pass. Record exact pass count.

- [ ] **Step 2: Run lint**

Run:

```bash
cd plugins/figure-agent
uv run ruff check .
```

Expected: `All checks passed!`

- [ ] **Step 3: Validate plugin manifest**

Run:

```bash
cd plugins/figure-agent
claude plugin validate .claude-plugin/plugin.json
```

Expected: validation passed.

- [ ] **Step 4: Validate marketplace from repo root**

Run:

```bash
claude plugin validate .
```

Expected: validation passed.

- [ ] **Step 5: Run stale contract grep**

Run:

```bash
rg -n "automatic redaction|security-first|selected preview → SVG/TikZ deterministic reconstruction|vector reconstruct|inside examples/<name>" plugins/figure-agent/README.md plugins/figure-agent/skills/figure-agent/SKILL.md plugins/figure-agent/commands
rg -n -P "(?<!examples/<name>/)build/<name>\\.pdf" plugins/figure-agent/README.md plugins/figure-agent/skills/figure-agent/SKILL.md plugins/figure-agent/commands
```

Expected:
- no automatic vectorization claims;
- no command docs telling users to run from `examples/<name>/`;
- bare `build/<name>.pdf` does not appear in command-facing docs.

- [ ] **Step 6: Run real compile/check/export smoke**

This is a non-skippable local ship gate. If a required binary is missing, stop and report the missing binary as a blocker instead of declaring v0.1 verified.

Run:

```bash
cd plugins/figure-agent
tmpdir="$(mktemp -d)"
mkdir -p "$tmpdir/demo"
cat > "$tmpdir/demo/demo.tex" <<'EOF'
\documentclass[border=2pt]{standalone}
\usepackage{polymer-paper-preamble}
\begin{document}
\begin{tikzpicture}
\node at (0,0) {demo};
\end{tikzpicture}
\end{document}
EOF
bash scripts/compile.sh "$tmpdir/demo/demo.tex"
uv run python3 scripts/check_collisions.py "$tmpdir/demo/build/demo.pdf"
uv run python3 scripts/check_visual_clash.py "$tmpdir/demo/build/demo.pdf" --dpi 150
mkdir -p "$tmpdir/demo/exports"
bash scripts/export_svg.sh "$tmpdir/demo/build/demo.pdf" "$tmpdir/demo/exports/demo.svg"
test -f "$tmpdir/demo/build/demo.pdf"
test -f "$tmpdir/demo/build/demo.png"
test -f "$tmpdir/demo/exports/demo.svg"
test ! -f "$tmpdir/demo/demo.pdf"
test ! -f "$tmpdir/demo/demo.png"
```

Expected: all commands exit 0 and generated artifacts are under `build/` and `exports/`, not next to the `.tex` source.

- [ ] **Step 7: Check git cleanliness**

Run:

```bash
git status --short
```

Expected: only intentional modified files remain if commits were skipped; clean if commits were made.

---

## Self-review Checklist

- Spec coverage:
  - Prompt intent control covered by Tasks 1-3.
  - Human/LLM vector finishing contract covered by Tasks 1, 4, and 5.
  - Canonical `build/` artifact path covered by Tasks 1, 4, 5, and 7.
  - Source-only packaging covered by Task 6.
  - Final verification covered by Task 7.

- No intentional package-module migration:
  - `python -m scripts.prompt_gen` remains outside v0.1.
  - Direct script invocation remains the documented path.

- No automatic preview vectorization:
  - Plan does not implement image-to-vector reconstruction.
  - v0.2 direction remains documented only.

- Test-first order:
  - Prompt normalization tests are added before implementation.
  - Compile contract test is added before changing `compile.sh`.
