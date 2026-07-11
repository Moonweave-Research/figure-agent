"""Stage and protect a versioned three-way blinded human review."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import platform
import random
import secrets
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from direct_svg_packet import validate_packet
from direct_svg_review import CONTAIN_GEOMETRY_POLICY, DirectSvgReviewError
from PIL import (
    Image,
    ImageChops,
    ImageOps,
    ImageStat,
    PngImagePlugin,
    UnidentifiedImageError,
)
from PIL import __version__ as PILLOW_VERSION

PANELS = ("C", "F")
LETTERS = ("A", "B", "C")
PUBLIC_SCHEMA = "figure-agent.three-way-blind-review.v3"
RESPONSE_SCHEMA = "figure-agent.three-way-review-response.v2"
STATE_SCHEMA = "figure-agent.direct-svg-review-state.v4"
PRIVATE_SCHEMA = "figure-agent.private-three-way-review-key.v3"
GENERATOR_REVISION = "direct_svg_stage_review.v4"
PERCEPTUAL_METRIC = "normalized_rgb_mean_absolute_error.v1"
PERCEPTUAL_THRESHOLD = 0.002
GENERATOR_FILES = (
    "pyproject.toml",
    "uv.lock",
    "scripts/direct_svg_stage_review.py",
    "scripts/direct_svg_review.py",
    "scripts/direct_svg_packet.py",
    "scripts/hybrid/comparison_report.py",
)
RESPONSE_STATES = (
    "scientific_gate_pending",
    "primary_scientific_fixed",
    "primary_visual_fixed",
    "second_scientific_fixed",
    "second_visual_fixed",
    "finalized",
)
VISUAL_CHOICES = {*LETTERS, "tie"}
SCIENTIFIC_CHOICES = {"pass", "fail"}


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _yaml_bytes(value: dict[str, Any]) -> bytes:
    return yaml.safe_dump(value, sort_keys=False).encode("utf-8")


def _opaque_commitment(raw_hash: str, seed: bytes, purpose: str) -> str:
    digest = hashlib.sha256(
        b"figure-agent.opaque-review.v3\0" + seed + b"\0" + purpose.encode() + b"\0"
    )
    digest.update(raw_hash.encode())
    return f"sha256:{digest.hexdigest()}"


def _opaque_file_hash(path: Path, seed: bytes, purpose: str) -> str:
    return _opaque_commitment(_sha256(path), seed, purpose)


def _load_yaml(path: Path, error: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise DirectSvgReviewError(error) from exc
    if not isinstance(value, dict):
        raise DirectSvgReviewError(error)
    return value


def _require_exact_keys(value: Any, expected: set[str], error: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise DirectSvgReviewError(error)
    return value


def _resolve_path(value: Any, roots: tuple[Path, ...]) -> Path:
    raw = Path(value) if isinstance(value, str) else None
    if (
        raw is None
        or not value
        or raw.is_absolute()
        or "." in raw.parts
        or ".." in raw.parts
    ):
        raise DirectSvgReviewError("review_prerequisite_path_invalid")
    authorized_roots = tuple(root.resolve() for root in roots)
    escaped = False
    for base in roots:
        candidate = Path(os.path.abspath(base / raw))
        owners = [root for root in authorized_roots if candidate.is_relative_to(root)]
        if not owners:
            escaped = escaped or ".." in raw.parts
            continue
        owner = max(owners, key=lambda root: len(root.parts))
        try:
            relative = candidate.relative_to(owner)
            cursor = owner
            for part in relative.parts:
                cursor = cursor / part
                if cursor.is_symlink():
                    raise DirectSvgReviewError("review_prerequisite_path_invalid")
            path = candidate.resolve(strict=True)
        except FileNotFoundError:
            continue
        if path == candidate and path.is_file():
            return path
    if escaped:
        raise DirectSvgReviewError("review_prerequisite_path_invalid")
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


def _reviewer_template() -> dict[str, None]:
    return {"name": None, "reviewed_at": None}


def _scientific_template() -> dict[str, dict[str, None]]:
    return {letter: {"verdict": None, "evidence": None} for letter in LETTERS}


def _visual_template() -> dict[str, None]:
    return {
        "composition_preference": None,
        "illustration_quality_preference": None,
        "typography_preference": None,
        "borderline_or_disputed": None,
    }


def _review_panels_template() -> dict[str, dict[str, Any]]:
    return {
        panel: {"scientific": _scientific_template(), "visual": _visual_template()}
        for panel in PANELS
    }


def _response_document() -> dict[str, Any]:
    return {
        "schema": RESPONSE_SCHEMA,
        "state": "scientific_gate_pending",
        "primary_review": {
            "reviewer": _reviewer_template(),
            "panels": _review_panels_template(),
        },
        "second_review": {
            "required": None,
            "reviewer": _reviewer_template(),
            "panels": _review_panels_template(),
        },
    }


def _legacy_response_has_answers(response: dict[str, Any]) -> bool:
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


def _response_has_answers(response: dict[str, Any]) -> bool:
    if response.get("schema") == RESPONSE_SCHEMA:
        return response != _response_document()
    if response.get("schema") == "figure-agent.three-way-review-response.v1":
        return _legacy_response_has_answers(response)
    raise DirectSvgReviewError("response_invalid")


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
        (
            (authority_size[0] - contained.width) // 2,
            (authority_size[1] - contained.height) // 2,
        ),
    )
    info = PngImagePlugin.PngInfo()
    info.add_text("packet_id", packet_id)
    canvas.save(destination, format="PNG", pnginfo=info)


def _perceptual_distance(first: Path, second: Path) -> float:
    try:
        with Image.open(first) as left, Image.open(second) as right:
            if left.size != right.size:
                raise DirectSvgReviewError("perceptual_geometry_mismatch")
            difference = ImageChops.difference(left.convert("RGB"), right.convert("RGB"))
            return sum(ImageStat.Stat(difference).mean) / (3 * 255)
    except (FileNotFoundError, OSError, UnidentifiedImageError) as exc:
        raise DirectSvgReviewError("review_image_invalid") from exc


def assert_perceptually_distinct(
    paths: list[Path], *, threshold: float = PERCEPTUAL_THRESHOLD
) -> None:
    """Fail closed when exact or near-duplicate score inputs are present."""
    if not isinstance(threshold, float | int) or isinstance(threshold, bool) or threshold < 0:
        raise DirectSvgReviewError("perceptual_threshold_invalid")
    raw_hashes = [_sha256(path) for path in paths]
    if len(raw_hashes) != len(set(raw_hashes)):
        raise DirectSvgReviewError("exact_duplicate")
    for index, left in enumerate(paths):
        for right in paths[index + 1 :]:
            if _perceptual_distance(left, right) <= threshold:
                raise DirectSvgReviewError("perceptual_duplicate")


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
    paths: list[Path] = []
    for letter in LETTERS:
        path = output_dir / f"option-{letter.lower()}.png"
        packet_id = hashlib.sha256(seed + panel.encode() + letter.encode()).hexdigest()
        _normalized(sources[mapping[letter]], path, authority_size, packet_id)
        paths.append(path)
        public_options[letter] = {
            "path": path.name,
            "opaque_sha256": _opaque_file_hash(path, seed, f"{panel}-{letter}"),
        }
        private_options[letter] = {
            "role": mapping[letter],
            "content_sha256": _sha256(path),
        }
    assert_perceptually_distinct(paths)
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
                "opaque_sha256": _opaque_file_hash(
                    path, seed, f"diag-{panel}-{left}-{right}"
                ),
                "diagnostic_only": True,
            }
        )
    return (
        {
            "options": public_options,
            "score_inputs": [public_options[letter] for letter in LETTERS],
            "diagnostics": diagnostics,
        },
        private_options,
    )


def _semantic_context(fixture_root: Path) -> dict[str, Any]:
    packet = _load_yaml(
        fixture_root / "contract/semantic-packet.yaml", "semantic_packet_invalid"
    )
    return {
        "scientific_objects": packet.get("scientific_objects"),
        "object_relations": packet.get("object_relations"),
        "text_content": packet.get("text_content"),
    }


def _html(manifest: dict[str, Any], response: dict[str, Any]) -> str:
    sections = []
    for panel in PANELS:
        images = "".join(
            f'<figure><img src="panels/{panel}/option-{letter.lower()}.png" '
            f'alt="Panel {panel} Option {letter}"><figcaption>Option {letter}</figcaption></figure>'
            for letter in LETTERS
        )
        scientific = html.escape(
            yaml.safe_dump(
                response["primary_review"]["panels"][panel]["scientific"],
                sort_keys=False,
            )
        )
        sections.append(
            f"<section><h2>Panel {panel}</h2><div class='options'>{images}</div>"
            "<h3>Step 1: scientific hard gate</h3>"
            f"<pre>{scientific}</pre><p>Visual scoring unlocks only after this gate is fixed.</p>"
            "</section>"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>Three-way opaque review</title>"
        "<style>body{font-family:system-ui;max-width:1500px;margin:auto}.options{display:grid;"
        "grid-template-columns:repeat(3,1fr);gap:1rem}img{width:100%;height:auto}"
        "figcaption{text-align:center;font-weight:700}pre{white-space:pre-wrap}</style></head><body>"
        "<h1>Three-way opaque review</h1><p>Diagnostics are excluded from scoring. "
        "Record a named scientific verdict and evidence for every option before visual scoring. "
        "A borderline or disputed score requires a distinct second named reviewer.</p>"
        + "".join(sections)
        + "</body></html>"
    )


def _private_permissions(root: Path) -> None:
    os.chmod(root, 0o700)
    for path in root.rglob("*"):
        os.chmod(path, 0o700 if path.is_dir() else 0o600)


def _atomic_bytes(path: Path, value: bytes, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(value)
        temporary = Path(handle.name)
    if mode is not None:
        os.chmod(temporary, mode)
    os.replace(temporary, path)


def _atomic_yaml(path: Path, value: dict[str, Any], mode: int | None = None) -> None:
    _atomic_bytes(path, _yaml_bytes(value), mode)


def _generator_binding(
    plugin_root: Path,
    generator_commit: str,
    declared_script_sha256: str | None,
    declared_receipt_sha256: str | None,
) -> dict[str, Any]:
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{generator_commit}^{{commit}}"],
            cwd=plugin_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        prefix = subprocess.check_output(
            ["git", "rev-parse", "--show-prefix"], cwd=plugin_root, text=True
        ).strip()
        committed_files = {
            relative: subprocess.check_output(
                ["git", "show", f"{resolved}:{prefix}{relative}"],
                cwd=plugin_root,
                stderr=subprocess.DEVNULL,
            )
            for relative in GENERATOR_FILES
        }
    except (OSError, subprocess.CalledProcessError) as exc:
        raise DirectSvgReviewError("generator_commit_invalid") from exc
    file_hashes = {
        relative: _sha256_bytes(content) for relative, content in committed_files.items()
    }
    for relative, committed_hash in file_hashes.items():
        local_path = plugin_root / relative
        if (
            not local_path.is_file()
            or local_path.is_symlink()
            or _sha256(local_path) != committed_hash
        ):
            raise DirectSvgReviewError("generator_script_blob_mismatch")
    script_hash = file_hashes["scripts/direct_svg_stage_review.py"]
    if declared_script_sha256 is not None and declared_script_sha256 != script_hash:
        raise DirectSvgReviewError("generator_script_blob_mismatch")
    environment = {
        "python": platform.python_version(),
        "pillow": PILLOW_VERSION,
        "pyyaml": yaml.__version__,
        "png_zlib": str(getattr(Image.core, "zlib_version", "unknown")),
        "resampling": "Pillow.Image.Resampling.LANCZOS",
    }
    receipt_body: dict[str, Any] = {
        "revision": GENERATOR_REVISION,
        "commit": resolved,
        "files": file_hashes,
        "environment": environment,
    }
    receipt_hash = _sha256_bytes(
        json.dumps(receipt_body, sort_keys=True, separators=(",", ":")).encode()
    )
    if declared_receipt_sha256 is not None and declared_receipt_sha256 != receipt_hash:
        raise DirectSvgReviewError("generator_receipt_mismatch")
    return {**receipt_body, "receipt_sha256": receipt_hash}


def _tree_bytes(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        raise DirectSvgReviewError("replay_byte_mismatch")
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _compare_tree(expected: Path, actual: Path) -> None:
    if _tree_bytes(expected) != _tree_bytes(actual):
        raise DirectSvgReviewError("replay_byte_mismatch")


def _read_regular_snapshot(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise DirectSvgReviewError("export_validation_failed") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise DirectSvgReviewError("export_validation_failed")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _commitments_from_key(key: dict[str, Any]) -> dict[str, str]:
    try:
        seed = bytes.fromhex(key["seed_hex"])
        raw = key["raw_upstream_bindings"]
        return {
            "run_state_1": _opaque_commitment(
                raw["run_state_hashes"][0], seed, "run-state-1"
            ),
            "run_state_2": _opaque_commitment(
                raw["run_state_hashes"][1], seed, "run-state-2"
            ),
            "semantic_packet": _opaque_commitment(
                raw["semantic_packet_sha256"], seed, "semantic-packet"
            ),
            **{
                f"authority_{panel}": _opaque_commitment(
                    raw["authority_sha256"][panel], seed, f"authority-{panel}"
                )
                for panel in PANELS
            },
        }
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise DirectSvgReviewError("export_validation_failed") from exc


def _validated_export_snapshot(
    distribution: Path, review_root: Path, private_root: Path
) -> dict[str, bytes]:
    try:
        if distribution.is_symlink() or review_root.is_symlink() or private_root.is_symlink():
            raise DirectSvgReviewError("export_validation_failed")
        distribution = distribution.resolve(strict=True)
        review_root = review_root.resolve(strict=True)
        private_root = private_root.resolve(strict=True)
        state_path = review_root / "review-state.yaml"
        state_bytes = _read_regular_snapshot(state_path)
        state = yaml.safe_load(state_bytes)
        if not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA:
            raise DirectSvgReviewError("export_validation_failed")
        version = state.get("version")
        expected_distribution = (review_root / "distributions" / version).resolve(strict=True)
        if distribution != expected_distribution:
            raise DirectSvgReviewError("export_validation_failed")
        manifest_bytes = _read_regular_snapshot(distribution / "manifest.yaml")
        manifest = yaml.safe_load(manifest_bytes)
        if (
            not isinstance(manifest, dict)
            or manifest.get("schema") != PUBLIC_SCHEMA
            or manifest.get("version") != version
            or state.get("public_manifest_sha256") != _sha256_bytes(manifest_bytes)
        ):
            raise DirectSvgReviewError("export_validation_failed")
        key_path = private_root / version / "key.yaml"
        key_bytes = _read_regular_snapshot(key_path)
        key = yaml.safe_load(key_bytes)
        if (
            not isinstance(key, dict)
            or key.get("schema") != PRIVATE_SCHEMA
            or key.get("version") != version
            or state.get("private_manifest_sha256") != _sha256_bytes(key_bytes)
            or key.get("public_manifest_sha256") != _sha256_bytes(manifest_bytes)
            or key.get("public_upstream_commitments") != manifest.get("upstream_commitments")
            or _commitments_from_key(key) != manifest.get("upstream_commitments")
            or key.get("generator") != manifest.get("generator")
            or state.get("generator") != manifest.get("generator")
        ):
            raise DirectSvgReviewError("export_validation_failed")
        current_generator = _generator_binding(
            Path(__file__).resolve().parents[1],
            manifest["generator"]["commit"],
            manifest["generator"]["files"]["scripts/direct_svg_stage_review.py"],
            manifest["generator"]["receipt_sha256"],
        )
        if current_generator != manifest.get("generator"):
            raise DirectSvgReviewError("export_validation_failed")
        inventory = manifest.get("public_inventory")
        if not isinstance(inventory, dict):
            raise DirectSvgReviewError("export_validation_failed")
        allowed = {"manifest.yaml", *inventory}
        if state.get("blinding_keys_revealed") is True:
            allowed.add("unblinding.yaml")
        actual: set[str] = set()
        for path in distribution.rglob("*"):
            relative = path.relative_to(distribution).as_posix()
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise DirectSvgReviewError("export_validation_failed")
            if path.is_file():
                actual.add(relative)
        if actual != allowed:
            raise DirectSvgReviewError("export_validation_failed")
        snapshots = {"manifest.yaml": manifest_bytes}
        for relative, expected_hash in inventory.items():
            if (
                not isinstance(relative, str)
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
            ):
                raise DirectSvgReviewError("export_validation_failed")
            content = _read_regular_snapshot(distribution / relative)
            bound_hash = (
                state.get("response_sha256")
                if expected_hash == "state:response_sha256"
                else expected_hash
            )
            if bound_hash != _sha256_bytes(content):
                raise DirectSvgReviewError("export_validation_failed")
            snapshots[relative] = content
        response = yaml.safe_load(snapshots["response.yaml"])
        if not isinstance(response, dict):
            raise DirectSvgReviewError("export_validation_failed")
        _validate_response(response)
        if response.get("state") != state.get("response_state"):
            raise DirectSvgReviewError("export_validation_failed")
        for panel in PANELS:
            for letter in LETTERS:
                relative = f"panels/{panel}/option-{letter.lower()}.png"
                if key["panel_assignments"][panel][letter]["content_sha256"] != _sha256_bytes(
                    snapshots[relative]
                ):
                    raise DirectSvgReviewError("export_validation_failed")
        if state.get("blinding_keys_revealed") is True:
            unblinding = _read_regular_snapshot(distribution / "unblinding.yaml")
            if state.get("unblinding_sha256") != _sha256_bytes(unblinding):
                raise DirectSvgReviewError("export_validation_failed")
            snapshots["unblinding.yaml"] = unblinding
        return snapshots
    except (
        DirectSvgReviewError,
        IndexError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        yaml.YAMLError,
    ) as exc:
        if isinstance(exc, DirectSvgReviewError) and str(exc) == "export_validation_failed":
            raise
        raise DirectSvgReviewError("export_validation_failed") from exc


def export_public_distribution(
    distribution: Path,
    destination: Path,
    *,
    review_root: Path,
    private_root: Path,
) -> Path:
    """Validate and export an exact regular-file snapshot of the current distribution."""
    if destination.exists():
        raise DirectSvgReviewError("export_destination_exists")
    snapshots = _validated_export_snapshot(distribution, review_root, private_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".review-export-", dir=destination.parent))
    try:
        for relative, content in snapshots.items():
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return destination


def _build_staged_bundle(
    fixture_root: Path,
    review_root: Path,
    private_root: Path,
    seed: bytes,
    generator: dict[str, str],
) -> tuple[str, Path, Path, dict[str, Any]]:
    plugin_root = fixture_root.parents[1]
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
        panel: fixture_root / f"reference/crops/panel-{panel.lower()}.png"
        for panel in PANELS
    }
    raw_upstream = {
        "run_state_hashes": [run_one_state_hash, run_two_state_hash],
        "semantic_packet_sha256": _sha256(semantic_path),
        "authority_sha256": {panel: _sha256(path) for panel, path in authorities.items()},
    }
    upstream_commitments = {
        "run_state_1": _opaque_commitment(run_one_state_hash, seed, "run-state-1"),
        "run_state_2": _opaque_commitment(run_two_state_hash, seed, "run-state-2"),
        "semantic_packet": _opaque_commitment(
            raw_upstream["semantic_packet_sha256"], seed, "semantic-packet"
        ),
        **{
            f"authority_{panel}": _opaque_commitment(
                raw_upstream["authority_sha256"][panel], seed, f"authority-{panel}"
            )
            for panel in PANELS
        },
    }
    version_digest = hashlib.sha256(
        seed
        + json.dumps(raw_upstream, sort_keys=True).encode()
        + json.dumps(generator, sort_keys=True).encode()
    ).hexdigest()[:16]
    version = f"review-v3-{version_digest}"
    public_temp = Path(tempfile.mkdtemp(prefix=".review-stage-", dir=review_root))
    private_temp = Path(tempfile.mkdtemp(prefix=".key-stage-", dir=private_root))
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
    response_bytes = _yaml_bytes(response)
    (public_temp / "response.yaml").write_bytes(response_bytes)
    manifest = {
        "schema": PUBLIC_SCHEMA,
        "version": version,
        "panels": public_panels,
        "responses": {
            panel: {"scientific_gate": None, "visual_scoring": None} for panel in PANELS
        },
        "response_schema": RESPONSE_SCHEMA,
        "response_contract": {
            "additional_fields": False,
            "state_machine": list(RESPONSE_STATES),
            "scientific_gate_precedes_visual_scoring": True,
            "named_reviewer_and_date_required": True,
            "scientific_evidence_required": True,
            "distinct_second_reviewer_required_when": "borderline_or_disputed",
        },
        "semantic_review_context": _semantic_context(fixture_root),
        "normalization": {
            "policy": CONTAIN_GEOMETRY_POLICY,
            "application": "all_three_options",
            "resampling": "LANCZOS",
            "canvas": "authority_dimensions_centered_white",
        },
        "perceptual_duplicate_policy": {
            "metric": PERCEPTUAL_METRIC,
            "threshold": PERCEPTUAL_THRESHOLD,
            "fail_when": "distance_lte_threshold",
            "scope": "within_panel_all_option_pairs",
            "calibration": "inclusive_boundary_and_localized_single-pixel_regression",
            "limitation": "global_mean_metric_may_underweight_small_local_defects",
            "authority": "duplicate_screen_only_not_visual_or_publication_acceptance",
        },
        "upstream_commitments": upstream_commitments,
        "generator": generator,
        "publication_acceptance": "not_claimed",
    }
    (public_temp / "index.html").write_text(
        _html(manifest, response), encoding="utf-8"
    )
    manifest["html_sha256"] = _sha256(public_temp / "index.html")
    manifest["public_inventory"] = {
        path.relative_to(public_temp).as_posix(): (
            "state:response_sha256"
            if path.name == "response.yaml"
            else _sha256(path)
        )
        for path in sorted(public_temp.rglob("*"))
        if path.is_file()
    }
    (public_temp / "manifest.yaml").write_bytes(_yaml_bytes(manifest))
    private_manifest = {
        "schema": PRIVATE_SCHEMA,
        "version": version,
        "seed_hex": seed.hex(),
        "panel_assignments": private_panels,
        "raw_upstream_bindings": raw_upstream,
        "public_upstream_commitments": upstream_commitments,
        "generator": generator,
        "public_manifest_sha256": _sha256(public_temp / "manifest.yaml"),
        "blinding_keys_revealed": False,
        "release_condition": "validated_finalized_named_human_scores",
    }
    (private_temp / "key.yaml").write_bytes(_yaml_bytes(private_manifest))
    _private_permissions(private_temp)
    if _response_has_answers(response):
        raise DirectSvgReviewError("staged_response_not_empty")
    state = {
        "schema": STATE_SCHEMA,
        "state": "awaiting_named_human_verdict",
        "version": version,
        "public_manifest_sha256": _sha256(public_temp / "manifest.yaml"),
        "private_manifest_sha256": _sha256(private_temp / "key.yaml"),
        "upstream_commitments": upstream_commitments,
        "generator": generator,
        "response_schema": RESPONSE_SCHEMA,
        "response_state": "scientific_gate_pending",
        "response_sha256": _sha256_bytes(response_bytes),
        "finalized_response_sha256": None,
        "normalization_policy": CONTAIN_GEOMETRY_POLICY,
        "perceptual_duplicate_policy": manifest["perceptual_duplicate_policy"],
        "blinding_keys_revealed": False,
        "cold_reproductions": 0,
        "publication_acceptance": "not_claimed",
    }
    return version, public_temp, private_temp, state


def _restore_state(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        _atomic_bytes(path, previous)


class _SimulatedCrash(BaseException):
    """Test-only interruption that bypasses normal transactional rollback."""


def _inject(step: str, failure_injection: str | None, crash_injection: str | None) -> None:
    if crash_injection == step:
        raise _SimulatedCrash("simulated_crash")
    if failure_injection == step:
        raise RuntimeError("injected")


def _previous_state_from_journal(journal: dict[str, Any]) -> bytes | None:
    encoded = journal.get("previous_state_hex")
    if encoded is None:
        return None
    if not isinstance(encoded, str):
        raise DirectSvgReviewError("transaction_journal_invalid")
    try:
        return bytes.fromhex(encoded)
    except ValueError as exc:
        raise DirectSvgReviewError("transaction_journal_invalid") from exc


def recover_review_transaction(review_root: Path, private_root: Path) -> dict[str, str]:
    """Conservatively roll back one interrupted publication or reveal transaction."""
    review_root = review_root.resolve()
    private_root = private_root.resolve()
    journals = [
        path
        for path in (
            review_root / ".publish-journal.yaml",
            review_root / ".reveal-journal.yaml",
        )
        if path.exists()
    ]
    if not journals:
        return {"status": "no_pending_transaction"}
    if len(journals) != 1:
        raise DirectSvgReviewError("multiple_transaction_journals")
    journal_path = journals[0]
    journal = _load_yaml(journal_path, "transaction_journal_invalid")
    version = journal.get("version")
    if not isinstance(version, str) or not version.startswith("review-v3-"):
        raise DirectSvgReviewError("transaction_journal_invalid")
    previous_state = _previous_state_from_journal(journal)
    state_path = review_root / "review-state.yaml"
    kind = journal.get("kind")
    if kind == "publication":
        expected = {
            "schema",
            "kind",
            "version",
            "previous_state_hex",
            "private_published",
            "public_published",
            "state_published",
        }
        _require_exact_keys(journal, expected, "transaction_journal_invalid")
        distribution = review_root / "distributions" / version
        protected = private_root / version
        if journal["state_published"]:
            _restore_state(state_path, previous_state)
        if journal["public_published"] and distribution.exists():
            shutil.rmtree(distribution)
        if journal["private_published"] and protected.exists():
            shutil.rmtree(protected)
    elif kind == "reveal":
        expected = {
            "schema",
            "kind",
            "version",
            "previous_state_hex",
            "stage_written",
            "public_published",
            "state_published",
        }
        _require_exact_keys(journal, expected, "transaction_journal_invalid")
        staged = review_root / f".reveal-stage-{version}.yaml"
        public = review_root / "distributions" / version / "unblinding.yaml"
        if journal["state_published"]:
            _restore_state(state_path, previous_state)
        if journal["public_published"]:
            public.unlink(missing_ok=True)
        if journal["stage_written"]:
            staged.unlink(missing_ok=True)
    else:
        raise DirectSvgReviewError("transaction_journal_invalid")
    journal_path.unlink()
    return {"status": "rolled_back", "kind": kind, "version": version}


def stage_review(
    fixture_root: Path,
    *,
    review_root: Path,
    private_root: Path,
    generator_commit: str,
    generator_script_sha256: str | None = None,
    generator_receipt_sha256: str | None = None,
    private_seed: bytes | None = None,
    replay: bool = False,
    failure_injection: str | None = None,
    crash_injection: str | None = None,
) -> dict[str, Any]:
    """Build, byte-verify, and transactionally publish one immutable review version."""
    fixture_root = fixture_root.resolve()
    review_root = review_root.resolve()
    private_root = private_root.resolve()
    plugin_root = fixture_root.parents[1]
    if review_root == private_root or private_root.is_relative_to(review_root):
        raise DirectSvgReviewError("private_root_must_be_external")
    if not generator_commit:
        raise DirectSvgReviewError("generator_commit_required")
    generator = _generator_binding(
        plugin_root,
        generator_commit,
        generator_script_sha256,
        generator_receipt_sha256,
    )
    if not replay:
        _fail_if_responses_exist(review_root)
    if replay and private_seed is None:
        current_state = _load_yaml(
            review_root / "review-state.yaml", "review_state_invalid"
        )
        current_version = current_state.get("version")
        if not isinstance(current_version, str):
            raise DirectSvgReviewError("review_state_invalid")
        protected_key = _load_yaml(
            private_root / current_version / "key.yaml", "private_manifest_invalid"
        )
        if protected_key.get("schema") != PRIVATE_SCHEMA:
            raise DirectSvgReviewError("private_manifest_invalid")
        try:
            seed = bytes.fromhex(protected_key["seed_hex"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DirectSvgReviewError("private_seed_invalid") from exc
    else:
        seed = private_seed if private_seed is not None else secrets.token_bytes(32)
    if not isinstance(seed, bytes) or len(seed) < 32:
        raise DirectSvgReviewError("private_seed_invalid")

    review_root.mkdir(parents=True, exist_ok=True)
    private_root.mkdir(parents=True, exist_ok=True)
    os.chmod(private_root, 0o700)
    version, public_temp, private_temp, state = _build_staged_bundle(
        fixture_root, review_root, private_root, seed, generator
    )
    distribution_path = review_root / "distributions" / version
    private_path = private_root / version
    state_path = review_root / "review-state.yaml"
    expected_state_bytes = _yaml_bytes(state)
    try:
        if distribution_path.exists():
            if not replay:
                raise DirectSvgReviewError("review_version_exists")
            _compare_tree(public_temp, distribution_path)
            _compare_tree(private_temp, private_path)
            if not state_path.is_file() or state_path.read_bytes() != expected_state_bytes:
                raise DirectSvgReviewError("replay_byte_mismatch")
            return {
                "version": version,
                "distribution_path": distribution_path,
                "private_path": private_path,
                "public_manifest_sha256": _sha256(
                    distribution_path / "manifest.yaml"
                ),
            }
        if replay:
            raise DirectSvgReviewError("replay_version_missing")

        journal_path = review_root / ".publish-journal.yaml"
        if journal_path.exists():
            raise DirectSvgReviewError("publish_journal_exists")
        previous_state = state_path.read_bytes() if state_path.exists() else None
        journal = {
            "schema": "figure-agent.review-publication-journal.v1",
            "kind": "publication",
            "version": version,
            "previous_state_hex": (
                previous_state.hex() if previous_state is not None else None
            ),
            "private_published": False,
            "public_published": False,
            "state_published": False,
        }
        _atomic_yaml(journal_path, journal)
        try:
            _inject("before_publish", failure_injection, crash_injection)
            distribution_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(private_temp, private_path)
            journal["private_published"] = True
            _atomic_yaml(journal_path, journal)
            _inject("after_private_publish", failure_injection, crash_injection)
            os.replace(public_temp, distribution_path)
            journal["public_published"] = True
            _atomic_yaml(journal_path, journal)
            _inject("after_public_publish", failure_injection, crash_injection)
            _atomic_bytes(state_path, expected_state_bytes)
            journal["state_published"] = True
            _atomic_yaml(journal_path, journal)
            _inject("after_state_publish", failure_injection, crash_injection)
            journal_path.unlink()
        except Exception:
            if journal["state_published"]:
                _restore_state(state_path, previous_state)
            if journal["public_published"]:
                shutil.rmtree(distribution_path)
            if journal["private_published"]:
                shutil.rmtree(private_path)
            journal_path.unlink(missing_ok=True)
            raise
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


def _validate_reviewer(value: Any, *, required: bool) -> dict[str, Any]:
    reviewer = _require_exact_keys(value, {"name", "reviewed_at"}, "reviewer_invalid")
    values = (reviewer["name"], reviewer["reviewed_at"])
    if required and any(not isinstance(item, str) or not item.strip() for item in values):
        raise DirectSvgReviewError("named_reviewer_required")
    if required:
        try:
            reviewed_at = datetime.fromisoformat(reviewer["reviewed_at"])
        except ValueError as exc:
            raise DirectSvgReviewError("reviewed_at_invalid") from exc
        if reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
            raise DirectSvgReviewError("reviewed_at_invalid")
    if not required and any(item is not None for item in values):
        raise DirectSvgReviewError("reviewer_must_be_empty")
    return reviewer


def _validate_panels(
    value: Any,
    *,
    scientific_complete: bool,
    visual_complete: bool,
) -> dict[str, Any]:
    panels = _require_exact_keys(value, set(PANELS), "response_panels_invalid")
    for panel_value in panels.values():
        panel = _require_exact_keys(
            panel_value, {"scientific", "visual"}, "response_panel_invalid"
        )
        scientific = _require_exact_keys(
            panel["scientific"], set(LETTERS), "scientific_gate_invalid"
        )
        for option_value in scientific.values():
            option = _require_exact_keys(
                option_value, {"verdict", "evidence"}, "scientific_gate_invalid"
            )
            if scientific_complete:
                if option["verdict"] not in SCIENTIFIC_CHOICES:
                    raise DirectSvgReviewError("scientific_verdict_invalid")
                if not isinstance(option["evidence"], str) or not option["evidence"].strip():
                    raise DirectSvgReviewError("scientific_evidence_required")
            elif any(item is not None for item in option.values()):
                raise DirectSvgReviewError("scientific_gate_must_be_empty")
        visual = _require_exact_keys(
            panel["visual"], set(_visual_template()), "visual_scoring_invalid"
        )
        if visual_complete:
            if any(
                visual[field] not in VISUAL_CHOICES
                for field in (
                    "composition_preference",
                    "illustration_quality_preference",
                    "typography_preference",
                )
            ):
                raise DirectSvgReviewError("visual_scoring_invalid")
            if not isinstance(visual["borderline_or_disputed"], bool):
                raise DirectSvgReviewError("visual_scoring_invalid")
        elif any(item is not None for item in visual.values()):
            raise DirectSvgReviewError("visual_scores_before_scientific_gate")
    return panels


def _validate_response(response: dict[str, Any]) -> None:
    root = _require_exact_keys(
        response,
        {"schema", "state", "primary_review", "second_review"},
        "response_closed_schema_invalid",
    )
    if root["schema"] != RESPONSE_SCHEMA or root["state"] not in RESPONSE_STATES:
        raise DirectSvgReviewError("response_schema_invalid")
    state = root["state"]
    primary_scientific = state != "scientific_gate_pending"
    primary_visual = state in {
        "primary_visual_fixed",
        "second_scientific_fixed",
        "second_visual_fixed",
        "finalized",
    }
    second_scientific = state in {
        "second_scientific_fixed",
        "second_visual_fixed",
    }
    second_visual = state == "second_visual_fixed"
    primary = _require_exact_keys(
        root["primary_review"], {"reviewer", "panels"}, "primary_review_invalid"
    )
    _validate_reviewer(primary["reviewer"], required=primary_scientific)
    primary_panels = _validate_panels(
        primary["panels"],
        scientific_complete=primary_scientific,
        visual_complete=primary_visual,
    )
    borderline = (
        any(
            panel["visual"]["borderline_or_disputed"]
            for panel in primary_panels.values()
        )
        if primary_visual
        else False
    )
    second = _require_exact_keys(
        root["second_review"],
        {"required", "reviewer", "panels"},
        "second_review_invalid",
    )
    expected_required: bool | None = borderline if primary_visual else None
    if second["required"] is not expected_required and second["required"] != expected_required:
        raise DirectSvgReviewError("second_review_requirement_invalid")
    if state == "finalized" and borderline:
        second_scientific = True
        second_visual = True
    _validate_reviewer(second["reviewer"], required=second_scientific)
    _validate_panels(
        second["panels"],
        scientific_complete=second_scientific,
        visual_complete=second_visual,
    )
    if second_scientific:
        first_name = primary["reviewer"]["name"].strip().casefold()
        second_name = second["reviewer"]["name"].strip().casefold()
        if first_name == second_name:
            raise DirectSvgReviewError("second_reviewer_must_be_distinct")


def _transition_allowed(current: str, proposed: str, response: dict[str, Any]) -> bool:
    if current == "scientific_gate_pending":
        return proposed == "primary_scientific_fixed"
    if current == "primary_scientific_fixed":
        return proposed == "primary_visual_fixed"
    if current == "primary_visual_fixed":
        required = response["second_review"]["required"]
        return proposed == ("second_scientific_fixed" if required else "finalized")
    if current == "second_scientific_fixed":
        return proposed == "second_visual_fixed"
    if current == "second_visual_fixed":
        return proposed == "finalized"
    return False


def _without_state(response: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in response.items() if key != "state"}


def _fixed_fields_preserved(current: dict[str, Any], proposed: dict[str, Any]) -> bool:
    current_state = current["state"]
    if current_state == "scientific_gate_pending":
        return True
    if current_state == "primary_scientific_fixed":
        return (
            current["primary_review"]["reviewer"]
            == proposed["primary_review"]["reviewer"]
            and all(
                current["primary_review"]["panels"][panel]["scientific"]
                == proposed["primary_review"]["panels"][panel]["scientific"]
                for panel in PANELS
            )
        )
    if current_state == "primary_visual_fixed":
        return current["primary_review"] == proposed["primary_review"]
    if current_state == "second_scientific_fixed":
        return (
            current["primary_review"] == proposed["primary_review"]
            and current["second_review"]["required"]
            == proposed["second_review"]["required"]
            and current["second_review"]["reviewer"]
            == proposed["second_review"]["reviewer"]
            and all(
                current["second_review"]["panels"][panel]["scientific"]
                == proposed["second_review"]["panels"][panel]["scientific"]
                for panel in PANELS
            )
        )
    if current_state == "second_visual_fixed":
        return _without_state(current) == _without_state(proposed)
    return False


def advance_review_response(
    review_root: Path, private_root: Path, proposed: dict[str, Any]
) -> dict[str, Any]:
    """Advance exactly one response state while preserving already fixed fields."""
    review_root = review_root.resolve()
    private_root = private_root.resolve()
    state_path = review_root / "review-state.yaml"
    state = _load_yaml(state_path, "review_state_invalid")
    if state.get("schema") != STATE_SCHEMA or state.get("blinding_keys_revealed") is not False:
        raise DirectSvgReviewError("review_state_invalid")
    version = state.get("version")
    if not isinstance(version, str):
        raise DirectSvgReviewError("review_state_invalid")
    response_path = review_root / "distributions" / version / "response.yaml"
    current_bytes = response_path.read_bytes()
    if state.get("response_sha256") != _sha256_bytes(current_bytes):
        raise DirectSvgReviewError("response_hash_mismatch")
    current = _load_yaml(response_path, "response_invalid")
    _validate_response(current)
    proposed_state = proposed.get("state") if isinstance(proposed, dict) else None
    if proposed_state not in RESPONSE_STATES or not _transition_allowed(
        current["state"], proposed_state, proposed
    ):
        raise DirectSvgReviewError("review_transition_invalid")
    _validate_response(proposed)
    if not _fixed_fields_preserved(current, proposed):
        raise DirectSvgReviewError("fixed_review_fields_changed")
    proposed_bytes = _yaml_bytes(proposed)
    proposed_hash = _sha256_bytes(proposed_bytes)
    previous_state = state_path.read_bytes()
    previous_response = current_bytes
    final_path = private_root / version / "final-response.yaml"
    final_written = False
    try:
        if proposed["state"] == "finalized":
            if final_path.exists():
                raise DirectSvgReviewError("final_response_exists")
            _atomic_bytes(final_path, proposed_bytes, 0o600)
            final_written = True
            state["finalized_response_sha256"] = proposed_hash
        state["response_state"] = proposed["state"]
        state["response_sha256"] = proposed_hash
        _atomic_bytes(response_path, proposed_bytes)
        _atomic_yaml(state_path, state)
    except Exception:
        _atomic_bytes(response_path, previous_response)
        _atomic_bytes(state_path, previous_state)
        if final_written:
            final_path.unlink(missing_ok=True)
        raise
    return {
        "version": version,
        "response_state": proposed["state"],
        "response_sha256": proposed_hash,
    }


def reveal_blinding_keys(
    review_root: Path,
    private_root: Path,
    *,
    failure_injection: str | None = None,
    crash_injection: str | None = None,
) -> dict[str, Any]:
    """Release assignments only after the protected finalized response validates."""
    review_root = review_root.resolve()
    private_root = private_root.resolve()
    state_path = review_root / "review-state.yaml"
    state = _load_yaml(state_path, "review_state_invalid")
    version = state.get("version")
    public_path = review_root / "distributions" / str(version) / "unblinding.yaml"
    if state.get("blinding_keys_revealed") is True:
        if (
            public_path.is_file()
            and not public_path.is_symlink()
            and state.get("unblinding_sha256") == _sha256(public_path)
        ):
            return {"version": version, "unblinding_path": public_path}
        raise DirectSvgReviewError("revealed_state_inconsistent")
    if state.get("response_state") != "finalized":
        raise DirectSvgReviewError("response_not_finalized")
    response_path = review_root / "distributions" / version / "response.yaml"
    final_path = private_root / version / "final-response.yaml"
    expected = state.get("finalized_response_sha256")
    if (
        not response_path.is_file()
        or not final_path.is_file()
        or _sha256(response_path) != expected
        or _sha256(final_path) != expected
        or response_path.read_bytes() != final_path.read_bytes()
    ):
        raise DirectSvgReviewError("finalized_response_hash_mismatch")
    key = _load_yaml(private_root / version / "key.yaml", "private_manifest_invalid")
    if public_path.exists() or state.get("blinding_keys_revealed") is not False:
        raise DirectSvgReviewError("blinding_keys_already_revealed")
    release = {
        "schema": "figure-agent.three-way-review-unblinding.v1",
        "version": version,
        "panel_assignments": key.get("panel_assignments"),
        "finalized_response_sha256": expected,
        "publication_acceptance": "not_claimed",
    }
    journal_path = review_root / ".reveal-journal.yaml"
    if journal_path.exists() or (review_root / ".publish-journal.yaml").exists():
        raise DirectSvgReviewError("transaction_recovery_required")
    previous_state = state_path.read_bytes()
    staged_path = review_root / f".reveal-stage-{version}.yaml"
    journal = {
        "schema": "figure-agent.review-reveal-journal.v1",
        "kind": "reveal",
        "version": version,
        "previous_state_hex": previous_state.hex(),
        "stage_written": False,
        "public_published": False,
        "state_published": False,
    }
    _atomic_yaml(journal_path, journal)
    try:
        _atomic_yaml(staged_path, release)
        journal["stage_written"] = True
        _atomic_yaml(journal_path, journal)
        _inject("after_reveal_stage", failure_injection, crash_injection)
        os.replace(staged_path, public_path)
        journal["public_published"] = True
        _atomic_yaml(journal_path, journal)
        _inject("after_reveal_publish", failure_injection, crash_injection)
        state["blinding_keys_revealed"] = True
        state["state"] = "named_human_verdict_fixed_and_unblinded"
        state["unblinding_sha256"] = _sha256(public_path)
        _atomic_yaml(state_path, state)
        journal["state_published"] = True
        _atomic_yaml(journal_path, journal)
        _inject("after_reveal_state", failure_injection, crash_injection)
        journal_path.unlink()
    except Exception:
        if journal["state_published"]:
            _atomic_bytes(state_path, previous_state)
        if journal["public_published"]:
            public_path.unlink(missing_ok=True)
        if journal["stage_written"]:
            staged_path.unlink(missing_ok=True)
        journal_path.unlink(missing_ok=True)
        raise
    return {"version": version, "unblinding_path": public_path}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture_root", type=Path)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--generator-commit")
    parser.add_argument("--generator-script-sha256")
    parser.add_argument("--generator-receipt-sha256")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--export-to", type=Path)
    parser.add_argument("--advance-response", type=Path)
    parser.add_argument("--reveal", action="store_true")
    parser.add_argument("--recover", action="store_true")
    args = parser.parse_args()
    if args.recover:
        result = recover_review_transaction(args.review_root, args.private_root)
    elif args.advance_response:
        result = advance_review_response(
            args.review_root,
            args.private_root,
            _load_yaml(args.advance_response, "response_invalid"),
        )
    elif args.reveal:
        result = reveal_blinding_keys(args.review_root, args.private_root)
    else:
        if not args.generator_commit:
            parser.error("--generator-commit is required when staging or replaying")
        result = stage_review(
            args.fixture_root,
            review_root=args.review_root,
            private_root=args.private_root,
            generator_commit=args.generator_commit,
            generator_script_sha256=args.generator_script_sha256,
            generator_receipt_sha256=args.generator_receipt_sha256,
            replay=args.replay,
        )
        if args.export_to:
            export_public_distribution(
                Path(result["distribution_path"]),
                args.export_to,
                review_root=args.review_root,
                private_root=args.private_root,
            )
    print(json.dumps({key: str(value) for key, value in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
