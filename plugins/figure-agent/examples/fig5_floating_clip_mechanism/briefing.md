# Briefing — fig5_floating_clip_mechanism

> **Genre**: Mechanism schematic (paper Fig 5, panel a — mechanism subset).
> **Paper figure plan**: Fig 5 = "Actuation as probe (mechanism + stills + Δθ + t₅₀)" per planning/INDEX.md v9.7. This fixture covers the **mechanism schematic ONLY** (sub-panel A). Stills (photos) → `\includegraphics`; Δθ / t₅₀ data plots → matplotlib / Graph_making_hub (out of figure-agent scope per plugin CLAUDE.md).
> **Source planning**: planning/session_summary_260427_mechanism.md (Mechanism Framework Floating-Clip + Air Gap, F_clip = Q_clip × E_active, 7-Phase Pulsed Bias Protocol)
> **Paper framing (v9.7 LOCKED)**: charge-trap-centered, bending = macroscopic probe NOT showcase

---

## §1. Figure identity + 30-second message

**정체성**: Mechanism schematic for the floating-clip Coulomb probe — explaining HOW the macroscopic bending in Fig 1 G arises from charge dynamics. Cover-figure / methods-figure register.

**30-second message**: *"황 풍부 폴리머 cantilever에 grounded poling으로 Q_clip lock한 뒤 active electrode를 polarity reverse하면, locked Q_clip × E_active Coulomb 척력이 즉시 발생하고 intrinsic carrier redistribution이 τ_pol에 걸쳐 차폐하면서 인력으로 회귀한다."*

**5-second impression**:
- Panel A (top): 7-phase voltage waveform (A→G timeline) — pulse sequence semantic
- Panel B (bottom): geometry + force diagram (active electrode | air gap | floating clip with Q_clip | cantilever with trapped charges)

**Anti-goal**:
- Showcase-tone ("new actuation!"); 본 paper는 charge-trap-centered, NOT actuation discovery
- Detailed device drawing (Fig 1 G가 이미 cantilever-electrode geometry 전달); 본 figure는 **mechanism explanation** focus
- Quantitative force vector magnitudes (those belong in paper Methods / SI)

---

## §2. Per-panel ROLE

| Panel | Narrative role | Aesthetic register |
|---|---|---|
| A (top) | 7-phase voltage waveform timeline (A→G phases) — protocol identity | data-style timeline (axis frame + tick markers + phase shading) |
| B (bottom) | Geometry + force diagram — active electrode + floating clip + cantilever + trapped charges; force vector at one snapshot (Phase D = polarity reversed, max repulsion) | schematic scene (Fig 1 G와 같은 register이지만 더 detailed) |

---

## §3. Physics invariants (LOCKED, planning/session_260427 anchored)

