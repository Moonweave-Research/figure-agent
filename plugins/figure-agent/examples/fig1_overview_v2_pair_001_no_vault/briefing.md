# Briefing — fig1_overview_v2_pair_001_no_vault

> **Pilot pair**: `fig1_overview_v2_pair_001` / **Arm**: no_vault
> **Design snapshot SHA**: `fa7a6d9ff7890a440ca3471995acf8145c47001a996dbd8bf2c428b363d8f7b7`
> **Authoring constraint**: same design.md snapshot as the vault arm; no tikz-vault references consulted.

## 1. Same target, design-only authoring

This arm targets the fig1_overview_v2 design at the v2.2 (chemistry-accuracy)
snapshot — same 2-row 7-panel layout, same v9.7+α charge-trap-centered framing.
Authoring is from design.md and the reference PNG only; no tikz-vault query,
no record metadata, no grammar/style anchors from a reference pool.

Authoring effort budget: one-pass write, partial scope (Panel A + Panel C
substantive; B/D/E/F/G scaffold-level). Same effort budget as the vault arm so
that the pair measures vault-grounding impact, not author-time differential.

## 2. What this figure shows

논문 전체 논리를 상→하 두 row로 압축. Row 1 (재료 → 구조 → trap 발생): Sulfur-rich
network → S-chain length 분포 → localized traps. Row 2 (3 lines of evidence
수렴): kinetic I(t)~t⁻ⁿ → ISPD Vₛ(t)→g(Eₜ) (paired transformation) → macroscopic
Coulomb probe.

Row 1 → Row 2: Panel C 하단에서 vertical Stealth arrow + label *"convergent
evidence"* (design.md §2.2 + §5).

스토리: *"황 풍부 폴리머에는 깊은 전하 트랩이 존재 → 다중 측정이 수렴 → 거시적 bending으로 발현."*

## 3. Physics invariants (from design.md §6 + §10 Q&A)

- Color convention (Q1): **shallow = blue, deep = red.**
- Panel C spatial map (Q2 + §2.3 정정): **left = shallow blue, right = deep red.**
  Asymmetry markers: deep has 4 wells > shallow's 3 wells, with 1–2 escape-up
  dashed arrows on the deep side.
- Panel C must be color-consistent with Panel F (g(Eₜ) bimodal: blue Shallow
  left, red Deep right; deep peak 1.8× shallow per Q4).
- Power-law I(t) ~ t⁻ⁿ lies ABOVE Debye reference at long times.
- Panel G: **Coulomb arrow only** (red, polymer → away from electrode).
  Maxwell attraction arrow is **forbidden** per §2.3 정정 사항 row 2 + §4 Panel G
  Forbidden list. Cantilever clip on TOP, polymer hanging down (§2.3 row 1).

## 4. Layout — 2-row, 7-panel

Canvas 14 cm × 9 cm → `\resizebox{178mm}{!}` to NatComm 178 mm.
Row 1 (y=5..9): A (x=0..3.50) | B (x=3.55..6.85) | C HERO (x=6.90..13.95).
Inter-row gap (y=4.50..5.00): vertical Stealth arrow + "convergent evidence".
Row 2 (y=0.1..4.45): D (x=0..4.45) | E (x=4.50..6.95) | F (x=7..10.45) | G (x=10.5..13.95).

## 5. Per-panel implementation status (partial scope, equal to vault arm)

- **Panel A** — IMPLEMENTED. 2-DIB benzene rings + polysulfide bridge chain
  (bezier curve per design §4 Panel A Render approach — *"Polysulfide chain →
  bezier curve, NOT sine 함수"*). S₈ corner inset as manual octagon (§4 Render
  approach: *"S₈ → manual octagon"*). Optional dashed inverse-vulcanization
  arrow from S₈ to DIB area.
- **Panel C** — IMPLEMENTED (HERO #1). Asymmetric energy landscape per §4:
  left = shallow blue (3 wells, 3 ⊖ electrons), right = deep red (4 wells, 4 ⊖
  electrons, 1–2 escape-up dashed arrows). Faded polymer-network backdrop.
- **Panel B, D, E, F, G** — scaffold-level (titles + motif outlines only).

Inter-panel arrows (A→B, B→C, D→E, E↔F, F→G): standard horizontal Stealth gray.
C → Row 2: thick vertical Stealth + "convergent evidence" (§5).

## 6. Author intent recap

This arm is the no-grounding baseline of the pair. Authoring follows design.md
v2.2 verbatim — including all §2.3 정정 사항 (color swap, Maxwell removal,
cantilever clip-up, hero hierarchy via well-count + saturation). Design.md is
not a vault artifact; it is the same document the vault arm author also reads.
The pair therefore controls for design correctness and measures only the effect
of vault-grounded grammar/style anchor awareness.
