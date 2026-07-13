# Figure Agent Authoring Execution Binding Design

**Status:** Approved design

**Authority:** `docs/product-spec.md` and `docs/execution-plan.md` remain the
only product and execution authorities. This document defines the smallest
repair required before rerunning the bounded Fig3 shape-profile experiment.

## Problem

The first two-arm Fig3 run exposed two control-plane failures before any visual
comparison was possible:

1. the generated sources omitted the mandatory
   `\usepackage{polymer-paper-preamble}` import and failed Style Lock lint; and
2. ORRO executed hand-authored inline prompts whose bytes differed from the
   declared Markdown prompt files and their recorded hashes.

The generated sources remain immutable negative evidence. Repairing either
source would hide the Figure Agent failure instead of fixing it.

## Decision

Extend the existing read-only context-pack compiler with one deterministic
authoring-execution packet. The packet is the sole prompt authority passed to
an author lane. It binds the exact rendered prompt bytes, mandatory source
contract, selected optional layout/profile inputs, model declaration, budget,
blank start, and output path.

ORRO role plans must consume the packet's prompt bytes without paraphrasing or
duplicating them. After execution, an arm-specific receipt binds those same
bytes to the transcript and generated source. Any mismatch makes the attempt
`execution_unbound` before compilation or visual review.

## Packet boundary

Add a narrow `figure-agent.authoring-execution-packet.v1` compiler rather than
turning context-pack into a model runner. The packet contains:

- fixture name and context-pack SHA-256;
- exact UTF-8 authoring prompt plus its SHA-256;
- model ID and budget-contract hash;
- blank-start path and SHA-256;
- one repository-relative output path;
- selected layout-contract and shape-profile hashes when present;
- mandatory source requirements, initially the standalone document class,
  TikZ package, and `polymer-paper-preamble` import;
- forbidden import classes and publication boundary; and
- packet SHA-256 computed from canonical JSON fields excluding that hash.

The compiler rejects absolute paths, `..`, symlinks, output paths outside the
fixture attempt directory, missing Style Lock files, duplicate source
requirements, and prompt bytes that do not contain every mandatory source
requirement literally.

## Prompt construction

Prompt construction is deterministic and separate from human prose files. It
combines, in fixed order:

1. the exact output path and one-attempt/no-repair instruction;
2. mandatory standalone TikZ source requirements;
3. semantic contracts and forbidden implications;
4. declared layout directives;
5. optional shape-profile directives; and
6. provenance and publication boundaries.

The packet writer writes the prompt file once. ORRO receives that file's bytes
directly. No role-plan generator may summarize, interpolate, or append arm
instructions after hashing. Control and treatment packets differ only in the
declared treatment overlay and its emitted directives.

## Execution and receipts

Before launching an author lane, a preflight verifies:

- packet canonical hash;
- prompt file hash and byte equality with the packet;
- model and budget equality across arms;
- identical blank-start hash;
- disjoint one-file write scopes; and
- mandatory preamble text in the prompt.

The runtime still cannot prove filesystem read isolation. Receipts therefore
record it as unavailable and separately record transcript-audit observations.

After each lane, the receipt records the packet, prompt, transcript, generated
source, model declaration, actual token usage or an explicit unavailable
reason, feedback rounds, manual repairs, forbidden-input audit, and touched
files. Receipt creation fails when the touched files differ from the declared
one-file scope or any bound bytes drift.

## Failure handling

- Missing mandatory source requirement: fail before model execution.
- Prompt file differs from packet: fail before model execution.
- ORRO executes different bytes: mark `execution_unbound`; do not compile for
  comparison eligibility.
- Generated source omits the mandatory preamble: preserve it as negative
  evidence; do not repair it.
- One arm fails: preserve both arm states and do not compare.
- Both arms compile: run existing layout and strict gates, then prepare human
  visual review.

ORRO and Depone verify persisted execution evidence only. They do not establish
scientific correctness, visual quality, or publication acceptance.

## Testing

Tests proceed from contracts outward:

1. RED tests for mandatory preamble inclusion and canonical prompt hashing;
2. rejection tests for path escape, prompt drift, missing source requirements,
   and unequal arm contracts;
3. CLI tests proving text and JSON expose identical prompt bytes and hashes;
4. receipt tests binding actual prompt/transcript/source bytes and touched
   files; and
5. a new additive two-arm Fig3 run using new filenames and a new ORRO evidence
   directory.

The historical failed run and its receipts are never overwritten.

## Success and stop conditions

The control-plane repair succeeds when a fresh checkout deterministically
produces two packets, ORRO executes byte-identical declared prompts, both
receipts bind actual runtime artifacts, and generated sources either fail
honestly or compile without manual repair.

If both sources render, the workflow stops at named human review for shape
naturalness and contemporary-paper suitability. Machine success remains
`review_ready`, never publication acceptance.
