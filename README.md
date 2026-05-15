# figure-agent

A Claude Code plugin marketplace containing **`figure-agent`** — a plugin for building reproducible, paper-grade scientific figures in TikZ.

You (or any LLM) author the TikZ. The plugin handles Style Lock, compile, visual QA, vision critique (via the host Claude Code session — no external API keys), and clean PDF / SVG / TIFF / PNG export.

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

The full docs live in [`plugins/figure-agent/README.md`](plugins/figure-agent/README.md). It covers:

- A start-to-finish walkthrough (one figure, six commands)
- Current state (what's shipped in v0.5.0)
- What's experimental / proposed (filed pre-spec issues)
- The documentation map (architecture, golden targets, trials)

## License + author

Author: Moon Choe. See `.claude-plugin/marketplace.json` and `plugins/figure-agent/.claude-plugin/plugin.json` for plugin metadata.
