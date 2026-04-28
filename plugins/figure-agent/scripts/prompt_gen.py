"""Generate redacted external image-gen prompt from spec.yaml + briefing.md.

Reads `examples/<name>/{spec.yaml, briefing.md}`. Composes one prompt block
following figure-agent's house template, applies redaction, and prints
prompt to stdout + audit summary to stderr.

v0.1 scope: stdlib-only YAML subset parser (top-level scalars + `panels`
list of dicts), markdown section split by `## N. <title>` headers,
HTML-comment placeholder stripping.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# sys.path[0] is the script's directory when invoked as `python3 prompt_gen.py`,
# so a sibling-module import works without any package wiring.
from redact import format_audit, redact

_SECTION_HEADER = re.compile(r"^##\s+(\d+)\.\s+(.+)$", re.MULTILINE)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_BLOCKQUOTE = re.compile(r"^>\s.*$", re.MULTILINE)
_FOOTER_RULE = re.compile(r"^---\s*$", re.MULTILINE)
_MD_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ALLOW_HINT = re.compile(r"\b(?:ok|allowed|허용)\b|노출\s*ok", re.IGNORECASE)
_SKIP_TOKENS = {"skip", "(none)", "none", "(default)", "default", "n/a", "na", "-"}


def _is_skip(body: str) -> bool:
    """True if the body's first meaningful word is a skip-keyword."""
    if not body:
        return True
    first_line = body.strip().splitlines()[0].lstrip("-* ").strip()
    parts = first_line.split()
    first_word = parts[0].rstrip(".,!?:") if parts else ""
    return first_word.lower() in _SKIP_TOKENS


def _filter_allowed_hints(body: str) -> str:
    """Drop lines marking items as explicitly allowed (OK / 허용 / 노출 OK).
    These are user notes about what *is* fine to expose, not negative items."""
    if not body:
        return body
    return "\n".join(ln for ln in body.splitlines() if not _ALLOW_HINT.search(ln))


def parse_spec(text: str) -> dict:
    """Minimal YAML subset parser. Top-level scalars + `panels` list-of-dicts.

    Not a general parser; rejects anything outside the v0.1 spec.yaml shape.
    """
    spec: dict = {"panels": []}
    in_panels = False
    cur: dict | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("panels:"):
            in_panels = True
            continue
        if in_panels:
            if line.startswith("  - "):
                if cur is not None:
                    spec["panels"].append(cur)
                cur = {}
                key, _, val = line[4:].partition(":")
                cur[key.strip()] = val.strip()
                continue
            if line.startswith("    ") and cur is not None:
                key, _, val = line.strip().partition(":")
                cur[key.strip()] = val.strip()
                continue
            # Exit panels block.
            if cur is not None:
                spec["panels"].append(cur)
                cur = None
            in_panels = False
        if not in_panels and ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            spec[key.strip()] = val.strip()
    if cur is not None:
        spec["panels"].append(cur)
    return spec


def parse_briefing(text: str) -> dict[int, tuple[str, str]]:
    """Split briefing.md into {section_number: (title, body)}.

    Strips top-of-file blockquote (dogfooding note), HTML-comment TODO hints,
    and trims whitespace. A section whose body is empty after stripping is
    returned with body == "" so the caller can decide how to surface it.
    """
    text = _BLOCKQUOTE.sub("", text)
    sections: dict[int, tuple[str, str]] = {}
    matches = list(_SECTION_HEADER.finditer(text))
    for i, m in enumerate(matches):
        n = int(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end]
        # Cut at first horizontal rule — footer instructions live below the rule.
        rule = _FOOTER_RULE.search(section_text)
        if rule is not None:
            section_text = section_text[: rule.start()]
        body = _HTML_COMMENT.sub("", section_text).strip()
        sections[n] = (title, body)
    return sections


