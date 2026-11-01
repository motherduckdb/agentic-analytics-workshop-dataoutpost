# The Next Data Stack Has No UI

A 90-minute hands-on workshop by Mehdi Ouazza and Jacob Matson (MotherDuck). Participants build an
analytics agent end to end, and each fundamental of an analytics agent is mapped to a MotherDuck
feature: the loop, context, interface, isolation, access and observability.

**Status: planning.** Nothing here is ready for participants yet. Start with [PLAN.md](PLAN.md).

| Path | What it is |
|---|---|
| [`PLAN.md`](PLAN.md) | The original abstract, what changed, the agenda, checked facts, decisions, open questions, next steps |
| [`HANDOFF.md`](HANDOFF.md) | How the plan evolved, where the facts came from, working preferences. Read this when picking the work up elsewhere |
| [`slides/`](slides/) | Draft deck. Same engine and brand as the talks on mehdio.com |
| [`parked/duckoffee/`](parked/duckoffee/) | The first dataset kit (messy raw exports, six breaks, a grader). Set aside for a longer format |

## Slides

```bash
cd slides
npm install
npm run build        # or: npm run watch
open dist/index.html
```

Keys: arrows to navigate, N for speaker notes, G to pick a slide, F for full screen, H to step
through code lines. Slide text lives in `slides/src/slides.json`, and the notes carry timings and
the planning details per slide.
