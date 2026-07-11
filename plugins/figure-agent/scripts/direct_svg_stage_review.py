"""Stage opaque, image-only human review packets for two completed runs."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import secrets
import shutil
from pathlib import Path
from typing import Any

import yaml
from direct_svg_packet import validate_packet
from direct_svg_review import (
    CONTAIN_GEOMETRY_POLICY,
    EXACT_GEOMETRY_POLICY,
    DirectSvgReviewError,
    build_review_packet,
)

RUN_STATE_SCHEMA = "figure-agent.direct-svg-run-state.v1"
PUBLIC_SCHEMA = "figure-agent.opaque-human-review.v1"
PRIVATE_SCHEMA = "figure-agent.private-review-key.v1"
REVIEW_STATE_SCHEMA = "figure-agent.direct-svg-review-state.v1"
PANELS = ("C", "F")


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _load_yaml(path: Path, *, error: str) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise DirectSvgReviewError(error) from exc
    if not isinstance(loaded, dict):
        raise DirectSvgReviewError(error)
    return loaded


def _resolve_declared_path(
    value: Any,
    *,
    run_dir: Path,
    fixture_root: Path,
    plugin_root: Path,
) -> Path:
    if not isinstance(value, str) or not value:
        raise DirectSvgReviewError("review_prerequisite_path_invalid")
    relative = Path(value)
    if relative.is_absolute():
        raise DirectSvgReviewError("review_prerequisite_path_invalid")
    candidates = (run_dir / relative, fixture_root / relative, plugin_root / relative)
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_relative_to(plugin_root) and resolved.is_file():
            return resolved
    raise DirectSvgReviewError("review_prerequisite_missing")


def _require_hash(path: Path, expected: Any, *, error: str) -> None:
    if expected != _sha256(path):
        raise DirectSvgReviewError(error)


def _validated_run(
    fixture_root: Path,
    run_name: str,
    packet_name: str,
    *,
    plugin_root: Path,
) -> dict[str, Path]:
    run_dir = fixture_root / "runs" / run_name
    state = _load_yaml(run_dir / "run-state.yaml", error="run_state_invalid")
    if state.get("schema") != RUN_STATE_SCHEMA or state.get("state") != "machine_review_ready":
        raise DirectSvgReviewError("run_not_machine_review_ready")
    if state.get("publication_acceptance") != "not_claimed":
        raise DirectSvgReviewError("publication_claim_forbidden")

    packet_path = fixture_root / "packets" / packet_name
    validate_packet(packet_path)
    packet_field = state.get("validated_packet") or state.get("synthesis_packet")
    if isinstance(packet_field, dict):
        declared_packet_path = packet_field.get("path")
        declared_packet_hash = packet_field.get("sha256")
    else:
        declared_packet_path = packet_field
        declared_packet_hash = state.get("validated_packet_sha256")
    resolved_packet = _resolve_declared_path(
        declared_packet_path,
        run_dir=run_dir,
        fixture_root=fixture_root,
        plugin_root=plugin_root,
    )
    if resolved_packet != packet_path.resolve():
        raise DirectSvgReviewError("validated_packet_path_mismatch")
    _require_hash(packet_path, declared_packet_hash, error="validated_packet_hash_mismatch")

    artifacts = state.get("candidate_artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 2:
        raise DirectSvgReviewError("candidate_artifacts_invalid")
    panel_paths: dict[str, Path] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict) or artifact.get("panel") not in PANELS:
            raise DirectSvgReviewError("candidate_artifacts_invalid")
        panel = artifact["panel"]
        render_value = artifact.get("render_path") or artifact.get("png_path")
        render_path = _resolve_declared_path(
            render_value,
            run_dir=run_dir,
            fixture_root=fixture_root,
            plugin_root=plugin_root,
        )
        _require_hash(
            render_path,
            artifact.get("render_sha256"),
            error="candidate_render_hash_mismatch",
        )
        panel_paths[panel] = render_path
    if set(panel_paths) != set(PANELS):
        raise DirectSvgReviewError("candidate_artifacts_invalid")
    return panel_paths


def _experiment_order(private_seed: bytes) -> list[str]:
    digest = hashlib.sha256(private_seed + b"experiment-order").digest()
    return ["test-a", "test-b"] if digest[0] % 2 == 0 else ["test-b", "test-a"]


def _option_seed(private_seed: bytes, experiment: str, panel: str) -> str:
    return hashlib.sha256(
        private_seed + b"option-order" + experiment.encode() + panel.encode()
    ).hexdigest()


def _semantic_review_context(fixture_root: Path) -> dict[str, Any]:
    packet = _load_yaml(
        fixture_root / "contract" / "semantic-packet.yaml",
        error="semantic_packet_invalid",
    )
    return {
        "scientific_objects": packet.get("scientific_objects"),
        "object_relations": packet.get("object_relations"),
        "text_content": packet.get("text_content"),
    }


def _response_template() -> dict[str, Any]:
    return {
        "option_A_scientific_fidelity": "pass/fail",
        "option_A_scientific_evidence": "",
        "option_B_scientific_fidelity": "pass/fail",
        "option_B_scientific_evidence": "",
        "composition_preference": "A/equivalent/B",
        "illustration_quality_preference": "A/equivalent/B",
        "typography_preference": "A/equivalent/B",
        "borderline_or_disputed": False,
        "named_reviewer": "",
        "reviewed_at": "",
    }


def _render_html(public_manifest: dict[str, Any]) -> str:
    context = public_manifest["semantic_review_context"]
    sections: list[str] = []
    for experiment in ("R1", "R2"):
        for panel in PANELS:
            base = f"{experiment}/{panel}"
            template = yaml.safe_dump(_response_template(), sort_keys=False)
            panel_key = f"panel_{panel.lower()}"
            objects = yaml.safe_dump(
                context["scientific_objects"][panel_key], sort_keys=False
            )
            texts = yaml.safe_dump(context["text_content"][panel_key], sort_keys=False)
            relations = [
                item
                for item in context["object_relations"]
                if str(item.get("subject", "")).lower().startswith(panel.lower())
            ]
            sections.append(
                f"""
