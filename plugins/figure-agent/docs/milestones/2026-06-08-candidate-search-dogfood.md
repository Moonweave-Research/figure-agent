# Candidate Search Dogfood - 2026-06-08

## Scope

Synthetic fixture dogfood for the reference-aware candidate-search vertical
slice. This verifies the public CLI workflow only; it does not mutate real
manuscript fixtures and does not claim autonomous art-direction quality.

## Fixture

Created a temp workspace fixture:

```text
examples/candidate_demo/spec.yaml
examples/candidate_demo/briefing.md
examples/candidate_demo/candidate_demo.tex
```

The source contained one simple TikZ node:

```tex
\node (label-a) at (0,0) {Old Label};
```

## Commands

Run from the repository root with:

```bash
FIGURE_AGENT_PLUGIN_ROOT=$PWD/plugins/figure-agent
FIGURE_AGENT_WORKSPACE=<tmp>/workspace
plugins/figure-agent/bin/fig-agent intent candidate_demo --json
plugins/figure-agent/bin/fig-agent candidates candidate_demo --json --output build/candidates/candidate_set.json
plugins/figure-agent/bin/fig-agent render-candidates candidate_demo --candidate-set build/candidates/candidate_set.json
plugins/figure-agent/bin/fig-agent rank-candidates candidate_demo --candidate-set build/candidates/candidate_set.json --json
plugins/figure-agent/bin/fig-agent review-candidate candidate_demo CAND001 --json
```

## Result

All commands exited 0.

Observed schemas:

```text
intent      figure-agent.intent-model.v1
candidates  figure-agent.candidate-set.v1
render      figure-agent.candidate-render-result.v1
rank        figure-agent.candidate-rank-result.v1
review      figure-agent.candidate-review-packet.v1
```

The render step created only fixture-local candidate evidence:

```text
build/candidates/candidate_set.json
build/candidates/CAND001/candidate_demo.tex
build/candidates/CAND001/candidate_manifest.json
```

The rank result emitted `effective_apply_authority=review_only`, which is the
expected conservative state for this minimal fixture. The candidate can be
reviewed, but source mutation remains gated.

## Release Gate Evidence

Focused release gate was run with Python 3.14 pinned so `uv run` used the same
host dependency ABI as the installed plugin runtime:

```bash
UV_PYTHON=$(python3 -c 'import sys; print(sys.executable)') \
PYTHONPATH=/opt/homebrew/lib/python3.14/site-packages:/Users/choemun-yeong/Library/Python/3.14/lib/python/site-packages \
python3 plugins/figure-agent/scripts/release_gate.py --output plugins/figure-agent/dist/cowork --json --skip-full-pytest --skip-claude-validate
```

Result:

```text
success: true
targeted_tests: 142 passed
ruff: passed
package_required_paths: passed
package_excluded_paths: passed
package_audit: passed
package_size_mib: 2.181
claude_validate_package: skipped explicitly
claude_validate_marketplace: skipped explicitly
```

## Boundary Notes

- This is a search-layer upgrade, not a taste oracle.
- MCP exposes read-only candidate tools and refuses MCP-side apply.
- Candidate rendering writes sandbox evidence only under
  `examples/<name>/build/candidates/`.
- Real manuscript fixture promotion still requires human review and accepted /
  golden boundary preservation.
