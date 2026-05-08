"""Emit the L4.5 vision-critique brief from briefing.md + TikZ + rendered PNG.

Produces the prompt-context block consumed by the `/fig_critique <name>` slash
command. The host Claude Code main loop reads the brief together with the
build PNG (via the Read tool) and writes the structured critique to
`examples/<name>/critique.md` (YAML front-matter + Markdown summary, schema
v1). No external API is called; the brief itself is API-free.

Successor to the v0.1 `review_brief.py` (HALT-then-paste workflow); see
`docs/architecture-v0.2-proposal.md` §4.5 for the rename + extend rationale.
"""

from __future__ import annotations

import sys
from pathlib import Path

from inputs import parse_briefing, parse_spec

MISSING_INVARIANTS = (
    "(none provided — critic should infer plausible physics constraints from §1+§2)"
)
STYLE_LOCK_PATH = Path(__file__).resolve().parent.parent / "styles" / "polymer-paper-preamble.sty"


class CritiqueBriefError(Exception):
    """Expected user-facing error while preparing the critique brief."""


def _require_file(path: Path, hint: str | None = None) -> None:
    if path.exists():
        return
    message = f"missing {path}"
    if hint:
        message = f"{message}; {hint}"
    raise FileNotFoundError(message)


def _author_intent(sections: dict[int, tuple[str, str]]) -> str:
    topic = sections.get(1, ("", ""))[1].strip()
    composition = sections.get(3, ("", ""))[1].strip()
    semantic_constraints = sections.get(7, ("", ""))[1].strip()
    parts = [part for part in [topic, composition, semantic_constraints] if part]
    return "\n\n".join(parts) if parts else "(briefing.md §1 and §3 are empty)"


def _example_relative_path(example_dir: Path, path: Path) -> str:
    return str(Path("examples") / example_dir.name / path.relative_to(example_dir))


def _require_fresh_png(png_path: Path, source_paths: tuple[Path, ...]) -> None:
    png_mtime = png_path.stat().st_mtime
    stale_sources = [path for path in source_paths if path.stat().st_mtime > png_mtime]
    if stale_sources:
        names = ", ".join(path.name for path in stale_sources)
        raise CritiqueBriefError(
            f"stale render {png_path}; newer source file(s): {names}; run /fig_compile first"
        )


def _reference_image_path(example_dir: Path, spec: dict) -> Path | None:
    """Locate reference image. spec.yaml reference_image takes precedence over directory scan."""
    ref_image_str = spec.get("reference_image")
    if ref_image_str:
        candidate = example_dir / ref_image_str
        if candidate.is_file():
            return candidate
    # Fallback: scan reference/ directory
    ref_dir = example_dir / "reference"
    if not ref_dir.is_dir():
        return None
    for candidate in [ref_dir / "golden_target_001.png"] + sorted(ref_dir.glob("*.png")):
        if candidate.exists():
            return candidate
    return None


def _critique_source_paths(tex_path: Path, briefing_path: Path) -> tuple[Path, ...]:
    paths = [tex_path, briefing_path]
    if STYLE_LOCK_PATH.exists():
        paths.append(STYLE_LOCK_PATH)
    return tuple(paths)


def _line_numbered(text: str) -> str:
    if not text.endswith("\n"):
        text += "\n"
    return "".join(
        f"{line_number:4d}: {line}\n" for line_number, line in enumerate(text.splitlines(), start=1)
    )


def generate_for(example_dir: Path) -> str:
    """Compose the reviewer brief for one `examples/<name>` directory."""
    if not example_dir.is_dir():
        raise FileNotFoundError(f"not a directory: {example_dir}")

    spec_path = example_dir / "spec.yaml"
    briefing_path = example_dir / "briefing.md"
    _require_file(spec_path)
    _require_file(briefing_path)

    spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    sections = parse_briefing(briefing_path.read_text(encoding="utf-8"))
    name = str(spec.get("name") or example_dir.name)

    tex_path = example_dir / f"{name}.tex"
    png_path = example_dir / "build" / f"{name}.png"
    _require_file(tex_path)
    _require_file(png_path, "run /fig_compile first")
    _require_fresh_png(png_path, _critique_source_paths(tex_path, briefing_path))

    tex = tex_path.read_text(encoding="utf-8")
    numbered_tex = _line_numbered(tex)
    invariants = sections.get(6, ("", ""))[1].strip() or MISSING_INVARIANTS
    render_path = _example_relative_path(example_dir, png_path)
    ref_image = _reference_image_path(example_dir, spec)
    ref_path = _example_relative_path(example_dir, ref_image) if ref_image else None

    ref_section = ""
    if ref_path:
        ref_section = f"""

**Reference image (for drift detection):** `{ref_path}`
(If the current render differs from reference, cite both in findings.
Use reference image as a tiebreaker in case of conflicting interpretations.)"""

    return f"""# Critique brief — {name}

**Render to inspect:** `{render_path}`
(The slash command loads this PNG into the host main loop via the Read tool.){ref_section}

## Author intent (from briefing.md)
{_author_intent(sections)}

## Physics invariants the figure MUST honor
{invariants}

## Source under review (TikZ)
```tex
{numbered_tex}```

## Critique rubric

### A. Physics correctness
- For each invariant in the section above, verify the rendered figure preserves it.
  Cite the .tex line numbers where a violation is seen.
- Check band ordering, arrow directions, label↔target binding, and any quantitative claim
  that contradicts the briefing.

### B. Aesthetic placement
- Label positioning: is each label clearly attached to its intended target? Is the offset
  consistent across labels of the same kind?
- Whitespace: does the figure feel cluttered or balanced?
- Visual hierarchy: are the most important elements visually dominant?
- Palette: are colors used consistently with their semantic role
  (e.g., blue=conduction, red=valence, amber=trap)?
- Nature-schematic style: minimal, sans-serif, no unnecessary text?

## Output format

Write findings to `examples/{name}/critique.md` with this exact structure
(YAML front-matter then human-readable Markdown body — schema v1):

```markdown
---
schema: figure-agent.critique.v1
fixture: {name}
generated_at: <ISO-8601 timestamp>
verdict: ready | revise | block
findings:
  - id: C001
    severity: BLOCKER | MAJOR | MINOR | NIT
    category: physics | label_placement | whitespace | hierarchy | palette | style
    tex_lines: [<int>, ...]
    observation: "<what is wrong, citing what you see in the PNG>"
    suggested_fix: "<concrete edit to the .tex>"
    status: open
---

# Vision Critique — {name}

<one-paragraph overall verdict, then per-finding prose discussion>
```

`verdict: ready` if zero BLOCKER + zero MAJOR findings; `revise` for any
MAJOR/MINOR; `block` only if a BLOCKER physics violation makes the figure
unsuitable for manuscript use. Critique is **report-only** for v0.2 — do
NOT auto-edit `<name>.tex`. See `docs/architecture-v0.2-proposal.md` §7.

---
(Generated by figure-agent /fig_critique for {name}. API-free; the host
Claude Code main loop reads the PNG and produces the critique using only
subscription tokens.)
"""


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: critique_brief.py <example_dir>", file=sys.stderr)
        return 2

    try:
        brief = generate_for(Path(sys.argv[1]))
    except (FileNotFoundError, CritiqueBriefError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(brief, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