<section>
  <h2>{experiment} / Panel {panel}</h2>
  <div class="pair">
    <figure>
      <img src="{base}/option-a.png" alt="{experiment} Panel {panel} Option A">
      <figcaption>Option A</figcaption>
    </figure>
    <figure>
      <img src="{base}/option-b.png" alt="{experiment} Panel {panel} Option B">
      <figcaption>Option B</figcaption>
    </figure>
  </div>
  <details><summary>Semantic objects, text, and relations</summary>
    <h3>Objects</h3><pre>{html.escape(objects)}</pre>
    <h3>Text</h3><pre>{html.escape(texts)}</pre>
    <h3>Relations</h3><pre>{html.escape(yaml.safe_dump(relations, sort_keys=False))}</pre>
  </details>
  <h3>Response template</h3>
  <ul>
    <li>Option A scientific fidelity (pass/fail) + evidence</li>
    <li>Option B scientific fidelity (pass/fail) + evidence</li>
    <li>Composition preference (A/equivalent/B)</li>
    <li>Illustration quality preference (A/equivalent/B)</li>
    <li>Typography preference (A/equivalent/B)</li>
    <li>Borderline/disputed flag</li>
    <li>Named reviewer and reviewed_at</li>
  </ul>
  <pre>{html.escape(template)}</pre>
</section>"""
            )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Opaque Human Review</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1400px;margin:2rem auto;
padding:0 1rem;color:#17202a}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
figure{{margin:0}}
img{{width:100%;height:auto;border:1px solid #ccd1d1;background:white}}
figcaption{{font-weight:700;text-align:center;margin:.4rem}}
section{{margin:3rem 0;border-top:2px solid #566573;padding-top:1rem}}
pre{{white-space:pre-wrap;background:#f4f6f7;padding:1rem}}
.notice{{background:#fff8e1;padding:1rem}}
</style></head><body>
<h1>Opaque Human Review</h1>
<p class="notice">Diagnostics are diagnostic only and excluded from score inputs.
Editability and cost are outside this image review and must be recorded separately.</p>
{''.join(sections)}
</body></html>
"""


