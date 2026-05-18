from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_export  # noqa: E402
import status as status_mod  # noqa: E402
from quality_manifest import file_sha256, input_manifest_hash  # noqa: E402

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
        "schema: figure-agent.critique.v1\n"
        f"fixture: {name}\n"
        "generated_at: 2026-05-17T00:00:00Z\n"
        "generator: critique_brief.py\n"
        f"generator_version: {file_sha256(REPO_ROOT / 'scripts' / 'critique_brief.py')}\n"
        "rubric_version: figure-agent.critique-rubric.v1\n"
        f"critique_input_hash: {critique_input_hash}\n"
        "verdict: ready\n"
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
        lambda example, name: regenerated.append((example, name)),
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
        lambda example, name: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "broken_ref_fig", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert regenerated == []
    assert "reference_image_missing" in captured.err
    assert "reference/missing.png" in captured.err


def test_run_export_skip_critique_allows_regenerate(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = _make_reference_fixture(tmp_path)
    regenerated: list[tuple[Path, str]] = []
    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    monkeypatch.setattr(run_export, "compute_export_state", lambda _example, _name: "MISSING")
    monkeypatch.setattr(
        run_export,
        "_regenerate",
        lambda example, name: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 0
    assert regenerated == [(repo / "examples" / "ref_fig", "ref_fig")]
    assert "regenerated exports/ for ref_fig" in captured.out


def test_run_export_blocks_hash_stale_critique(
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
        lambda example, name: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 1
    assert regenerated == []
    assert "critique_stale" in captured.err
    assert "--skip-critique" in captured.err


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
        lambda example, name: regenerated.append((example, name)),
    )
    monkeypatch.setattr(sys, "argv", ["run_export.py", "ref_fig", "--skip-critique"])

    rc = run_export.main()

    captured = capsys.readouterr()
    assert rc == 0
    assert regenerated == [(fixture, "ref_fig")]
    assert "regenerated exports/ for ref_fig" in captured.out