def _bullet_block(body: str) -> str:
    """Convert a free-form body into a bullet list.

    - Strips markdown bold (`**foo**` → `foo`) so external tools see plain text.
    - Existing `- ` / `* ` lines kept; other paragraphs become one bullet each.
    """
    if not body:
        return "- (not specified — fill briefing.md)"
    lines = [_MD_BOLD.sub(r"\1", ln.strip()) for ln in body.splitlines() if ln.strip()]
    out: list[str] = []
    for ln in lines:
        if ln.startswith("- "):
            out.append(ln)
        elif ln.startswith("* "):
            out.append("- " + ln[2:])
        else:
            out.append(f"- {ln}")
    return "\n".join(out)


def compose_prompt(spec: dict, briefing: dict[int, tuple[str, str]]) -> str:
    name = spec.get("name", "(unnamed)")
    panels = spec.get("panels", [])
    panel_summary = (
        ", ".join(f"({p.get('id', '?')}) {p.get('caption', '')}".strip() for p in panels)
        if panels
        else "single panel"
    )

    topic = briefing.get(1, ("", ""))[1] or "(topic missing — fill briefing §1)"
    vocab = briefing.get(2, ("", ""))[1]
    composition = briefing.get(3, ("", ""))[1]
    forbidden = briefing.get(4, ("", ""))[1]
    style_extra = briefing.get(5, ("", ""))[1]

    header = "Create a clean white-background Nature-style scientific schematic."

    parts: list[str] = [
        header,
        "",
        "Topic:",
        topic,
        "",
        f"Layout: {panel_summary}",
        "",
        "Include:",
        _bullet_block(composition),
    ]

    if vocab:
        parts += ["", "Domain vocabulary to honor:", _bullet_block(vocab)]

    parts += [
        "",
        "Style:",
        "- minimal, elegant, balanced composition",
        "- consistent colors",
        "- no unnecessary text",
        "- white background",
    ]
    if style_extra and not _is_skip(style_extra):
        parts += [_bullet_block(style_extra)]

    parts += [
        "",
        "Do NOT include:",
        "- numerical values",
        "- experimental conditions",
        "- dimensional annotations",
        "- specific quantitative labels",
        "- count tokens (e.g., '4 dots', '두 개')",
    ]
    if forbidden and not _is_skip(forbidden):
        cleaned = _filter_allowed_hints(forbidden)
        if cleaned.strip():
            parts += [_bullet_block(cleaned)]

    parts += [
        "",
        f"(Generated by figure-agent for figure: {name})",
    ]
    return "\n".join(parts)


def generate_for(example_dir: Path) -> tuple[str, list]:
    """Read spec.yaml + briefing.md from `example_dir`, compose + redact prompt."""
    spec_path = example_dir / "spec.yaml"
    briefing_path = example_dir / "briefing.md"
    if not spec_path.exists():
        raise FileNotFoundError(f"missing {spec_path}")
    if not briefing_path.exists():
        raise FileNotFoundError(f"missing {briefing_path}")
    spec = parse_spec(spec_path.read_text())
    briefing = parse_briefing(briefing_path.read_text())
    prompt = compose_prompt(spec, briefing)
    redacted, audit = redact(prompt)
    return redacted, audit


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: prompt_gen.py <example_dir>", file=sys.stderr)
        return 2
    example_dir = Path(sys.argv[1])
    if not example_dir.is_dir():
        print(f"not a directory: {example_dir}", file=sys.stderr)
        return 2
    prompt, audit = generate_for(example_dir)
    print("=== REDACTED PROMPT (copy below for external tool) ===")
    print(prompt)
    print("=== END PROMPT ===")
    print("\n=== Redaction audit ===", file=sys.stderr)
    print(format_audit(audit), file=sys.stderr)
    print(
        "\n⚠️  Review the prompt for any remaining sensitive content before "
        "sending to an external service.",
        file=sys.stderr,
    )
    print(
        "\nNext steps:\n"
        "  1. Copy prompt above into your image-gen tool of choice.\n"
        "  2. Generate 3-5 candidates.\n"
        f"  3. Save into {example_dir}/previews/ (any filename).\n"
        "  4. Run /fig_preview_select to continue.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
