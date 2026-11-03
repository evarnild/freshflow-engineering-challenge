# freshflow-engineering-challenge — plan

The coordinator view. Each item's detail lives in `intents/<id>-<slug>/`
(see `intents/README.md`). Only the coordinator session edits this file.

## Snapshot

- 2026-11-03: repository created with the AI-native SDLC kit
  (ai-sdlc-kit).
- 2026-11-03: §1 merged. A FastAPI service in `src/freshflow/` loads the
  four CSVs through tested cleaning rules and serves recommendations per
  store and ordering day (Python 3.12, uv, Docker).

## Queue

| Item | Type · status |
| --- | --- |
| [§2](intents/2-sdlc-kit-0-3/) Bring the SDLC kit up to ai-sdlc-kit 0.3.0 | refactor · accepted |

## Backlog

- Later: parallel sessions (a worktree and a session per intent) (`spawn`, `sessions`)
  once more than one intent runs at a time.
- Later: revisit the interim gate-recording rule in `intents/README.md`
  once a few intents have gone through it.

## Shipped

| Item | Merged |
| --- | --- |
| [§1](intents/1-order-recommendations-service/) Stack, skeleton and the order-recommendations service | 2026-11-03 · 99e87e8 |
