from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_export  # noqa: E402


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
