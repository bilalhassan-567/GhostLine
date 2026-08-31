---
title: Ghostline
emoji: "\U0001F4DE"
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
short_description: Phone-powered data-verification engine (CALL-E hackathon)
---

# Ghostline — hosted console

This Space runs the Ghostline web console. Source, tests, and full documentation:
**https://github.com/bilalhassan-567/GhostLine**

The container clones the GitHub repo at build time, so re-running the build (Space →
Settings → *Factory rebuild*) picks up the latest code.

**Secrets** (Space → Settings → *Variables and secrets*):

| Name | Needed for |
|---|---|
| `CALLE_API_KEY` | Live calls. Without it the console runs in Replay Mode only. |
| `LLM_API_KEY` | The LLM extractor. Without it the deterministic extractor is used. |
| `GHOSTLINE_MODE` | `replay` (default) or `live`. |
| `GHOSTLINE_TEST_NUMBERS` | Comma-separated E.164 lines you own, for the demo. |
