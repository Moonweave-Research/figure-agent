"""Package editable source separately from outlined display exports."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from quality_manifest import file_sha256
from render_input_manifest import manifest_path
from style_contract import resolve_style


def write_bundle(example_dir: Path, name: str, source: Path, render: Path, styles: Path) -> Path:
    inputs_path = manifest_path(render)
    inputs = json.loads(inputs_path.read_text())
    files = {f"source/{source.name}": source}
    for relative in inputs.get("dependencies", {}):
        path = (source.parent / relative).resolve()
        if not path.is_relative_to(source.parent.resolve()) or not path.is_file():
            raise ValueError(f"invalid editable dependency: {relative}")
        files[f"source/{relative}"] = path
    style, _ = resolve_style(example_dir, styles / "polymer-paper-preamble.sty")
    files[f"source/{style.name}"] = style
    for filename in ("spec.yaml", "briefing.md", "claim_authority.yaml"):
        path = example_dir / filename
        if path.is_file():
            files[f"source/{filename}"] = path
    files["evidence/render_inputs.json"] = inputs_path
    receipt = render.parent / "compile_run.json"
    if receipt.is_file():
        files["evidence/compile_run.json"] = receipt
    exported_pdf = example_dir / "exports" / f"{name}.pdf"
    manifest = {
        "schema": "figure-agent.submission-bundle.v1",
        "fixture": example_dir.name,
        "submission_pdf": {"path": exported_pdf.name, "sha256": file_sha256(exported_pdf)},
        "editable_authority": f"source/{source.name}",
        "display_derivative": {"path": f"{name}.svg", "text_editability": "outlined"},
        "sources": {key: file_sha256(path) for key, path in sorted(files.items())},
        "font_policy": "PDF preserves embedded fonts; source rebuild needs recorded system fonts.",
        "publication_approval": "not_implied_by_export",
    }
    output = example_dir / "exports" / f"{name}_editable_source.zip"
    temporary = output.with_suffix(".zip.tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for relative, path in sorted(files.items()):
                archive.write(path, relative)
            archive.writestr("delivery_manifest.json", json.dumps(manifest, indent=2) + "\n")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output
