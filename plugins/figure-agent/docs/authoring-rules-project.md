---
schema: figure-agent.authoring-rules.v1
fixture: polymer_paper_project
promotion_state: n1_hypotheses
rules:
  - id: polymer_paper_project.cantilever-vertical-clip-top
    category: instrument_standard
    rule: "Draw the polymer cantilever vertical: clip/clamp on top, polymer hangs down, deflection sideways toward a side electrode. Horizontal cantilever orientation is wrong for this lab and its experiments."
    source:
      kind: hand_patch_commit
      locator: "examples/fig3_floating_clip_protocol vertical re-draw (2026-06-20)"
      quote: "clip on TOP, polymer hangs down"
    transfer_policy: use_as_constraint
  - id: polymer_paper_project.trap-colour-shallow-blue-deep-red
    category: label_binding
    rule: "Shallow traps and shallow states are blue or teal; deep traps and deep states are red. Keep this colour mapping consistent across every figure."
    source:
      kind: hand_patch_commit
      locator: "examples/fig1_overview_v2_pair_001_vault/authoring_contract.md"
      quote: "Shallow traps are blue and deep traps are red across Panels C, F, and G"
    transfer_policy: use_as_constraint
  - id: polymer_paper_project.panel-header-and-label-clearance
    category: panel_layout
    rule: "Reserve a clear header band inside every panel for the panel letter and title. Keep body geometry and subtitles out of that band. Every label must clear other text, apparatus geometry, semantic paths, and the panel frame; use whitespace or a leader when direct placement does not fit. Do not solve clearance by forcing an equal-cell grid: composition remains author-selected."
    source:
      kind: iteration_comment
      locator: "Fig1 R5 prospective v2 adversarial review (2026-07-18)"
      quote: "아직 내가 굳이 안집어줘도 많을 정도로 완성도는 부족"
    transfer_policy: use_as_constraint
  - id: polymer_paper_project.ispd-keyence-manual-transfer
    category: instrument_standard
    rule: "For ISPD panels, depict a Keyence SK series induction-type, non-contact electrostatic voltmeter. Corona-charge the specimen first, then manually transfer the same specimen to the adjacent measurement station. Do not invent an automated motion stage, continuous scan, conveyor, or Kelvin probe. Preserve the confirmed series-level topology without inventing an exact model."
    source:
      kind: iteration_comment
      locator: "Fig1 Panel E human review (2026-07-19)"
      quote: "코로나 차지를 한 후에, 직접 옆에 있는, 저 측정 장비 쪽으로 옮기는거야 우리가 자동 모션 기계는 아니야 / 아까 너가 말한 시리즈는 맞아"
    transfer_policy: use_as_constraint
  - id: polymer_paper_project.ispd-two-terminal-corona-topology
    category: instrument_standard
    rule: "For this sulfur-polymer experiment, corona charging applies a high-voltage potential difference across the needle electrode and the opposing counter electrode through the supply's two terminals. Do not add a grid or a protective/earth ground symbol. Preserve the two-terminal circuit and manual specimen transfer, but do not invent an exact polarity or voltage unless paper-local experimental evidence declares it."
    source:
      kind: iteration_comment
      locator: "Fig1 Panel E human scientific correction (2026-07-20)"
      quote: "코로나 차지 할때, 접지를 안한거 같은데, 실 실험에서, 그냥 양단에 고전압을 거는 식으로 했지 / 그리드도 빼 그리도 우리 안썼어"
    transfer_policy: use_as_constraint
  - id: polymer_paper_project.ispd-grounded-backing-plate
    category: instrument_standard
    rule: "For corona-charged ISPD, place the specimen on a grounded backing plate in both the charging and non-contact measurement states. Attach the ground to the conductive backing plate, not the polymer film. When showing manual transfer, preserve this electrical role at both stations without implying that the instrument probe contacts the specimen."
    source:
      kind: iteration_comment
      locator: "examples/fig1_overview_v5f_art_direction_001_vault/briefing.md §13.6; Panel E physical-layout review (2026-07-20)"
      quote: "Substrate represents the conductive base required for ISPD charge-decay path. Ground attaches to substrate (not polymer)"
    transfer_policy: use_as_constraint
    lifecycle: superseded
    superseded_by: polymer_paper_project.ispd-two-terminal-corona-topology
    superseded_reason: Later human scientific review confirmed that the actual experiment used the high-voltage supply's two terminals without a grid or an earth-grounded backing topology.
---

# Project authoring rule catalog (polymer_paper_project)

Cross-figure conventions for the sulfur-polymer paper, inherited by EVERY figure's
authoring context pack. Distinct from the per-fixture `authoring-rules-pair001.md`
catalog: rules here are project-scope (not tied to one figure) and were distilled
from conventions that recur across figures — for example the vertical-cantilever
orientation, which an AI default-orientation bias kept re-violating on each new
figure because the convention was previously locked to the fig1 pilot catalog.

Add a rule here only when a convention is genuinely cross-figure and source-anchored
(an iteration comment, a critique adjudication, or a hand-patch commit).

New fixtures must annotate each panel region with a canonical `% Panel X` comment line
(matching `^\s*%\s*Panel\s+<id>`); the candidate loop maps a detector source_line to its
enclosing panel via these markers, and without them defect candidates are refused as
`unknown_panel`.
