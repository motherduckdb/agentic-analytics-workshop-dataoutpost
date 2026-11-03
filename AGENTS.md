# Working on this repo

This repo prepares a workshop. It is not the participant repo yet. Read [PLAN.md](PLAN.md) first.

## Writing

- No em dashes or en dashes in prose. Use a period, a comma or a colon.
- Plain declarative sentences. No "it's not X, it's Y" punchlines, no filler intros.
- Slide text stays short. Details go in the speaker notes.

## Slides

- Content: `slides/src/slides.json`. Visuals for `custom` slides: `slides/src/Visuals.tsx`.
- `slides/src/deck.css` is copied unchanged from the Jev for analytics deck on mehdio.com. Do not
  edit it. Put workshop styles in `slides/src/workshop.css`.
- Build with `npm run build` in `slides/`, then open `slides/dist/index.html`.
- `slides/` is the source of truth. The mehdio.com copy (`src/talks/no-ui-data-stack/` in
  mehdio-website) hosts it: after edits, copy `slides/src/` and `slides/assets/` there. Its
  `Deck.tsx` imports `../jev-analytics/deck.css` instead of `./deck.css`.

## Facts

- When a slide or PLAN.md states a product fact (tool names, limits, plans, versions), it must come
  from the code, the docs or a query we ran. Mark anything untested as a draft.

## Secrets

- Never print or commit a MotherDuck token or an AI key. `.env` files are ignored.

## parked/duckoffee

Self-contained and set aside. Its own `AGENTS.md` and `.claude/` hooks apply only when that folder
is opened as the project. See its README.
