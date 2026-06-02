# Issue 100CM - Marketplace Source Hygiene Guard

Status: implemented
Type: operator UX, plugin install freshness, marketplace source hygiene
Priority: P3

## Problem

Issue 100CJ through 100CL made `plugin_install_freshness.py` catch dirty source
git state, wrong top-level next actions, and installed example-source drift.

That still left an operator gap: a developer can run the freshness check from a
clean feature worktree, but `claude plugin install figure-agent@figure-agent-local`
does not install from the current shell directory. It installs from the
registered `figure-agent-local` marketplace source in
`~/.claude/plugins/known_marketplaces.json`.

If that registered source points at a different checkout, raw install/update can
copy a dirty or stale tree even though the clean worktree was the one under
review.

## Contract

Extend the plugin install freshness diagnostic with a separate
`marketplace_source_hygiene` readiness signal:

- infer the current repo marketplace root from `.claude-plugin/marketplace.json`
  and its `figure-agent` plugin source;
- read the registered `figure-agent-local` directory marketplace from
  `known_marketplaces.json`;
- report `clean` when the registered marketplace source matches the current
  repo marketplace root;
- report `dirty` when it points elsewhere;
- allow `unavailable` outside a discoverable local marketplace context so unit
  tests and ad-hoc plugin roots do not become host-machine dependent;
- exit nonzero when the marketplace source is dirty;
- make top-level `next_action` point at marketplace registration repair after
  source package/git blockers and before installed-cache blockers.

## Acceptance

- TDD reproduces a clean source/install payload where
  `known_marketplaces.json` points `figure-agent-local` at a different repo.
- The CLI emits `marketplace_source_hygiene.state: dirty`, names both
  `registered_source` and `expected_source`, and exits nonzero.
- The CLI keeps payload freshness semantics unchanged (`state: fresh` when
  source and installed payloads match).
- README documents that raw Claude plugin install uses the registered
  marketplace source, not necessarily the current shell directory.

## Verification

- `uv run pytest -q tests/test_plugin_install_freshness.py`
- `uv run pytest -q tests/test_release_contract.py`
- `uv run pytest -q`
- `uv run ruff check scripts/plugin_install_freshness.py tests/test_plugin_install_freshness.py tests/test_release_contract.py`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