def stage_review(
    fixture_root: Path,
    *,
    review_root: Path | None = None,
    review_state_path: Path | None = None,
    private_seed: bytes | None = None,
) -> dict[str, Any]:
    """Validate completed runs and stage public/private review artifacts."""
    fixture_root = fixture_root.resolve()
    plugin_root = fixture_root.parents[1]
    review_root = (review_root or fixture_root / "review").resolve()
    review_state_path = (review_state_path or review_root / "review-state.yaml").resolve()
    private_seed = private_seed if private_seed is not None else secrets.token_bytes(32)
    if not isinstance(private_seed, bytes) or len(private_seed) < 32:
        raise DirectSvgReviewError("private_seed_invalid")

    run_images = {
        "test-a": _validated_run(
            fixture_root,
            "test-a",
            "test-a-reconstruction.yaml",
            plugin_root=plugin_root,
        ),
        "test-b": _validated_run(
            fixture_root,
            "test-b",
            "test-b-synthesis.yaml",
            plugin_root=plugin_root,
        ),
    }
    authority_images = {
        panel: fixture_root / "reference" / "crops" / f"panel-{panel.lower()}.png"
        for panel in PANELS
    }

    public_root = review_root / "public"
    private_root = review_root / "private"
    for root in (public_root, private_root):
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True)

    experiment_names = _experiment_order(private_seed)
    experiment_map = dict(zip(("R1", "R2"), experiment_names, strict=True))
    public_experiments: dict[str, Any] = {}
    private_keys: dict[str, Any] = {}
    for public_label in ("R1", "R2"):
        internal_name = experiment_map[public_label]
        public_experiments[public_label] = {}
        private_keys[public_label] = {"run": internal_name, "panels": {}}
        geometry_policy = (
            EXACT_GEOMETRY_POLICY
            if internal_name == "test-a"
            else CONTAIN_GEOMETRY_POLICY
        )
        for panel in PANELS:
            public_dir = public_root / public_label / panel
            private_path = private_root / public_label / panel / "blinding-key.yaml"
            packet = build_review_packet(
                authority_images[panel],
                run_images[internal_name][panel],
                public_dir,
                seed=_option_seed(private_seed, internal_name, panel),
                private_manifest_path=private_path,
                candidate_normalization_policy=geometry_policy,
            )
            public_experiments[public_label][panel] = {
                "manifest": f"{public_label}/{panel}/public-review-manifest.yaml",
                "manifest_sha256": _sha256(packet["public_manifest_path"]),
                "review_input_hash": packet["public_manifest"]["review_input_hash"],
                "response_template": _response_template(),
            }
            private_keys[public_label]["panels"][panel] = {
                "key_manifest": str(private_path.relative_to(private_root)),
                "key_manifest_sha256": _sha256(private_path),
            }

    public_manifest = {
        "schema": PUBLIC_SCHEMA,
        "experiments": public_experiments,
        "semantic_review_context": _semantic_review_context(fixture_root),
        "normalization": {
            "policy_set": [EXACT_GEOMETRY_POLICY, CONTAIN_GEOMETRY_POLICY],
            "application": "opaque",
            "resampling": "LANCZOS",
            "canvas": "authority_size_centered_white",
        },
        "diagnostics": "diagnostic_only_excluded_from_score_inputs",
        "editability_cost": "separate_not_inferred_from_images",
        "publication_acceptance": "not_claimed",
    }
    html_path = public_root / "index.html"
    html_path.write_text(_render_html(public_manifest), encoding="utf-8")
    public_manifest["html"] = {"path": "index.html", "sha256": _sha256(html_path)}
    public_manifest_path = public_root / "public-review-manifest.yaml"
    public_manifest_path.write_text(
        yaml.safe_dump(public_manifest, sort_keys=False), encoding="utf-8"
    )

    private_manifest = {
        "schema": PRIVATE_SCHEMA,
        "seed_hex": private_seed.hex(),
        "experiment_assignments": experiment_map,
        "keys": private_keys,
        "public_manifest_sha256": _sha256(public_manifest_path),
        "blinding_keys_revealed": False,
        "release_condition": "named_human_scores_fixed",
        "publication_acceptance": "not_claimed",
    }
    private_manifest_path = private_root / "private-review-manifest.yaml"
    private_manifest_path.write_text(
        yaml.safe_dump(private_manifest, sort_keys=False), encoding="utf-8"
    )

    review_state = {
        "schema": REVIEW_STATE_SCHEMA,
        "state": "awaiting_named_human_verdict",
        "public_manifest_sha256": _sha256(public_manifest_path),
        "private_manifest_sha256": _sha256(private_manifest_path),
        "blinding_keys_revealed": False,
        "cold_reproductions": 0,
        "publication_acceptance": "not_claimed",
    }
    review_state_path.parent.mkdir(parents=True, exist_ok=True)
    review_state_path.write_text(
        yaml.safe_dump(review_state, sort_keys=False), encoding="utf-8"
    )
    return {
        "public_manifest": public_manifest,
        "review_state": review_state,
        "public_manifest_path": public_manifest_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture_root", type=Path)
    args = parser.parse_args()
    result = stage_review(args.fixture_root)
    print(
        json.dumps(
            {
                "state": result["review_state"]["state"],
                "public_review": str(result["public_manifest_path"]),
                "public_manifest_sha256": result["review_state"][
                    "public_manifest_sha256"
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
