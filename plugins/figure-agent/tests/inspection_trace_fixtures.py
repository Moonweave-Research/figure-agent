"""Synthetic host receipts for contract tests; never evidence of human review."""

import json

import yaml
from post_repair_visual_review import EXECUTION_RECEIPT_SCHEMA, _canonical_hash
from quality_manifest import file_sha256


def issue_inspection_trace(fixture):
    manifest_path = fixture / "build/audit_crops/manifest.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text())
    render = fixture / manifest["render_path"]
    if not render.is_file():
        render.write_bytes(b"synthetic test render")
    manifest["render_sha256"] = file_sha256(render)
    manifest_path.write_text(json.dumps(manifest))
    crops = {item["id"]: item for item in manifest["crops"]}
    entries = [crops[key] for key in manifest["required_crop_ids"]]
    transcript = fixture / "synthetic-host-transcript.json"
    transcript.write_text(json.dumps({"synthetic_test_only": True, "artifacts": entries}))
    execution = {
        "schema": EXECUTION_RECEIPT_SCHEMA,
        "request_sha256": file_sha256(manifest_path),
        "actor": {"kind": "tool", "identity": "synthetic-test", "model_or_tool": "fixture"},
        "transcript": {"path": transcript.name, "sha256": file_sha256(transcript)},
        "inspected_artifacts": [
            {"path": manifest["render_path"], "sha256": manifest["render_sha256"]},
            *[{key: item[key] for key in ("path", "sha256")} for item in entries],
        ],
    }
    execution["receipt_sha256"] = _canonical_hash(execution, omitted="receipt_sha256")
    trace = {
        "schema": "figure-agent.inspection-trace.v1",
        "fixture": fixture.name,
        "source": "external_tool",
        "execution": execution,
        "inspected_artifacts": [
            {
                **{key: item[key] for key in ("id", "path", "sha256")},
                "verdict": "inspected",
                "note": "synthetic contract test",
            }
            for item in entries
        ],
    }
    (fixture / "inspection_trace.yaml").write_text(yaml.safe_dump(trace))
