# Issue 61 - External Second-Opinion Vision Evidence

Status: proposed

Depends on: Issue 58 single next-action UX and Issue 59 SVG polish promotion
dogfood

## Problem

Host-vision critique is stronger after high-zoom crops, crop-read
accountability, clash candidates, and aesthetic packs, but a single vision
model can still miss small aesthetic or geometry defects. External second
opinions can help, but direct provider automation introduces cost, quota,
privacy, and reproducibility problems.

The missing plugin layer is not an API client. It is a first-class evidence
import contract for independent visual reviews.

## Goal

Define and test an optional external-vision evidence import path that lets a
human or outer agent attach a second-opinion review without letting that review
mutate source, accepted/golden state, export state, or release gates by itself.

## Order

Run after next-action UX and SVG route dogfood. External reviews should clarify
edge cases, not compensate for unclear local state.

## Scope

In scope:

- Design an optional evidence file such as
  `examples/<name>/external_vision_review.yaml`.
- Require provenance fields:
  - reviewer/model/tool name;
  - reviewed artifact hash;
  - reviewed crop ids or image paths;
  - timestamp;
  - findings;
  - confidence;
  - conflicts with host critique if any.
- Include the evidence in critique freshness only when the fixture opts in.
- Surface conflicts as human review, not automatic truth.
- Add lint/schema tests for malformed or stale evidence.

Out of scope:

- Calling Gemini, Claude, OpenAI, or any other provider from the plugin.
- Storing API keys.
- Making external review a required gate for all fixtures.
- Automatically applying external suggestions.
- Treating external review as higher authority than local contracts.

## Acceptance

- The external evidence contract is optional and controlled.
- Stale external evidence cannot silently pass as current.
- Conflicting external vs host critique findings surface as human review.
- Provider-specific details remain outside the plugin core.
- No network dependency is introduced into tests or normal commands.

## Review Questions

1. Does this improve blind-spot coverage without making the plugin provider
   dependent?
2. Can stale or mismatched external evidence affect a current figure?
3. Are conflicts routed to human judgment instead of automatic override?
4. Does the format remain useful for Gemini, Claude, or manual reviewer notes?
