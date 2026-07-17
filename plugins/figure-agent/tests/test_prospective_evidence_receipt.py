from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import prospective_evidence_receipt as receipt  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> Path:
    fixture = tmp_path / "fixture"
    files = {
        "fixture.tex": "\\documentclass{standalone}\n",
        "build/strict.json": json.dumps(
            {
                "schema": "figure-agent.strict-status.v1",
                "strict_requested": True,
                "detector_failed": False,
                "state": "passed",
            }
        )
        + "\n",
        "build/figure.png": "render\n",
        "review/crops/manifest.json": '{"crops": ["panel-a.png"]}\n',
        "review/crops/panel-a.png": "crop\n",
        "review/critique.json": '{"findings": []}\n',
        "review/adjudication.yaml": "decision: review_ready\n",
        "build/figure.pdf": "pdf\n",
    }
    for relative, content in files.items():
        path = fixture / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    declaration = {
        "fixture": "fixture",
        "compile": {
            "command": "FIGURE_AGENT_STRICT=1 bash scripts/compile.sh examples/fixture/fixture.tex",
            "strict": True,
            "returncode": 0,
        },
        "artifacts": [
            {"role": "source", "path": "fixture.tex"},
            {"role": "strict_compile_report", "path": "build/strict.json"},
            {"role": "render", "path": "build/figure.png"},
            {"role": "audit_crop_manifest", "path": "review/crops/manifest.json"},
            {"role": "audit_crop", "path": "review/crops/panel-a.png"},
            {"role": "critique", "path": "review/critique.json"},
            {"role": "adjudication", "path": "review/adjudication.yaml"},
            {"role": "export", "path": "build/figure.pdf"},
        ],
        "correction": {"state": "not_captured", "minutes": None},
        "publication_acceptance": "not_claimed",
    }
    (fixture / "declaration.yaml").write_text(yaml.safe_dump(declaration), encoding="utf-8")
    return fixture


def test_records_hash_bound_immutable_prospective_evidence(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)

    result = receipt.record(
        fixture_dir=fixture,
        declaration="declaration.yaml",
        output_dir="review/prospective/q4-001",
    )

    output = fixture / "review/prospective/q4-001"
    payload = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert result == payload
    assert payload["schema"] == "figure-agent.prospective-evidence-receipt.v1"
    assert payload["publication_acceptance"] == "not_claimed"
    assert payload["correction"] == {"state": "not_captured", "minutes": None}
    assert payload["source_declaration"]["path"] == "declaration.yaml"
    assert payload["source_declaration"]["sha256"] == _sha256(fixture / "declaration.yaml")
    assert {item["role"] for item in payload["artifacts"]} == {
        "source",
        "strict_compile_report",
        "render",
        "audit_crop_manifest",
        "audit_crop",
        "critique",
        "adjudication",
        "export",
    }
    for item in payload["artifacts"]:
        snapshot = output / item["snapshot_path"]
        assert snapshot.is_file()
        assert item["sha256"] == _sha256(snapshot)


@pytest.mark.parametrize(
    ("declaration", "output"),
    [
        ("/tmp/declaration.yaml", "review/out"),
        ("../declaration.yaml", "review/out"),
        ("declaration.yaml", "/tmp/out"),
        ("declaration.yaml", "../out"),
    ],
)
def test_rejects_non_fixture_relative_paths(tmp_path: Path, declaration: str, output: str) -> None:
    fixture = _fixture(tmp_path)

    with pytest.raises(receipt.ProspectiveEvidenceReceiptError, match="path_invalid"):
        receipt.record(fixture_dir=fixture, declaration=declaration, output_dir=output)


