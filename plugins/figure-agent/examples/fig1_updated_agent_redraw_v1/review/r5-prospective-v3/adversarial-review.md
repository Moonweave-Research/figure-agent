# R5 prospective v3 adversarial review

The source passed Style Lock lint and compiled without the v2 asset-import and
numeric-anchor failures. Strict review nevertheless failed. This is an improved
failure, not an accepted figure.

## Detected blockers

The text-collision detector reported six overlaps, concentrated in the D header
and the E apparatus labels. Strict status is `failed`.

## Additional definite visual defects missed by the current detectors

- In F, the `Coulomb repulsion` and `floating polymer cantilever` annotations
  compete with the force arrow and each other.
- The F bottom floating-state sentence is compressed against the panel frame.
- The E apparatus labels remain crowded even where pairwise word IoU stays below
  the current collision threshold.

## Product attribution and next boundary

The exact asset import, vertical cantilever rule, malformed-coordinate blocker,
and author-selected composition all behaved as intended. The remaining systemic
gap is panel-local visual reasoning for a free composition: the current rendered
detectors do not reliably infer each generated panel frame, reserve its header
band, or evaluate text/path/frame clearance within that local coordinate system.

The next slice should discover panel frames from source/render geometry and bind
text plus semantic paths to those frames before proposing a repair. It must not
restore a fixed 2 by 3 layout. Machine checks remain distinct from publication
acceptance.
