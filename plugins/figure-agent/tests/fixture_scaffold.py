"""Shared scaffold for the `<workspace>/examples/<name>/` fixture shape.

Roughly thirty test modules each grew their own `_fixture` writing the same
three files. Anything beyond spec/briefing/tex stays in the caller: this covers
the common shape only, it is not a place to accumulate per-test setup.
"""

from __future__ import annotations

from pathlib import Path


def make_example_fixture(
    workspace: Path,
    name: str,
    *,
    spec: str | None = None,
    briefing: str | None = None,
    tex: str | None = None,
) -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    if spec is not None:
        (fixture / "spec.yaml").write_text(spec, encoding="utf-8")
    if briefing is not None:
        (fixture / "briefing.md").write_text(briefing, encoding="utf-8")
    if tex is not None:
        (fixture / f"{name}.tex").write_text(tex, encoding="utf-8")
    return fixture
