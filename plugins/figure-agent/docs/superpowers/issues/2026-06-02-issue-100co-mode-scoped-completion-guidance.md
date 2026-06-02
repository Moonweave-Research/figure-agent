# Issue 100CO - Mode-Scoped Completion Guidance

Status: implemented
Type: operator UX, driver guidance, completion boundary
Priority: P1

## Problem

`/fig_drive` intentionally supports multiple modes. A complete result in
`authoring` means "source/build loop is closed", while a complete result in
`review` means "no automated review blocker remains". Neither necessarily means
the whole figure is release-ready, accepted, golden-current, or finished from an
art-direction standpoint.

Before this slice, `operator_guidance.next_step` used the same generic complete
text for those mode-local completions:

`No required plugin action remains for this mode.`

That text was technically correct but too easy to misread as whole-figure
completion.

## Contract

Make `operator_guidance.next_step` mode-scoped whenever `/fig_drive` returns
`action: complete`:

- `authoring` complete says render/source authoring is closed and points to
  `--mode review`;
- `review` complete says no automated review blocker remains and points to
  `--mode release` or `--mode final`;
- `polish` complete says it is only SVG-polish mode closure and still requires
  review/final before release readiness;
- `final` and other terminal complete states keep the existing no-required-action
  wording.

This is an explanation change only. It must not change action selection,
safe-command selection, mutation boundaries, or final-readiness gates.

## Acceptance

- TDD reproduces authoring-mode `complete` returning generic guidance without a
  review-mode follow-up.
- TDD reproduces review-mode `complete` returning generic guidance without a
  release/final follow-up.
- The driver keeps `action: complete`, `stop_boundary: null`, and
  `safe_command: null` for those states.
- `/fig_drive` docs explain that complete is selected-mode scoped.

## Verification

- `uv run pytest -q tests/test_fig_driver.py::test_authoring_mode_completes_when_render_fresh tests/test_fig_driver.py::test_review_mode_completes_after_latest_clean_loop_checkpoint`
- `uv run pytest -q tests/test_fig_driver.py tests/test_release_contract.py`
- `uv run pytest -q`
- `uv run ruff check scripts/fig_driver_guidance.py tests/test_fig_driver.py`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