def test_rejects_symlink_input_and_output_ancestor(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (fixture / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(receipt.ProspectiveEvidenceReceiptError, match="output_symlink"):
        receipt.record(
            fixture_dir=fixture,
            declaration="declaration.yaml",
            output_dir="linked/out",
        )

    target = fixture / "build/figure.png"
    target.rename(fixture / "build/actual.png")
    target.symlink_to(fixture / "build/actual.png")
    with pytest.raises(receipt.ProspectiveEvidenceReceiptError, match="artifact_symlink"):
        receipt.record(
            fixture_dir=fixture,
            declaration="declaration.yaml",
            output_dir="review/new-out",
        )


def test_rejects_duplicate_path_or_role_and_existing_output(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    declaration = yaml.safe_load((fixture / "declaration.yaml").read_text())
    declaration["artifacts"].append({"role": "human_verdict", "path": "build/figure.pdf"})
    (fixture / "duplicate.yaml").write_text(yaml.safe_dump(declaration))
    with pytest.raises(receipt.ProspectiveEvidenceReceiptError, match="path_duplicate"):
        receipt.record(
            fixture_dir=fixture,
            declaration="duplicate.yaml",
            output_dir="review/new-out",
        )

    declaration["artifacts"][-1]["path"] = "review/verdict.json"
    (fixture / "review/verdict.json").write_text("{}\n")
    declaration["artifacts"].append({"role": "human_verdict", "path": "review/verdict-2.json"})
    (fixture / "review/verdict-2.json").write_text("{}\n")
    (fixture / "duplicate.yaml").write_text(yaml.safe_dump(declaration))
    with pytest.raises(receipt.ProspectiveEvidenceReceiptError, match="role_cardinality"):
        receipt.record(
            fixture_dir=fixture,
            declaration="duplicate.yaml",
            output_dir="review/new-out",
        )

    (fixture / "review/new-out").mkdir()
    with pytest.raises(receipt.ProspectiveEvidenceReceiptError, match="output_exists"):
        receipt.record(
            fixture_dir=fixture,
            declaration="declaration.yaml",
            output_dir="review/new-out",
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: data["compile"].update(strict=False),
        lambda data: data["compile"].update(returncode=1),
        lambda data: data.update(publication_acceptance="accepted"),
        lambda data: data.update(correction={"state": "not_captured", "minutes": 3}),
        lambda data: data.update(correction={"state": "measured", "minutes": None}),
    ],
)
def test_rejects_invalid_strict_correction_or_acceptance_facts(
    tmp_path: Path, mutation: object
) -> None:
    fixture = _fixture(tmp_path)
    declaration = yaml.safe_load((fixture / "declaration.yaml").read_text())
    mutation(declaration)  # type: ignore[operator]
    (fixture / "invalid.yaml").write_text(yaml.safe_dump(declaration))

    with pytest.raises(receipt.ProspectiveEvidenceReceiptError):
        receipt.record(
            fixture_dir=fixture,
            declaration="invalid.yaml",
            output_dir="review/new-out",
        )


def test_editable_source_drift_cleans_staging_and_publishes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    original = receipt._read_regular
    reads = 0

    def drift(*args: object, **kwargs: object) -> tuple[Path, bytes]:
        nonlocal reads
        path, data = original(*args, **kwargs)  # type: ignore[arg-type]
        reads += 1
        if reads == 11:
            return path, data + b"drift"
        return path, data

    monkeypatch.setattr(receipt, "_read_regular", drift)
    with pytest.raises(receipt.ProspectiveEvidenceReceiptError, match="source_artifact_drift"):
        receipt.record(
            fixture_dir=fixture,
            declaration="declaration.yaml",
            output_dir="review/prospective/q4-001",
        )

    assert not (fixture / "review/prospective/q4-001").exists()
    assert not list((fixture / "review/prospective").glob(".*.staging-*"))


def test_accepts_json_measured_correction_and_optional_human_verdict(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    declaration = yaml.safe_load((fixture / "declaration.yaml").read_text())
    declaration["correction"] = {"state": "measured", "minutes": 12.5}
    declaration["artifacts"].append({"role": "human_verdict", "path": "review/human-verdict.json"})
    (fixture / "review/human-verdict.json").write_text('{"verdict": "accept"}\n')
    (fixture / "declaration.json").write_text(json.dumps(declaration))

    payload = receipt.record(
        fixture_dir=fixture,
        declaration="declaration.json",
        output_dir="review/prospective/q4-json",
    )

    assert payload["correction"] == {"state": "measured", "minutes": 12.5}
    assert sum(item["role"] == "human_verdict" for item in payload["artifacts"]) == 1


def test_rejects_strict_report_that_does_not_prove_strict_rc_zero(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    (fixture / "build/strict.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.strict-status.v1",
                "strict_requested": False,
                "detector_failed": False,
                "state": "passed",
            }
        )
        + "\n"
    )

    with pytest.raises(receipt.ProspectiveEvidenceReceiptError, match="strict_report_invalid"):
        receipt.record(
            fixture_dir=fixture,
            declaration="declaration.yaml",
            output_dir="review/prospective/q4-invalid",
        )


def test_rejects_missing_editable_source_role(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    declaration = yaml.safe_load((fixture / "declaration.yaml").read_text())
    declaration["artifacts"] = [
        item for item in declaration["artifacts"] if item["role"] != "source"
    ]
    (fixture / "missing-source.yaml").write_text(yaml.safe_dump(declaration))

    with pytest.raises(receipt.ProspectiveEvidenceReceiptError, match="role_cardinality"):
        receipt.record(
            fixture_dir=fixture,
            declaration="missing-source.yaml",
            output_dir="review/prospective/q4-invalid",
        )


def test_rejects_source_role_that_is_not_editable_tex(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    declaration = yaml.safe_load((fixture / "declaration.yaml").read_text())
    (fixture / "source.txt").write_text("not tex\n")
    next(item for item in declaration["artifacts"] if item["role"] == "source")["path"] = (
        "source.txt"
    )
    (fixture / "invalid-source.yaml").write_text(yaml.safe_dump(declaration))

    with pytest.raises(receipt.ProspectiveEvidenceReceiptError, match="source_invalid"):
        receipt.record(
            fixture_dir=fixture,
            declaration="invalid-source.yaml",
            output_dir="review/prospective/q4-invalid",
        )
