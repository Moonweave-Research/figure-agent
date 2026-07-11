from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from direct_svg_stage_review import stage_review
from PIL import Image

FIXTURE = Path(__file__).parents[1] / "examples" / "fig1_direct_svg_cleanroom_baseline"
FORBIDDEN_PUBLIC_TERMS = {
    "test-a",
    "test-b",
    "reconstruction",
    "synthesis",
    "comparator",
    "candidate",
    "direct-svg",
    "tikz",
    "source paths",
    "private key",
    "assignment",
    "seed",
}


def test_stage_review_creates_two_level_blinded_public_packets(tmp_path: Path) -> None:
    review_root = tmp_path / "review"
    state_path = review_root / "review-state.yaml"

    result = stage_review(
        FIXTURE,
        review_root=review_root,
        review_state_path=state_path,
        private_seed=bytes.fromhex("11" * 32),
    )

    assert set(result["public_manifest"]["experiments"]) == {"R1", "R2"}
    for experiment in ("R1", "R2"):
        for panel in ("C", "F"):
            directory = review_root / "public" / experiment / panel
            assert {"option-a.png", "option-b.png", "public-review-manifest.yaml"}.issubset(
                {path.name for path in directory.iterdir()}
            )
            assert Image.open(directory / "option-a.png").size == Image.open(
                directory / "option-b.png"
            ).size
    assert (review_root / "public" / "index.html").is_file()
    assert (review_root / "private" / "private-review-manifest.yaml").is_file()
    assert not list((review_root / "public").rglob("*private*"))

    option_hashes_by_panel = {panel: [] for panel in ("C", "F")}
    file_hashes_by_panel = {panel: [] for panel in ("C", "F")}
    for experiment in ("R1", "R2"):
        for panel in ("C", "F"):
            manifest = yaml.safe_load(
                (
                    review_root
                    / "public"
                    / experiment
                    / panel
                    / "public-review-manifest.yaml"
                ).read_text(encoding="utf-8")
            )
            option_hashes_by_panel[panel].extend(
                item["sha256"] for item in manifest["options"].values()
            )
            file_hashes_by_panel[panel].extend(
                hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (review_root / "public" / experiment / panel).glob(
                    "option-?.png"
                )
            )
    assert all(len(values) == len(set(values)) for values in option_hashes_by_panel.values())
    assert all(len(values) == len(set(values)) for values in file_hashes_by_panel.values())

    public_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (review_root / "public").rglob("*")
        if path.suffix in {".html", ".yaml"}
    ).lower()
    leaked_terms = {term for term in FORBIDDEN_PUBLIC_TERMS if term in public_text}
    assert not leaked_terms
    for required in (
        "scientific fidelity",
        "composition preference",
        "illustration quality preference",
        "typography preference",
        "borderline/disputed",
        "named reviewer",
        "reviewed_at",
    ):
        assert required in public_text

    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert state["state"] == "awaiting_named_human_verdict"
    assert state["cold_reproductions"] == 0
    assert state["publication_acceptance"] == "not_claimed"
    assert state["public_manifest_sha256"].startswith("sha256:")
    assert state["private_manifest_sha256"].startswith("sha256:")


def test_stage_review_hashes_are_deterministic_for_fixed_private_seed(
    tmp_path: Path,
) -> None:
    results = []
    for name in ("one", "two"):
        root = tmp_path / name
        results.append(
            stage_review(
                FIXTURE,
                review_root=root,
                review_state_path=root / "review-state.yaml",
                private_seed=bytes.fromhex("22" * 32),
            )
        )

    comparable = [
        {
            "public_manifest": result["public_manifest"],
            "public_manifest_sha256": result["review_state"]["public_manifest_sha256"],
        }
        for result in results
    ]
    assert json.dumps(comparable[0], sort_keys=True) == json.dumps(comparable[1], sort_keys=True)
