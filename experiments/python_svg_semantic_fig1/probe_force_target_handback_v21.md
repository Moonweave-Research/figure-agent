# Fig1 Probe Force Target Handback v21

## Scope

This pass follows `probe_force_target_options_v21.md` and locks the Fig1 macroscopic probe force target as `cantilever`. It is a semantic contract migration, not a general visual polish pass.

## Implemented Boundary

- No new scaffold was created.
- No origin, hero, electrical evidence, or interpretation panel polish was included.
- No component reference registry was introduced.
- The reference PNG remains layout/style evidence only, not ground_truth.
- The causal diagram remains semantic/narrative evidence only.
- The renderer still uses drawsvg as the SVG compositor.
- The legacy dirty files `src/fig1_scene.py` and `src/semantic_scene.py` were not touched by this pass.
- Human visual review remains required before publication-grade approval.

## Visible / Semantic Changes

- `ForceArrow.force_target` was added with a compatibility default for non-Fig1 probes.
- The Fig1 `repulsion_arrow` now uses `force_target="cantilever"`.
- The red Coulomb force arrow now points leftward, away from the right-side `+ V` electrode.
- The probe force label now reads `Force on cantilever`.
- The probe conclusion copy now states that like-charge repulsion drives the cantilever away from `+V`.
- SVG metadata now uses `force_target=cantilever` and `arrow_direction=cantilever_leftward_repulsion`.

## Gate Changes

- `verify_fig1_semantics.py` now rejects the old rightward reference arrow contract.
- `verify_fig1_physics_sanity.py` now checks probe geometry: charge/electrode separation, force-arrow start proximity, force endpoints inside the probe frame, and bend-state consistency.
- `src/test_fig1_physics_sanity.py` includes v21 mutation tests for rightward cantilever force vectors, charge/electrode overlap, force-start drift, and bend-state drift.

## Hash Record

- previous hash: `55702be313ca70192560a569c8d45949b575e5bfa960252acd9e72f7294e230a`
- new hash: `0ceca15c136d21cb73676dcd91fb9a50aec54e41e05cd2b541dba0caef3b8edf`

## Next Direction

The next visual pass can evaluate whether the leftward force arrow still reads well against the reference-like probe panel composition. That review is human visual review territory; v21 only locks the physical target and vector contract.
