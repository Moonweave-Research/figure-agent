# Figure Agent

Figure Agent is an agentic system for creating publication-quality scientific
and technical figures.

It is not a graph plotting library. It is not a matplotlib wrapper. It is not a one-shot image generator.

The system turns figure intent into an editable figure representation, renders
candidate figures, critiques them visually and semantically, checks journal
compliance, and iteratively repairs the figure until it converges.

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

After install, the six commands are available in any Claude Code session:

```
/fig_new       /fig_extract    /fig_compile
/fig_critique  /fig_export     /fig_status
```

## What's inside

```
.
├── .claude-plugin/
│   └── marketplace.json        ← declares this repo as a marketplace
└── plugins/
    └── figure-agent/           ← the plugin itself
        ├── README.md           ← full documentation (start here)
        ├── commands/           ← the six slash commands
        ├── skills/             ← workflow skill
        ├── scripts/            ← compile, export, critique, perception pack
        ├── examples/           ← per-figure folders (specs, briefings, sources)
        └── docs/               ← architecture, golden targets, dogfood trials
```

## Documentation

Agents and contributors must start with the sole product and execution
authority:

- [`plugins/figure-agent/docs/figure-agent.md`](plugins/figure-agent/docs/figure-agent.md) — product contract, architecture boundaries, executable roadmap, and completion gates.

The operational docs live in [`plugins/figure-agent/README.md`](plugins/figure-agent/README.md). It covers:

- A start-to-finish walkthrough (one figure, six commands)
- Current state (what's shipped in v0.5.0)
- What's experimental / proposed (filed pre-spec issues)
- The documentation map (architecture, golden targets, trials)

## License + author

Author: Moon Choe. See `.claude-plugin/marketplace.json` and `plugins/figure-agent/.claude-plugin/plugin.json` for plugin metadata.
