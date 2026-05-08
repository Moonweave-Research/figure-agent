# Gemini review — architecture-v0.4.1-build-perception-pack.md

**Date:** 2026-05-08
**Reviewer:** Gemini 3.1 Pro Preview
**Spec under review:** `docs/architecture-v0.4.1-build-perception-pack.md`
**Verdict:** needs further revision
**Round:** 2nd (v0.4 was reviewed earlier same day)

---

### 1. RESOLUTION VERIFICATION — Topology FP on macro endpoints (Gemini #3)
**Severity: BLOCKING**
The spec claims in §8 that the `\dibRing` false-positive problem (Gemini #3) is resolved by "path reconstruction" (§4.2). This resolution does not hold. Gemini #3 correctly pointed out that the polysulfide chains attach to the *middle* of the DIB ring's closed path (a T-junction), not its 0-degree start/end point. Because the distance from the chain's attachment point to the ring's endpoint is ~0.81 cm, the endpoint-to-endpoint distance is far greater than the `0.20 cm` threshold. Path reconstruction (§4.2) merely merges sequential segments of the *same* chain; it does not compute endpoint-to-stroke intersections. Thus, the algorithm will still falsely flag the valid starting points of all 6 chains as lonely. The mathematical foundation of the topology algorithm remains broken for attached components.

### 2. NEW ALGORITHM CLAIMS — Path reconstruction guarantees false negatives
**Severity: BLOCKING**
The spec claims (§4.2) that external lonely endpoints will catch the dangling chain termini, but masks the empirical result as "TBD in MVP trial" (§7.1). The Codex review already explicitly verified that two faded chain tails terminate within ~0.12-0.19 cm of *each other*. Because they are different chains, path reconstruction will not merge them. Consequently, the Stage 1 topology clustering will group these two external endpoints into a single cluster of size 2. Because `lonely` strictly requires `cluster size = 1` (§4.2), these two dangling chains will NOT be flagged. Shipping a known algorithmic failure into an MVP trial is unacceptable.

### 3. COORDINATE MAPPING — Scaling math is completely hallucinated
**Severity: BLOCKING**
The spec §4.1 declares `cm_per_source_unit: 1.291` and `source_origin_in_pdf_cm: [0.27, 0.27]`. This is mathematically wrong. The PDF page is 18.08 cm wide because it contains 17.8 cm of scaled content (`178mm`) plus a `4pt` border on each side (`4 * 2.54 / 72 = 0.141 cm`, making total width `17.8 + 0.282 = 18.082 cm`).
- The correct `cm_per_source_unit` is the scaled content width divided by the source canvas width: `17.8 / 14.0 = 1.271`. The spec incorrectly divided the *entire page width* (18.08) by 14.0, yielding 1.291. This ~1.5% scaling error translates to >0.21 cm drift across the canvas, entirely breaking the `ε=0.20 cm` clustering threshold.
- The correct `source_origin_in_pdf_cm` should be the border padding: `[0.141, 0.141]`. The spec's `[0.27, 0.27]` is wrong.
Any bounding boxes or coordinate hints relying on these hallucinated scaling factors will completely miss their intended PDF targets.

### 4. INTENT-GATING SOUNDNESS — Manual BBox computation is a severe burden
**Severity: BLOCKING**
The spec introduces `bbox_pdf_cm` as a manual authoring step (§5.1), claiming it takes "~5-10 min one-time" and is a "small author burden." This is a gross underestimate. The user authors in TikZ coordinates (e.g., 14×9 canvas). Forcing the user to manually compute PDF cm coordinates requires them to reverse-engineer LaTeX's `\resizebox` and border padding scaling math, which even the spec author failed to do correctly (see Issue #3). Additionally, the spec strictly enforces a single scalar string `intent_type: network` per panel (§5.1), providing no mechanism for mixed-intent panels (e.g., a process diagram that includes a network inset), which will cause silent fallback or false positives.

### 5. SCOPE DOWNSCOPE — Orphaned style logic in report
**Severity: NON-BLOCKING**
The MVP downscope correctly defers `wireframe.png` and `edge.png`, recognizing that `overlay.png` alone answers the chain-connectivity question without the 4-6 s render penalty. However, §3.2 cuts `style.yaml`, while §4.4's report still claims to output "Color count: 8 actual vs 6 declared." The logic to compare actual extracted colors against the declared styles has been orphaned. The implementation plan must ensure this logic is migrated to `topology.yaml` or explicitly dropped.

### 6. PROBE INTEGRITY — Endpoint math discrepancy
**Severity: NON-BLOCKING**
The spec §7.1 cites 176 path segments (46 lines + 120 curves + 10 rects) and 332 endpoints. If each segment has 2 endpoints, 176 segments should yield 352 endpoints. The discrepancy (332 vs 352) implies either closed loops (rects) sharing endpoints or an undocumented pdfplumber merging step. While minor, the translation of PDF primitives into segment endpoints must be documented before implementation.

### 7. INTEGRATION REFACTOR — Safe `critique_brief.py` refactor
**Severity: NON-BLOCKING**
The spec §6.2 mandates refactoring `critique_brief.py:generate_for()` from a single multi-line f-string into a list of joined sections. A review of `scripts/critique_brief.py` and `tests/test_critique_brief.py` confirms that the tests assert substring presence (e.g., `"### A. Physics correctness" in brief`) rather than exact line-by-line matches. The refactor is structurally safe and will not break existing contracts if the `\n\n` joins are handled cleanly.

---

**Verdict: Needs further revision.**
While the dependency swap to `pdfplumber` (MIT) and the MVP downscope to four core outputs are massive improvements, the core mathematical logic is fatally flawed. The path reconstruction algorithm fails to account for T-junction intersections (guaranteeing false positives) and fails to catch clustered dangling chains (guaranteeing false negatives). Furthermore, the hallucinated `1.291` scale factor proves that shifting the burden of PDF cm coordinate calculation to the user is an unreasonable and highly error-prone UX decision. The spec must solve the endpoint-to-stroke intersection math and provide an automated coordinate mapping mechanism before moving to implementation.
