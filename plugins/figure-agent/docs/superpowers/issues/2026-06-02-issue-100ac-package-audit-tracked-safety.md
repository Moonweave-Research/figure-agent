# Issue 100AC - Package Audit Tracked-Path Safety

Status: implemented

Type: operations safety, package cleanup, release guard

## Problem

`plugin_package_audit.py --clean` is meant to remove generated junk from an
installed Claude plugin cache. When run against a development checkout, it could
also classify tracked `build/` or `exports/` paths as junk and delete tracked
`.gitkeep` files or checked-in golden export artifacts.

That is unsafe because the helper is documented in release/install workflows and
operators may run it from the development tree while checking package size.

## Root Cause

The junk scanner was filesystem-only. It knew that `build` and `exports`
directories are generated package junk in an installed plugin cache, but it did
not check whether the same paths are tracked source artifacts in a git worktree.

## Goal

Keep installed-cache cleanup behavior unchanged, while making development
checkout cleanup conservative: if a junk-looking path is tracked by git or
contains tracked files, do not remove it.

## Implemented

- `plugin_package_audit.py` now detects tracked files under the audited root
  when the root is inside a git worktree.
- Junk candidates that are tracked files or tracked-containing directories are
  protected from removal.
- Non-git installed plugin caches keep the original cleanup behavior.
- Added a release-contract regression test that initializes a temporary git
  worktree and proves tracked `build/.gitkeep` and `exports/demo.pdf` survive
  cleanup while untracked `.pytest_cache` is still removed.

## Non-Goals

- No package manifest changes.
- No build/export behavior changes.
- No fixture source, accepted, golden, or publication state mutation.
- No attempt to preserve untracked diagnostics in a development tree.

## Verification

- Red test failed first because tracked `build` and `exports` directories were
  reported as junk.
- After the fix, focused package-audit tests passed.

## Review Results

1. Safety: tracked source and golden artifacts are protected when the audit runs
   inside a git worktree.
2. Cache behavior: installed cache roots remain cleanable because they are not
   git worktrees.
3. Scope containment: only the package-audit helper and release-contract tests
   changed.
