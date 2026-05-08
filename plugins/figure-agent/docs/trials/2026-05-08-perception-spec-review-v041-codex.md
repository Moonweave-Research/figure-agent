# Codex review — architecture-v0.4.1-build-perception-pack.md

**Date:** 2026-05-08
**Reviewer:** Codex (gpt-5.1)
**Spec under review:** `docs/architecture-v0.4.1-build-perception-pack.md`
**Verdict:** needs further revision before implementation plan
**Round:** 2nd (v0.4 was reviewed earlier same day; reviews at `2026-05-08-perception-spec-review-codex.md` / `..-gemini.md`)

---

I audited every §8 row. Text-only fixes mostly hold for the PyMuPDF API/schema correction and the orthogonality framing, but the implementation-critical rows do not hold.

**1. BLOCKING — Topology fix does not resolve macro endpoint false positives**
v0.4.1 claims Gemini #3 is fixed by path reconstruction before lonely detection (v0.4.1 §6.2 / algorithm §4.2). The prior Gemini issue was not just split chains; it was endpoint-to-endpoint topology falsely flagging chains that attach to the middle of a closed DIB ring path (Gemini v0.4 review). The TeX still has `\dibRing` as a closed cycle and chains attached by separate draws (`fig1_overview_v2.tex:59` / chain macro at `:73`). Path reconstruction merges linker/solid/faded chain segments, but it does not add endpoint-to-path distance against ring edges. So the ring-side "external endpoints" remain likely false positives.

**2. BLOCKING — Path reconstruction is underspecified despite working for solid/faded joins**
I verified the rendered PDF does preserve solid→faded tail continuity: the relevant curve joins match within about 0.0005-0.0013 cm, so rotated scopes are not the failure mode. The failure is that v0.4.1 admits pdfplumber gives flat `page.lines`, `page.curves`, `page.rects` with no drawing grouping (v0.4.1 §3.1), then says "group sequential segments" (pipeline §4.2). In the actual PDF, linkers are `page.lines` and waves are `page.curves`; there is no defined global sequence across those collections. The spec needs explicit reconstruction rules: same stroke/color/linewidth, endpoint matching, branch handling, object ordering fallback, and endpoint-to-path attachment.

**3. BLOCKING — pdfplumber probe baseline does not reproduce under the spec's own endpoint schema**
Raw object counts reproduce exactly: pdfplumber 0.11.9 reports 46 lines, 120 curves, 10 rects, 277 chars, and 332 line/curve endpoints, matching §7.1. But using `pts` first/last as the spec's curve payload requires (schema §3.1), I get 49 endpoints lonely at ε=0.20 cm, not 81. The 81-ish number appears tied to using bbox fields or mixed coordinate conventions, not true curve endpoints. That breaks the proposed regression criterion (§7.1 claim).

**4. BLOCKING — Coordinate mapping remains internally inconsistent**
The page size values are correct, but the mapping is not. `\resizebox{178mm}{!}` over a 14 cm source width implies 1.271 cm/source-cm, not `cm_per_source_unit: 1.291` (v0.4.1 §4.1; TeX source at line 19). The stated Panel A bbox `[0.27, 6.55, 4.66, 11.08]` also contradicts the declared top-left, y-down convention (bbox §4.2 / normalization §6). Top-row Panel A should not live at y=6.55..11.08 in top-left PDF cm coordinates.

**5. BLOCKING — Intent gating is not yet a runnable contract**
The enum includes `network`, `plot`, `process`, `composite`, `other` (§4.2), but the external YAML schema only defines `network` and `plot` rules (§5.3). Mixed panels are not addressed. The "5-10 min" burden is also understated because current `fig1_overview_v2/spec.yaml` has no `panels` list at all, and manual `bbox_pdf_cm` authoring depends on the unresolved coordinate mapping.

**6. BLOCKING — Dependency resolution fixed license but not required/optional contract**
The PyMuPDF AGPL issue is fixed textually by switching to pdfplumber (§3.1). But §8 says no graceful skip is needed because pdfplumber is required (resolution map), while §7.4 says missing pdfplumber should gracefully WARN and continue (anti-case). In the repo, pdfplumber is only in the dev dependency group, not runtime dependencies (`pyproject.toml:27`). The dependency policy is still unresolved.

**7. NON-BLOCKING — Scope downscope is directionally right but text leaks deferred features back into MVP**
Cutting to `extract.yaml`, `topology.yaml`, `overlay.png`, `report.md` is a real improvement (§2). For the narrow Panel A topology question, overlay plus topology is enough. But §2 still lists color count, font hierarchy, baseline groups, and density as T1 coverage (tier table), and the report example still includes color count and per-panel density. That partially reintroduces deferred `style.yaml` / `alignment.yaml` work.

**8. NON-BLOCKING — critique_brief refactor is feasible, but §8 overstates the fix**
The actual `generate_for()` is a single f-string return (`scripts/critique_brief.py:139`), so v0.4.1's sectioned refactor is a plausible implementation direction (§6.2). Existing tests pass: `uv run pytest tests/test_critique_brief.py -q` → 11 passed. But the prior issue also asked how perception pack freshness, partial generation, and missing YAML/PNG files are validated; current freshness logic only checks PNG/source inputs (`scripts/critique_brief.py:51`). That belongs in the implementation plan before calling the row fully resolved.

---

**Overall verdict:** needs further revision before implementation plan. The direction is salvageable, but §8 currently marks several unresolved implementation risks as fixed. The next revision should replace endpoint-only topology with endpoint-to-path-aware reconstruction, correct the pdfplumber probe baseline using real `pts`, define one coordinate convention with reproducible scale/origin math, and make `intent_rules.yaml` plus dependency policy executable rather than descriptive.
