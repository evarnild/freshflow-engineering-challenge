# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project overview

freshflow-engineering-challenge: a new project; its purpose is written down by §1.

So far the repository holds only the
AI-native SDLC kit (from ai-sdlc-kit, first built for heraklios). The
product's stack and architecture are **§1's decision** (undecided). Until §1
merges, there is no product code, and no section below describes any.

## Commands

```
npm run verify        # THE check before a change is done (today: the kit's own tests)
npm run check:intent  # does this branch's change match its intent? (intents/README.md)
npm run sdlc:scan     # the evidence behind docs/sdlc-grid.md
npm run test:kit      # node --test over scripts/*.test.mjs
```

The kit needs Node ≥ 22 and nothing else: no `npm install`. §1 extends
`verify` with the product's build, lint and tests, whatever the stack is.
Keep it **one** command.

## How work flows

`sdlc.md` is the step-by-step version for the owner: intent → spec → plan →
build → review → merge, and what each type requires. If it disagrees with the
rules below or with `intents/README.md` and `REVIEW-POLICY.md`, those win.

- `plan.md` is the coordinator view (snapshot, queue, backlog, shipped).
  Each work item's detail lives in `intents/<id>-<slug>/`. Read
  `intents/README.md` for the types, the gates and branch naming
  (`feat/2-…`, `fix/2-…`).
- No code before the plan's gate is recorded in `metadata.yml`. Who may
  record a gate is set out in `intents/README.md` → "Recording a gate".
- `/intent` drafts an intent, `/review` runs `REVIEW-POLICY.md` and writes
  `review.md`, and `/grid` refreshes `docs/sdlc-grid.md`.
- The `freshflow-engineering-challenge-implementer` agent builds an approved plan, and the
  `freshflow-engineering-challenge-reviewer` agent does the adversarial passes for `/review`.
- Merges into `main` are local. An agent merges, pushes, deletes a branch
  or removes a worktree only when the owner explicitly asks for that action
  in the current conversation, never on its own initiative, and only after
  the preconditions in `REVIEW-POLICY.md` → "Merging".
- **Never `git checkout` a branch in the main checkout.** It belongs to the
  coordinator session. Implementers and reviewers work in their own
  worktrees.
- A change owes a **live check** when `REVIEW-POLICY.md` → "Live checks"
  says so. The owner runs it and records `live_checked: <date>` before the
  merge. An agent's own run is evidence, never that gate.

## Architecture

None yet. §1 writes this section: the modules, the boundary between pure,
tested logic and I/O (model calls, channels, storage), and the conventions
worth knowing before editing. When it does, it also:

- narrows `CORE_CODE` in `scripts/intent-check-lib.mjs` to the modules whose
  mistakes cost most;
- names the runtime paths that owe a live check (`REVIEW-POLICY.md` →
  "Live checks", rule 1);
- names the paths behind the Reviewed tier's "by meaning" list (prompts,
  user-facing output, credentials, personal data).

## Conventions that already apply

- Model calls and external APIs are faked or recorded in tests, never called
  live from the suite.
- No secret, token or real user data is committed, including in fixtures
  and logs.
- No new dependency arrives without a line in the intent's `plan.md` saying
  why.
