from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import human_attestation  # noqa: E402


def _fixture(workspace: Path) -> Path:
    fixture = workspace / "examples" / "demo_fig"
    fixture.mkdir(parents=True)
    (fixture / "demo_fig.tex").write_text("source\n", encoding="utf-8")
    return fixture


def _provision_key() -> None:
    human_attestation._load_or_create_key()


class _Stdin:
    def __init__(self, tty: bool) -> None:
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def _at_a_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", _Stdin(True))


def test_verify_attestation_rejects_forged_json_without_valid_hmac(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    fixture = _fixture(tmp_path / "workspace")
    source_hash = human_attestation.source_set_sha256(fixture)
    (fixture / "human_attestation.json").write_text(
        json.dumps(
            {
                "schema": human_attestation.SCHEMA,
                "fixture": "demo_fig",
                "source_set_sha256": source_hash,
                "created_at": "2026-07-02T00:00:00Z",
                "signature": "sha256:not-real",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    ok, reason = human_attestation.verify_attestation(fixture)

    assert ok is False
    assert reason == "bad_hmac"


def test_verify_attestation_rejects_stale_source_set_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")
    _provision_key()
    human_attestation.write_attestation(fixture)
    (fixture / "demo_fig.tex").write_text("changed\n", encoding="utf-8")

    ok, reason = human_attestation.verify_attestation(fixture)

    assert ok is False
    assert reason == "stale_source_set_sha256"


def test_verify_attestation_rejects_stale_briefing_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")
    (fixture / "briefing.md").write_text("briefing\n", encoding="utf-8")
    _provision_key()
    human_attestation.write_attestation(fixture)

    (fixture / "briefing.md").write_text("changed briefing\n", encoding="utf-8")

    ok, reason = human_attestation.verify_attestation(fixture)

    assert ok is False
    assert reason == "stale_source_set_sha256"


def test_verify_attestation_missing_key_does_not_create_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")
    _provision_key()
    human_attestation.write_attestation(fixture)
    (home / ".figure-agent" / "attest.key").unlink()
    (home / ".figure-agent").rmdir()
    home.rmdir()

    ok, reason = human_attestation.verify_attestation(fixture)

    assert ok is False
    assert reason == "missing_attestation_key"
    assert not home.exists()


def test_verify_attestation_missing_key_tolerates_read_only_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writable_home = tmp_path / "writable_home"
    monkeypatch.setenv("HOME", str(writable_home))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")
    _provision_key()
    human_attestation.write_attestation(fixture)

    readonly_home = tmp_path / "readonly_home"
    readonly_home.mkdir()
    readonly_home.chmod(0o500)
    monkeypatch.setenv("HOME", str(readonly_home))
    try:
        ok, reason = human_attestation.verify_attestation(fixture)
    finally:
        readonly_home.chmod(0o700)

    assert ok is False
    assert reason == "missing_attestation_key"
    assert not (readonly_home / ".figure-agent").exists()


def test_verify_attestation_rejects_non_ascii_signature_before_key_load(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    fixture = _fixture(tmp_path / "workspace")
    payload = {
        "schema": human_attestation.SCHEMA,
        "fixture": "demo_fig",
        "source_set_sha256": human_attestation.source_set_sha256(fixture),
        "created_at": "2026-07-02T00:00:00Z",
        "signature": "sha256:" + "é" * 64,
    }
    (fixture / "human_attestation.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    ok, reason = human_attestation.verify_attestation(fixture)

    assert ok is False
    assert reason == "bad_hmac"
    assert not home.exists()


def test_verify_attestation_accepts_valid_hmac_with_tmp_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")
    _provision_key()

    payload = human_attestation.write_attestation(fixture)
    ok, reason = human_attestation.verify_attestation(fixture)

    assert payload["schema"] == human_attestation.SCHEMA
    assert payload["fixture"] == "demo_fig"
    assert ok is True
    assert reason == "ok"
    key_path = tmp_path / "home" / ".figure-agent" / "attest.key"
    assert key_path.is_file()
    assert key_path.stat().st_mode & 0o777 == 0o600


def test_write_attestation_refuses_to_mint_a_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")

    with pytest.raises(ValueError, match="missing_attestation_key"):
        human_attestation.write_attestation(fixture)

    assert not (fixture / "human_attestation.json").exists()
    assert not home.exists()


def test_write_attestation_refuses_symlinked_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")
    _provision_key()
    real = tmp_path / "elsewhere.tex"
    real.write_text("other source\n", encoding="utf-8")
    (fixture / "demo_fig.tex").unlink()
    (fixture / "demo_fig.tex").symlink_to(real)

    with pytest.raises(ValueError, match="symlink"):
        human_attestation.write_attestation(fixture)

    assert not (fixture / "human_attestation.json").exists()


def test_verify_attestation_rejects_symlinked_source_member(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")
    _provision_key()
    human_attestation.write_attestation(fixture)
    content = (fixture / "demo_fig.tex").read_text(encoding="utf-8")
    real = tmp_path / "elsewhere.tex"
    real.write_text(content, encoding="utf-8")
    (fixture / "demo_fig.tex").unlink()
    (fixture / "demo_fig.tex").symlink_to(real)

    ok, reason = human_attestation.verify_attestation(fixture)

    assert ok is False
    assert reason == "source_set_unreadable"


def test_verify_attestation_rejects_symlinked_attestation_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")
    _provision_key()
    human_attestation.write_attestation(fixture)
    real = tmp_path / "moved_attestation.json"
    (fixture / "human_attestation.json").rename(real)
    (fixture / "human_attestation.json").symlink_to(real)

    ok, reason = human_attestation.verify_attestation(fixture)

    assert ok is False
    assert reason == "attestation_unreadable"


def test_create_cli_rejects_non_tty_stdin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("FIGURE_AGENT_WORKSPACE", str(tmp_path / "workspace"))
    _fixture(tmp_path / "workspace")

    monkeypatch.setattr(sys, "stdin", _Stdin(False))

    assert human_attestation.main(["create", "demo_fig"]) == 1
    output = tmp_path / "workspace" / "examples" / "demo_fig" / "human_attestation.json"
    assert not output.exists()


def test_write_attestation_refuses_a_non_tty_caller_holding_a_usable_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")
    _provision_key()
    monkeypatch.setattr(sys, "stdin", _Stdin(False))

    with pytest.raises(human_attestation.NonInteractiveAttestation):
        human_attestation.write_attestation(fixture)

    assert not (fixture / "human_attestation.json").exists()
    assert human_attestation.verify_attestation(fixture) == (
        False,
        "missing_human_attestation",
    )


def test_write_attestation_refuses_symlinked_output_and_leaves_the_victim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _at_a_terminal(monkeypatch)
    fixture = _fixture(tmp_path / "workspace")
    _provision_key()
    victim = tmp_path / "victim.txt"
    victim.write_text("do not overwrite me\n", encoding="utf-8")
    (fixture / "human_attestation.json").symlink_to(victim)

    with pytest.raises(ValueError, match="symlink"):
        human_attestation.write_attestation(fixture)

    assert victim.read_text(encoding="utf-8") == "do not overwrite me\n"
