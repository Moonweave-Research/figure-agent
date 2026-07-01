from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_export  # noqa: E402
import status as status_mod  # noqa: E402
from quality_manifest import CRITIQUE_RUBRIC_VERSION, file_sha256, input_manifest_hash  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_reference_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    fixture = repo / "examples" / "ref_fig"
    (fixture / "build").mkdir(parents=True)
    (fixture / "reference").mkdir()
    (fixture / "spec.yaml").write_text(
        "\n".join(
            [
                "name: ref_fig",
                "style_profile: polymer-default",
                "reference_image: reference/ref.png",
                "panels: []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("briefing", encoding="utf-8")
    (fixture / "ref_fig.tex").write_text("% tikz", encoding="utf-8")
    (fixture / "reference" / "ref.png").write_bytes(b"\x89PNG")
    (fixture / "build" / "ref_fig.pdf").write_bytes(b"%PDF")
    return repo


def _make_missing_reference_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    fixture = repo / "examples" / "broken_ref_fig"
    (fixture / "build").mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        "\n".join(
            [
                "name: broken_ref_fig",
                "style_profile: polymer-default",
                "reference_image: reference/missing.png",
                "panels: []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("briefing", encoding="utf-8")
    (fixture / "broken_ref_fig.tex").write_text("% tikz", encoding="utf-8")
    (fixture / "build" / "broken_ref_fig.pdf").write_bytes(b"%PDF")
    return repo


def _critique_input_hash(fixture: Path, name: str) -> str:
    spec = status_mod.parse_spec((fixture / "spec.yaml").read_text(encoding="utf-8"))
    return input_manifest_hash(
        status_mod._critique_source_paths(fixture, name, spec),
        base_dir=REPO_ROOT,
    )


def _write_hashed_critique(fixture: Path, name: str, critique_input_hash: str) -> None:
    (fixture / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1.2\n"
        f"fixture: {name}\n"
        "generated_at: 2026-05-17T00:00:00Z\n"
        "generator: critique_brief.py\n"
        f"generator_version: {file_sha256(REPO_ROOT / 'scripts' / 'critique_brief.py')}\n"
        f"rubric_version: {CRITIQUE_RUBRIC_VERSION}\n"
        f"critique_input_hash: {critique_input_hash}\n"
        "verdict: ready\n"
        "audit_enumeration:\n"
        "  structural_completeness:\n"
        "    components:\n"
        "      - component: demo\n"
        "        mount_support: yes\n"
        "        rationale: supported\n"
        "        connections: no connections\n"
        "    missing_from_reference:\n"
        "      - element: none\n"
        "        status: intentional_omission\n"
        "        rationale: not needed\n"
        "  label_target_matching:\n"
        "    - label: demo\n"
        "      nearest_object: demo\n"
        "      intended_target: demo\n"
        "      matches: true\n"
        '      proposed_fix: ""\n'
        "  physical_plausibility:\n"
        "    - check: floating_components\n"
        "      finding: no floating components\n"
        "      verdict: convention_acceptable\n"
        "  conceptual_completeness:\n"
        "    - element: none\n"
        "      reference: briefing\n"
        "      severity: NIT\n"
        "      proposed_action: accept_simplification\n"
        "quality_axes:\n"
        "  message_storyline:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: story is clear\n"
        "    evidence: briefing and render\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  panel_role_coherence:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: panel role is clear\n"
        "    evidence: panel A\n"
        "    panel_roles:\n"
        "      - panel_id: A\n"
        "        role: setup\n"
        "        role_quality: clear\n"
        "        rationale: panel introduces the setup\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  subregion_integration:\n"
        "    verdict: not_applicable\n"
        "    confidence: low\n"
        '    rationale: ""\n'
        '    evidence: ""\n'
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  component_fidelity:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: components are recognizable\n"
        "    evidence: structural audit\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  scientific_plausibility:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: no visible scientific conflict\n"
        "    evidence: briefing invariant\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  composition_layout:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: layout is readable\n"
        "    evidence: render\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  label_annotation_semantics:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: labels match targets\n"
        "    evidence: label audit\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  journal_polish:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: polish is adequate\n"
        "    evidence: render\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  reference_fidelity:\n"
        "    verdict: not_applicable\n"
        "    confidence: low\n"
        '    rationale: ""\n'
        '    evidence: ""\n'
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "  publication_readiness:\n"
        "    verdict: pass\n"
        "    confidence: high\n"
        "    rationale: all applicable quality axes pass\n"
        "    evidence: quality axis summary\n"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
        "panels: []\n"
        "findings: []\n"
        "---\n"
        "# Vision Critique\n",
        encoding="utf-8",
    )


def test_run_export_blocks_reference_fixture_without_critique(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = _make_reference_fixture(tmp_path)
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert "critique_missing" in captured.err
    assert "/fig_critique ref_fig" in captured.err
    assert "--skip-critique" in captured.err


def test_run_export_blocks_on_violated_semantic_assertion(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # New contract: the gate re-runs the check against the current render, so a
    # cached JSON is irrelevant — the violation must come from the declared spec
    # assertion evaluated against the PDF's word geometry.
    repo = _make_reference_fixture(tmp_path)
    fixture = repo / "examples" / "ref_fig"
    (fixture / "spec.yaml").write_text(
        "\n".join(
            [
                "name: ref_fig",
                "style_profile: polymer-default",
                "reference_image: reference/ref.png",
                "panels: []",
                "semantic_assertions:",
                "  - id: shallow-above-deep",
                "    relation: above",
                "    subject: shallow",
                "    reference: deep",
                "",
            ]
        ),
        encoding="utf-8",
    )
    # shallow rendered BELOW deep (larger y-center) violates relation: above.
    shallow = {"text": "shallow", "xmin": 0.0, "xmax": 10.0, "ymin": 95.0, "ymax": 105.0}
    deep = {"text": "deep", "xmin": 0.0, "xmax": 10.0, "ymin": 5.0, "ymax": 15.0}
    monkeypatch.setattr(
        run_export, "extract_pdf_words_and_page", lambda _pdf: ([shallow, deep], (600.0, 400.0))
    )
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _e, _n: run_export.EXPORT_FRESH)
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert "semantic_assertion" in captured.err.lower()
    assert "shallow-above-deep" in captured.err


def _write_tex_assertion_fixture(
    repo: Path, *, tex_body: str, assertion_block: str, cache_json: str | None = None
) -> None:
    """Overlay a tex_assertions spec + source (and optional stale cache) on ref_fig."""
    fixture = repo / "examples" / "ref_fig"
    (fixture / "spec.yaml").write_text(
        "\n".join(
            [
                "name: ref_fig",
                "style_profile: polymer-default",
                "reference_image: reference/ref.png",
                "panels: []",
                assertion_block,
                "",
            ]
        ),
        encoding="utf-8",
    )
    (fixture / "ref_fig.tex").write_text(tex_body, encoding="utf-8")
    if cache_json is not None:
        (fixture / "build" / "tex_assertions.json").write_text(cache_json, encoding="utf-8")


_VIOLATING_TEX = "\\draw[forceArr] (0,0) -- (2,0);\n"  # +x, violates direction: decreasing
_SATISFYING_TEX = "\\draw[forceArr] (0,0) -- (-2,0);\n"  # -x, satisfies decreasing
_TEX_ASSERTION_BLOCK = "\n".join(
    [
        "tex_assertions:",
        "  - id: force-repels",
        "    anchor_style: forceArr",
        "    axis: x",
        "    direction: decreasing",
    ]
)


def test_run_export_blocks_violating_tex_source_without_cache(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # Fresh checkout / git-clean: build/tex_assertions.json is absent. The gate must
    # re-run the checker against the source and still block, not fail open.
    repo = _make_reference_fixture(tmp_path)
    _write_tex_assertion_fixture(
        repo, tex_body=_VIOLATING_TEX, assertion_block=_TEX_ASSERTION_BLOCK
    )
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _e, _n: run_export.EXPORT_FRESH)
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert "tex_assertion" in captured.err.lower()
    assert "force-repels" in captured.err


def test_run_export_ignores_stale_clean_tex_assertion_cache(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # A stale cache claims the figure is clean, but the current source violates.
    # The gate must trust the source, not the cache.
    repo = _make_reference_fixture(tmp_path)
    _write_tex_assertion_fixture(
        repo,
        tex_body=_VIOLATING_TEX,
        assertion_block=_TEX_ASSERTION_BLOCK,
        cache_json=json.dumps({"issues": []}),
    )
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _e, _n: run_export.EXPORT_FRESH)
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert "force-repels" in captured.err


def test_run_export_blocks_malformed_tex_assertions_spec(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # Malformed declared assertion must fail closed, not silently pass.
    repo = _make_reference_fixture(tmp_path)
    _write_tex_assertion_fixture(
        repo,
        tex_body=_VIOLATING_TEX,
        assertion_block="\n".join(
            [
                "tex_assertions:",
                "  - id: force-repels",
                "    anchor_style: forceArr",
                "    direction: decreasing",
            ]
        ),
    )
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _e, _n: run_export.EXPORT_FRESH)
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert "tex_assertion" in captured.err.lower()


def test_run_export_allows_satisfied_tex_source_without_cache(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # Guard against over-blocking: a satisfied assertion with no cache must not block.
    repo = _make_reference_fixture(tmp_path)
    _write_tex_assertion_fixture(
        repo, tex_body=_SATISFYING_TEX, assertion_block=_TEX_ASSERTION_BLOCK
    )
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _e, _n: run_export.EXPORT_FRESH)
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig", "--skip-critique"])

    rc = run_export.main()

    assert rc == 0


def test_run_export_rejects_unsafe_fixture_name_before_regenerate(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    (repo / "examples").mkdir(parents=True)
    outside = repo / "outside"
    (outside / "build").mkdir(parents=True)
    (outside / "spec.yaml").write_text("name: outside\npanels: []\n", encoding="utf-8")
    (outside / "outside.tex").write_text("% tikz\n", encoding="utf-8")
    (outside / "build" / "outside.pdf").write_bytes(b"%PDF")
    regenerated: list[tuple[Path, str]] = []
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _example, _name: "MISSING")
    monkeypatch.setattr(
        run_export,
        "_regenerate",
        lambda example, name, plugin_root=None: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "../outside", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert regenerated == []
    assert "fixture name must be a single examples/<name> directory name" in captured.err


def test_run_export_blocks_declared_missing_reference_before_regenerate(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = _make_missing_reference_fixture(tmp_path)
    regenerated: list[tuple[Path, str]] = []
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _example, _name: "MISSING")
    monkeypatch.setattr(
        run_export,
        "_regenerate",
        lambda example, name, plugin_root=None: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "broken_ref_fig"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert regenerated == []
    assert "reference_image_missing" in captured.err
    assert "reference/missing.png" in captured.err


def test_run_export_skip_critique_still_blocks_declared_missing_reference(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = _make_missing_reference_fixture(tmp_path)
    regenerated: list[tuple[Path, str]] = []
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _example, _name: "MISSING")
    monkeypatch.setattr(
        run_export,
        "_regenerate",
        lambda example, name, plugin_root=None: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "broken_ref_fig", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert regenerated == []
    assert "reference_image_missing" in captured.err
    assert "reference/missing.png" in captured.err


def test_run_export_skip_critique_allows_regenerate(tmp_path: Path, monkeypatch, capsys) -> None:
    repo = _make_reference_fixture(tmp_path)
    regenerated: list[tuple[Path, str]] = []
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _example, _name: "MISSING")
    monkeypatch.setattr(
        run_export,
        "_regenerate",
        lambda example, name, plugin_root=None: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 0
    assert regenerated == [(repo / "examples" / "ref_fig", "ref_fig")]
    assert "regenerated exports/ for ref_fig" in captured.out


def test_run_export_regenerate_uses_explicit_plugin_root(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "ref_fig"
    (fixture / "build").mkdir(parents=True)
    (fixture / "build" / "ref_fig.pdf").write_bytes(b"%PDF")
    plugin_root = tmp_path / "installed-plugin"
    plugin_root.mkdir()
    calls: list[tuple[list[str], Path, bool]] = []

    def fake_run(cmd: list[str], *, cwd: Path, check: bool) -> None:
        calls.append((cmd, cwd, check))

    monkeypatch.setattr(run_export.subprocess, "run", fake_run)

    run_export._regenerate(fixture, "ref_fig", plugin_root=plugin_root)

    assert [cwd for _cmd, cwd, _check in calls] == [plugin_root, plugin_root, plugin_root]
    assert all(check for _cmd, _cwd, check in calls)
    assert calls[0][0][:2] == ["bash", "scripts/export_svg.sh"]
    assert calls[2][0][:2] == ["bash", "scripts/svg_to_png.sh"]
    assert (fixture / "exports" / "ref_fig.pdf").read_bytes() == b"%PDF"


def test_run_export_blocks_hash_stale_critique(tmp_path: Path, monkeypatch, capsys) -> None:
    repo = _make_reference_fixture(tmp_path)
    fixture = repo / "examples" / "ref_fig"
    old_hash = _critique_input_hash(fixture, "ref_fig")
    _write_hashed_critique(fixture, "ref_fig", old_hash)
    (fixture / "briefing.md").write_text("changed briefing", encoding="utf-8")
    regenerated: list[tuple[Path, str]] = []
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _example, _name: "MISSING")
    monkeypatch.setattr(
        run_export,
        "_regenerate",
        lambda example, name, plugin_root=None: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert regenerated == []
    assert "critique_stale" in captured.err
    assert "--skip-critique" in captured.err


def test_run_export_blocks_hash_fresh_but_invalid_critique(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = _make_reference_fixture(tmp_path)
    fixture = repo / "examples" / "ref_fig"
    critique_hash = _critique_input_hash(fixture, "ref_fig")
    (fixture / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1.7\n"
        "fixture: ref_fig\n"
        "generated_at: 2026-05-17T00:00:00Z\n"
        "generator: critique_brief.py\n"
        f"generator_version: {file_sha256(REPO_ROOT / 'scripts' / 'critique_brief.py')}\n"
        f"rubric_version: {CRITIQUE_RUBRIC_VERSION}\n"
        f"critique_input_hash: {critique_hash}\n"
        "verdict: ready\n"
        "---\n"
        "# malformed critique\n",
        encoding="utf-8",
    )
    regenerated: list[tuple[Path, str]] = []
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _example, _name: "MISSING")
    monkeypatch.setattr(
        run_export,
        "_regenerate",
        lambda example, name, plugin_root=None: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert regenerated == []
    assert "critique_invalid" in captured.err
    assert "critique_contract" in captured.err


def test_run_export_skip_critique_allows_hash_stale_regenerate(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = _make_reference_fixture(tmp_path)
    fixture = repo / "examples" / "ref_fig"
    old_hash = _critique_input_hash(fixture, "ref_fig")
    _write_hashed_critique(fixture, "ref_fig", old_hash)
    (fixture / "briefing.md").write_text("changed briefing", encoding="utf-8")
    regenerated: list[tuple[Path, str]] = []
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _example, _name: "MISSING")
    monkeypatch.setattr(
        run_export,
        "_regenerate",
        lambda example, name, plugin_root=None: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 0
    assert regenerated == [(fixture, "ref_fig")]
    assert "regenerated exports/ for ref_fig" in captured.out