3.1 **F_clip = Q_clip × E_active** (simple model, planning §1)
3.2 **Q_clip lock via Phase A grounded poling**: Q_clip = -C·V₀ where C = clip-ground capacitance, V₀ = poling voltage
3.3 **Phase B disconnect**: ground wire physically removed → Q_clip frozen (no carrier exchange with ground)
3.4 **Phase D polarity reversal**: V_active sign flips → Coulomb force sign flips immediately (no τ delay since electric field propagation is ~ps; Q_clip is locked so doesn't redistribute via ground)
3.5 **Phase E relaxation**: intrinsic mobile carriers (electrons or holes) drift in V_active field → redistribute to shield external field → effective E_active(in-film) decreases → Coulomb repulsion weakens → image attraction returns dominates
3.6 **Time-scale ordering** (fast → slow): V_active change (instant) > image charge in clip metal (~ps) > Q_clip via ground if grounded (~µs, blocked in Phase B+) > mobile carrier drift (~ms) > trap capture/detrap (~τ_d, Fig 1 F) > deep trap full relaxation (~hour)
3.7 **Maxwell attraction**: ALWAYS present (image charge between trapped charge and grounded electrode); not depicted in Fig 1 G to focus on novel Coulomb signature, but **must appear in Fig 5 mechanism schematic** as part of force competition
3.8 **No new injection in Phase B+**: floating clip means ground wire disconnect; Phase A's grounded poling is the only "injection" event; subsequent phases involve *redistribution* of locked charge only (planning §5 terminology lock)
3.9 **Trap loading** (Phase A also affects film traps): grounded poling Q charges both clip metal AND in-film trap sites (intrinsic mobile carriers captured by traps); trapped charge ≠ Q_clip but coupled to it (both contribute to net polarization)

---

## §4. Forbidden

- **Showcase tone words** ("first demonstration", "novel actuator", "device") — Fig 5 is mechanism explanation, paper framing is charge-trap-centered (planning §6)
- **Quantitative force vector magnitudes** (e.g., "1 mN" or "10 kV/m") — cartoon register; quantitative in paper Methods Eq.X / SI
- **Both-electrode connected geometry** (Watanabe 1999/2004 prior art) — explicitly contrasted; our geometry is floating-clip
- **Bidirectional / piezoelectric arrows** — anti-goal of charge-trap framing
- **Maxwell-only or Coulomb-only representation** — Fig 5 MUST show competition between two forces (Coulomb repulsion + image attraction); Fig 1 G simplifies to Coulomb-only for novel-signature focus, but Fig 5 is mechanism focus → show both

---

## §5. Per-panel ROLE detail

### Panel A — 7-phase voltage waveform

- **Axis**: V_active (y-axis, ± V₀) vs time t (x-axis, with phase labels A, B, C, D, E, F, G)
- **Levels**: 3 distinct levels — `+V₀` (Phase A, G), `0` (Phase C, F), `-V₀` (Phase D, E); transitions sharp (square-wave style)
- **Phase shading**: light vertical bands behind each phase to mark boundaries (cAmber!8 tint similar to Fig 1 Row 2 wash)
- **Phase labels**: small italic letters A through G centered in each phase band
- **Clip status annotation** (top of axis): "GROUNDED" during Phase A only; "FLOATING" during Phase B onwards (sub-text or color band)
- **Key event arrows**: small ↓ markers at "Phase A end" (Q_clip lock) and "Phase D start" (polarity flip — sign of mechanism signature)

### Panel B — Geometry + force diagram (Phase D snapshot)

- **Active electrode** (LEFT side, opposite of Fig 1 G): tall rectangle, grounded symbol below, label "active electrode (−V₀)" at Phase D
- **Air gap** (center): explicit dimension arrow with "d_air" label
- **Cantilever** (RIGHT side): polymer strip hanging from clip at top, bending LEFT toward active electrode (Phase D: attractive Maxwell + repulsive Coulomb compete; the cartoon shows NET = repulsion bend, AWAY from active electrode)
  - Actually flipping convention from Fig 1 G — here the BEND direction depends on phase
  - At Phase D (polarity reversed, locked Q_clip same sign as new V_active polarity): Coulomb repulsion dominates → cantilever bends AWAY from active electrode (i.e., to the RIGHT in this layout)
- **Floating clip** at cantilever tip (or top? — choose tip-clip for visual clarity): small gray block with "Q_clip (−)" label (sign matches Phase A grounded poling result)
- **Trapped charges** (3 ●, inside polymer body): polarity-neutral filled dots (per Fig 1 v8 convention)
- **Force vectors at clip**:
  - **F_Coulomb** (red, →): repulsive Q_clip × E_active force pushing clip AWAY from active electrode (Phase D scenario)
  - **F_Maxwell / F_image** (cRed!50, dashed, ←): image-charge attractive force toward active electrode (always present, competes with Coulomb)
  - Both vectors at same point (clip), opposite directions, magnitudes shown by arrow lengths
- **Net bending arrow**: thick gray arrow on cantilever indicating net direction (= dominant force direction at this phase)

---

## §6. Visual story arc

| Frame | Element | Dwell | Purpose |
|---|---|---|---|
| 1 | Panel A: scan phase timeline left→right | 3s | Pulse protocol identity (A grounded poling, then disconnect, then polarity ops) |
| 2 | Panel A → Panel B transition (Phase D zoom-in) | 0.5s | "Focus on the moment of mechanism" |
| 3 | Panel B: active electrode → air gap → cantilever | 2s | Geometry identity |
| 4 | Panel B: locked Q_clip + force vectors | 3s | Mechanism core — Coulomb vs image-attraction competition |
| 5 | Panel B: net bending direction | 1s | Macroscopic outcome |

Total ~10s.

---

## §7. Implementation status

**Current**: scaffold only — briefing.md + spec.yaml + skeleton .tex (this commit).
**Next**: Panel A waveform + Panel B geometry; iteration plan once skeleton compiles.

---

## §8. Cross-reference

- **Fig 1 G**: same geometry idiom (cantilever + electrode + air gap + q_tr markers); Fig 5 B extends this with active electrode + force vectors + Phase D snapshot
- **Fig 3**: time-constant τ_d (ISPD) provides quantitative anchor for Phase E relaxation rate
- **Paper Methods §M.x**: 7-phase protocol full specification + F_clip equation derivation
- **Paper SI Methods S0**: 4-식 framework (CvS / ISPD / Shallow+Deep DOS / Coulomb-Maxwell competition)
- **Hirai prior art Mechanism Contrast** (references.md Section 3.5): connected-electrode geometries fail Signature A (OFF charge ZERO) and Signature B (polarity-independent or delayed bending); our floating-clip protocol passes both
