# Figure Agent

Figure Agent is a paper-figure quality kernel for scientific schematics. A
human, LLM, or declared domain tool authors the figure; the kernel preserves
intent and evidence, renders editable source, detects reproducibility and
legibility failures, and routes bounded repair without claiming publication
acceptance.

It is not a graph plotting library. It is not a matplotlib wrapper. It is not a one-shot image generator.

Convergence means reaching the highest achievable scientific-figure aesthetic
quality while staying strictly inside the target journal's guidelines. Journal rules are hard constraints; beauty is optimized only within those constraints.

This repository is also a Claude Code plugin marketplace containing
**`figure-agent`**, the local plugin implementation for reproducible,
paper-grade scientific figures in TikZ.

## Install

This repo is a **local marketplace**, not a published one. Add it directly from this checkout:

```bash
# from inside this repo
claude plugin add .
```

Or point at the marketplace manifest:

```bash
claude plugin add path/to/this/repo/.claude-plugin/marketplace.json
```

The canonical documented workflow route is:

```
/fig_new       /fig_status      /fig_compile
/fig_critique  /fig_adjudicate  /fig_run
/fig_export    /fig_closeout
```

This route does not retire supporting or compatibility commands. Runtime enters
through `/fig_status` and `/fig_run`; the shared classification lives in
[`plugins/figure-agent/docs/public-command-route.yaml`](plugins/figure-agent/docs/public-command-route.yaml);
callable-surface compaction remains unfinished roadmap work.

## What's inside

```
.
├── .claude-plugin/
│   └── marketplace.json        ← declares this repo as a marketplace
└── plugins/
    └── figure-agent/           ← the plugin itself
        ├── README.md           ← full documentation (start here)
        ├── commands/           ← public and compatibility command adapters
        ├── skills/             ← workflow skill
        ├── scripts/            ← compile, export, critique, perception pack
        ├── examples/           ← per-figure folders (specs, briefings, sources)
        └── docs/               ← authority, references, project state, evidence
```

## Documentation

Agents and contributors must start with the sole product and execution
authority:

- [`plugins/figure-agent/docs/figure-agent.md`](plugins/figure-agent/docs/figure-agent.md) — product contract, architecture boundaries, executable roadmap, and completion gates.

The operational docs live in [`plugins/figure-agent/README.md`](plugins/figure-agent/README.md). It covers:

- A start-to-finish walkthrough for the canonical documented route
- Current state for plugin version v0.10.0
- The supported and compatibility command surfaces
- The active operational architecture and human/machine boundaries

Document status is machine-readable in
[`plugins/figure-agent/docs/document-status.yaml`](plugins/figure-agent/docs/document-status.yaml).
Only the authority and approved operational references ship in the generic
Cowork package; paper-local state, plans, trials, and historical proposals do
not instruct installed agents.

## License + author

Author: Moon Choe. See `.claude-plugin/marketplace.json` and `plugins/figure-agent/.claude-plugin/plugin.json` for plugin metadata.
