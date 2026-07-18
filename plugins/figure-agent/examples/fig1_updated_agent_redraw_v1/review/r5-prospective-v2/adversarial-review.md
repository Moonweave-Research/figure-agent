# R5 prospective v2 adversarial review

This run tests composition freedom and delivery of Figure Agent rules; it is not
a publication candidate. The diagnostic PNG exists only because LuaLaTeX emitted
a page despite source errors. Strict compilation did not pass.

## What improved

- Neither A nor B defaulted to an equal 2 by 3 grid. Both made Panel C the large
  visual hero, directly showing that the v1 grid was prompt-imposed rather than
  an optimized model choice.
- Both conditions drew the cantilever vertically from a top mechanical support.
- B used the reviewed Panel F motif and the paper palette, font hierarchy, and
  minimum stroke discipline instead of inventing local replacements.

## Definite blockers in B

- The source contains malformed sulfur-chain coordinate tokens such as `(s0.78)`;
  the A-panel bonds therefore do not compile correctly.
- D title and subtitle collide.
- E instrument/component labels collide with each other and with apparatus.
- F title competes with the top mechanical support.
- The Coulomb-repulsion annotation collides with the cantilever annotation and
  its semantic path.
- Bottom electrical-state text sits too close to the panel boundary.

## System attribution

- The earlier horizontal cantilever was a delivery failure: the project rule
  existed in the context pack but was omitted from the bound authoring prompt.
  Commit `92874ff5` repairs that connection.
- The first B compile failure was an asset-interface failure: the catalog named
  a repository path but did not state the TeX import path expected by
  `compile.sh`. Commit `57008597` adds an exact import directive for future runs.
- The malformed coordinates and visible text collisions remain authoring and
  preflight gaps. They are evidence for the next product slice, not permission
  to manually polish this immutable attempt.

Machine gates are not publication acceptance. C repair remains unadmitted until
B is machine-valid and a named human authorizes the bounded repair child.
