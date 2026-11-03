# freshflow-engineering-challenge — plan

The coordinator view. Each item's detail lives in `intents/<id>-<slug>/`
(see `intents/README.md`). Only the coordinator session edits this file.

## Snapshot

- 2026-11-03: repository created with the AI-native SDLC kit
  (ai-sdlc-kit). There is no product code yet. Stack: undecided.

## Queue

| Item | Type · status |
| --- | --- |
| [§1](intents/1-order-recommendations-service/) Stack, skeleton and the order-recommendations service | feature · accepted |

## Backlog

- §1: choose the stack and build the project skeleton. Extend `npm run
  verify` with build, lint and test. Write `CLAUDE.md` → "Architecture".
  Narrow `CORE_CODE`. Name the live-check and Reviewed-tier paths. Start it
  with `/intent --feature`.
- Later: parallel sessions (a worktree and a session per intent) (`spawn`, `sessions`)
  once more than one intent runs at a time.
- Later: revisit the interim gate-recording rule in `intents/README.md`
  once a few intents have gone through it.

## Shipped

| Item | Merged |
| --- | --- |
