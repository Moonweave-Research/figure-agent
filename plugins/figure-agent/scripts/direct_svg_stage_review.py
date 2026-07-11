"""Atomically stage a versioned three-way blinded human-review distribution."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import random
import secrets
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml
from direct_svg_packet import validate_packet
from direct_svg_review import CONTAIN_GEOMETRY_POLICY, DirectSvgReviewError
from PIL import Image, ImageChops, ImageOps, PngImagePlugin, UnidentifiedImageError

PANELS = ("C", "F")
LETTERS = ("A", "B", "C")
PUBLIC_SCHEMA = "figure-agent.three-way-blind-review.v1"
RESPONSE_SCHEMA = "figure-agent.three-way-review-response.v1"
STATE_SCHEMA = "figure-agent.direct-svg-review-state.v2"
PRIVATE_SCHEMA = "figure-agent.private-three-way-review-key.v1"
GENERATOR_REVISION = "direct_svg_stage_review.v2"


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _opaque_hash(path: Path, seed: bytes, purpose: str) -> str:
    digest = hashlib.sha256(b"figure-agent.opaque-review.v2\0" + seed + purpose.encode())
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _load_yaml(path: Path, error: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise DirectSvgReviewError(error) from exc
    if not isinstance(value, dict):
        raise DirectSvgReviewError(error)
    return value


def _resolve_path(value: Any, roots: tuple[Path, ...]) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise DirectSvgReviewError("review_prerequisite_path_invalid")
    for root in roots:
        path = (root / value).resolve()
        if path.is_file():
            return path
    raise DirectSvgReviewError("review_prerequisite_missing")


def _validated_run(
    fixture_root: Path,
    run_dir: Path,
    packet_path: Path,
    plugin_root: Path,
) -> tuple[dict[str, Path], str]:
    state_path = run_dir / "run-state.yaml"
    state = _load_yaml(state_path, "run_state_invalid")
    if state.get("schema") != "figure-agent.direct-svg-run-state.v1":
        raise DirectSvgReviewError("run_state_invalid")
    if state.get("state") != "machine_review_ready":
        raise DirectSvgReviewError("run_not_machine_review_ready")
    if state.get("publication_acceptance") != "not_claimed":
        raise DirectSvgReviewError("publication_claim_forbidden")
    validate_packet(packet_path)
    packet_ref = state.get("validated_packet") or state.get("synthesis_packet")
    if isinstance(packet_ref, dict):
        declared_path, declared_hash = packet_ref.get("path"), packet_ref.get("sha256")
    else:
        declared_path = packet_ref
        declared_hash = state.get("validated_packet_sha256")
    resolved = _resolve_path(declared_path, (run_dir, fixture_root, plugin_root))
    if resolved != packet_path.resolve() or declared_hash != _sha256(packet_path):
        raise DirectSvgReviewError("validated_packet_hash_mismatch")
    images: dict[str, Path] = {}
    artifacts = state.get("candidate_artifacts")
    if not isinstance(artifacts, list):
        raise DirectSvgReviewError("candidate_artifacts_invalid")
    for item in artifacts:
        if not isinstance(item, dict) or item.get("panel") not in PANELS:
            raise DirectSvgReviewError("candidate_artifacts_invalid")
        render = _resolve_path(
            item.get("render_path") or item.get("png_path"),
            (run_dir, fixture_root, plugin_root),
        )
        if item.get("render_sha256") != _sha256(render):
            raise DirectSvgReviewError("candidate_render_hash_mismatch")
        images[item["panel"]] = render
    if set(images) != set(PANELS):
        raise DirectSvgReviewError("candidate_artifacts_invalid")
    return images, _sha256(state_path)


def _response_panel() -> dict[str, None]:
    fields = {
        f"option_{letter}_{suffix}": None
        for letter in LETTERS
        for suffix in ("scientific_fidelity", "scientific_evidence")
    }
    return {
        **fields,
        "composition_preference": None,
        "illustration_quality_preference": None,
        "typography_preference": None,
        "borderline_or_disputed": None,
    }


def _response_document() -> dict[str, Any]:
    return {
        "schema": RESPONSE_SCHEMA,
        "primary_reviewer": {"name": None, "reviewed_at": None},
        "second_reviewer": {
            "required": None,
            "name": None,
            "reviewed_at": None,
        },
        "panels": {panel: _response_panel() for panel in PANELS},
    }


def _response_has_answers(response: dict[str, Any]) -> bool:
    values: list[Any] = []
    for role in ("primary_reviewer", "second_reviewer"):
        block = response.get(role, {})
        if isinstance(block, dict):
            values.extend(block.values())
    panels = response.get("panels", {})
    if isinstance(panels, dict):
        for block in panels.values():
            if isinstance(block, dict):
                values.extend(block.values())
    return any(value is not None for value in values)


def _fail_if_responses_exist(review_root: Path) -> None:
    for path in review_root.glob("distributions/*/response.yaml"):
        if _response_has_answers(_load_yaml(path, "response_invalid")):
            raise DirectSvgReviewError("existing_review_response")


def _normalized(
    source: Path,
    destination: Path,
    authority_size: tuple[int, int],
    packet_id: str,
) -> None:
    try:
        with Image.open(source) as opened:
            contained = ImageOps.contain(
                opened.convert("RGB"), authority_size, method=Image.Resampling.LANCZOS
            )
    except (FileNotFoundError, OSError, UnidentifiedImageError) as exc:
        raise DirectSvgReviewError("review_image_invalid") from exc
    canvas = Image.new("RGB", authority_size, "white")
    canvas.paste(
        contained,
        ((authority_size[0] - contained.width) // 2, (authority_size[1] - contained.height) // 2),
    )
    info = PngImagePlugin.PngInfo()
    info.add_text("packet_id", packet_id)
    canvas.save(destination, format="PNG", pnginfo=info)


def _write_panel(
    panel: str,
    sources: dict[str, Path],
    output_dir: Path,
    seed: bytes,
) -> tuple[dict[str, Any], dict[str, Any]]:
    output_dir.mkdir(parents=True)
    with Image.open(sources["authority"]) as authority:
        authority_size = authority.size
    roles = ["authority", "run_one", "run_two"]
    random.Random(hashlib.sha256(seed + panel.encode()).digest()).shuffle(roles)
    mapping = dict(zip(LETTERS, roles, strict=True))
    public_options: dict[str, Any] = {}
    private_options: dict[str, Any] = {}
    for letter in LETTERS:
        path = output_dir / f"option-{letter.lower()}.png"
        packet_id = hashlib.sha256(seed + panel.encode() + letter.encode()).hexdigest()
        _normalized(sources[mapping[letter]], path, authority_size, packet_id)
        public_options[letter] = {
            "path": path.name,
            "opaque_sha256": _opaque_hash(path, seed, f"{panel}-{letter}"),
        }
        private_options[letter] = {
            "role": mapping[letter],
            "content_sha256": _sha256(path),
        }
    diagnostics: list[dict[str, Any]] = []
    for left, right in (("A", "B"), ("A", "C"), ("B", "C")):
        with Image.open(output_dir / f"option-{left.lower()}.png") as first, Image.open(
            output_dir / f"option-{right.lower()}.png"
        ) as second:
            difference = ImageChops.difference(first.convert("RGB"), second.convert("RGB"))
            path = output_dir / f"diagnostic-{left.lower()}-{right.lower()}.png"
            difference.save(path)
        diagnostics.append(
            {
                "path": path.name,
                "opaque_sha256": _opaque_hash(path, seed, f"diag-{panel}-{left}-{right}"),
                "diagnostic_only": True,
            }
        )
    return (
        {
            "options": public_options,
            "score_inputs": [public_options[letter] for letter in LETTERS],
            "diagnostics": diagnostics,
            "response_template": _response_panel(),
        },
        private_options,
    )


def _semantic_context(fixture_root: Path) -> dict[str, Any]:
    packet = _load_yaml(fixture_root / "contract/semantic-packet.yaml", "semantic_packet_invalid")
    return {
        "scientific_objects": packet.get("scientific_objects"),
        "object_relations": packet.get("object_relations"),
        "text_content": packet.get("text_content"),
    }


def _html(manifest: dict[str, Any]) -> str:
    sections = []
    for panel in PANELS:
        images = "".join(
            f'<figure><img src="panels/{panel}/option-{letter.lower()}.png" '
            f'alt="Panel {panel} Option {letter}"><figcaption>Option {letter}</figcaption></figure>'
            for letter in LETTERS
        )
        response = html.escape(yaml.safe_dump(manifest["responses"][panel], sort_keys=False))
        sections.append(
            f"<section><h2>Panel {panel}</h2><div class='options'>{images}</div>"
            f"<h3>Unanswered response</h3><pre>{response}</pre></section>"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>Three-way opaque review</title>"
        "<style>body{font-family:system-ui;max-width:1500px;margin:auto}.options{display:grid;"
        "grid-template-columns:repeat(3,1fr);gap:1rem}img{width:100%;height:auto}"
        "figcaption{text-align:center;font-weight:700}pre{white-space:pre-wrap}</style></head><body>"
        "<h1>Three-way opaque review</h1><p>Diagnostics are diagnostic only and excluded "
        "from score inputs. Editability and cost remain separate.</p>"
        + "".join(sections)
        + "</body></html>"
    )


def _private_permissions(root: Path) -> None:
    os.chmod(root, 0o700)
    for path in root.rglob("*"):
        os.chmod(path, 0o700 if path.is_dir() else 0o600)


def _atomic_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=path.parent, delete=False, encoding="utf-8"
    ) as handle:
        yaml.safe_dump(value, handle, sort_keys=False)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def export_public_distribution(distribution: Path, destination: Path) -> Path:
    """Export exactly one validated public distribution and nothing adjacent."""
    if destination.exists():
        raise DirectSvgReviewError("export_destination_exists")
    manifest = _load_yaml(distribution / "manifest.yaml", "public_manifest_invalid")
    if manifest.get("schema") != PUBLIC_SCHEMA:
        raise DirectSvgReviewError("public_manifest_invalid")
    shutil.copytree(distribution, destination)
    return destination


def stage_review(
    fixture_root: Path,
    *,
    review_root: Path,
    private_root: Path,
    generator_commit: str,
    private_seed: bytes | None = None,
    replay: bool = False,
    failure_injection: str | None = None,
) -> dict[str, Any]:
    """Build, validate, and atomically publish one immutable review version."""
    fixture_root = fixture_root.resolve()
    review_root = review_root.resolve()
    private_root = private_root.resolve()
    plugin_root = fixture_root.parents[1]
    if review_root == private_root or private_root.is_relative_to(review_root):
        raise DirectSvgReviewError("private_root_must_be_external")
    if not generator_commit:
        raise DirectSvgReviewError("generator_commit_required")
    seed = private_seed if private_seed is not None else secrets.token_bytes(32)
    if not isinstance(seed, bytes) or len(seed) < 32:
        raise DirectSvgReviewError("private_seed_invalid")
    _fail_if_responses_exist(review_root)

    run_one, run_one_state_hash = _validated_run(
        fixture_root,
        fixture_root / "runs/test-a",
        fixture_root / "packets/test-a-reconstruction.yaml",
        plugin_root,
    )
    run_two, run_two_state_hash = _validated_run(
        fixture_root,
        fixture_root / "runs/test-b",
        fixture_root / "packets/test-b-synthesis.yaml",
        plugin_root,
    )
    semantic_path = fixture_root / "contract/semantic-packet.yaml"
    authorities = {
        panel: fixture_root / f"reference/crops/panel-{panel.lower()}.png" for panel in PANELS
    }
    upstream = {
        "run_state_hashes": [run_one_state_hash, run_two_state_hash],
        "semantic_packet_sha256": _sha256(semantic_path),
        "authority_sha256": {panel: _sha256(path) for panel, path in authorities.items()},
    }
    version_digest = hashlib.sha256(
        seed + json.dumps(upstream, sort_keys=True).encode() + generator_commit.encode()
    ).hexdigest()[:16]
    version = f"review-v1-{version_digest}"
    distribution_path = review_root / "distributions" / version
    private_path = private_root / version
    if distribution_path.exists():
        if replay:
            manifest_path = distribution_path / "manifest.yaml"
            return {
                "version": version,
                "distribution_path": distribution_path,
                "private_path": private_path,
                "public_manifest_sha256": _sha256(manifest_path),
            }
        raise DirectSvgReviewError("review_version_exists")

    review_root.mkdir(parents=True, exist_ok=True)
    private_root.mkdir(parents=True, exist_ok=True)
    os.chmod(private_root, 0o700)
    public_temp = Path(tempfile.mkdtemp(prefix=".review-stage-", dir=review_root))
    private_temp = Path(tempfile.mkdtemp(prefix=".key-stage-", dir=private_root))
    try:
        public_panels: dict[str, Any] = {}
        private_panels: dict[str, Any] = {}
        for panel in PANELS:
            public_panels[panel], private_panels[panel] = _write_panel(
                panel,
                {
                    "authority": authorities[panel],
                    "run_one": run_one[panel],
                    "run_two": run_two[panel],
                },
                public_temp / "panels" / panel,
                seed,
            )
        response = _response_document()
        (public_temp / "response.yaml").write_text(
            yaml.safe_dump(response, sort_keys=False), encoding="utf-8"
        )
        manifest = {
            "schema": PUBLIC_SCHEMA,
            "version": version,
            "panels": public_panels,
            "responses": {panel: _response_panel() for panel in PANELS},
            "response_schema": RESPONSE_SCHEMA,
            "semantic_review_context": _semantic_context(fixture_root),
            "normalization": {
                "policy": CONTAIN_GEOMETRY_POLICY,
                "application": "all_three_options",
                "resampling": "LANCZOS",
                "canvas": "authority_dimensions_centered_white",
            },
            "upstream_bindings": upstream,
            "generator": {"revision": GENERATOR_REVISION, "commit": generator_commit},
            "publication_acceptance": "not_claimed",
        }
        (public_temp / "index.html").write_text(_html(manifest), encoding="utf-8")
        manifest["html_sha256"] = _sha256(public_temp / "index.html")
        (public_temp / "manifest.yaml").write_text(
            yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
        )
        private_manifest = {
            "schema": PRIVATE_SCHEMA,
            "version": version,
            "seed_hex": seed.hex(),
            "panel_assignments": private_panels,
            "public_manifest_sha256": _sha256(public_temp / "manifest.yaml"),
            "blinding_keys_revealed": False,
            "release_condition": "named_human_scores_fixed",
        }
        (private_temp / "key.yaml").write_text(
            yaml.safe_dump(private_manifest, sort_keys=False), encoding="utf-8"
        )
        _private_permissions(private_temp)
        if _response_has_answers(response):
            raise DirectSvgReviewError("staged_response_not_empty")
        decoded = []
        for path in public_temp.glob("panels/*/option-?.png"):
            with Image.open(path) as image:
                decoded.append(hashlib.sha256(image.convert("RGB").tobytes()).hexdigest())
        if len(decoded) != 6 or len(decoded) != len(set(decoded)):
            raise DirectSvgReviewError("decoded_pixel_duplicate")
        if failure_injection == "before_publish":
            raise RuntimeError("injected")
        distribution_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(private_temp, private_path)
        os.replace(public_temp, distribution_path)
        state = {
            "schema": STATE_SCHEMA,
            "state": "awaiting_named_human_verdict",
            "version": version,
            "public_manifest_sha256": _sha256(distribution_path / "manifest.yaml"),
            "private_manifest_sha256": _sha256(private_path / "key.yaml"),
            "upstream_bindings": upstream,
            "generator": {"revision": GENERATOR_REVISION, "commit": generator_commit},
            "response_schema": RESPONSE_SCHEMA,
            "normalization_policy": CONTAIN_GEOMETRY_POLICY,
            "blinding_keys_revealed": False,
            "cold_reproductions": 0,
            "publication_acceptance": "not_claimed",
        }
        _atomic_yaml(review_root / "review-state.yaml", state)
    finally:
        if public_temp.exists():
            shutil.rmtree(public_temp)
        if private_temp.exists():
            shutil.rmtree(private_temp)
    return {
        "version": version,
        "distribution_path": distribution_path,
        "private_path": private_path,
        "public_manifest_sha256": _sha256(distribution_path / "manifest.yaml"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture_root", type=Path)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--generator-commit", required=True)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--export-to", type=Path)
    args = parser.parse_args()
    result = stage_review(
        args.fixture_root,
        review_root=args.review_root,
        private_root=args.private_root,
        generator_commit=args.generator_commit,
        replay=args.replay,
    )
    if args.export_to:
        export_public_distribution(Path(result["distribution_path"]), args.export_to)
    print(
        json.dumps(
            {
                "version": result["version"],
                "public_review": str(result["distribution_path"]),
                "public_manifest_sha256": result["public_manifest_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
