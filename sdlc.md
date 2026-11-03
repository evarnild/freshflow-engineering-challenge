# How to make a change in freshflow-engineering-challenge

This is the short version of the AI-native SDLC as it runs here. The detail
lives in [`intents/README.md`](intents/README.md) (types, gates, who edits
what) and [`REVIEW-POLICY.md`](REVIEW-POLICY.md) (tiers, review passes). If
this file and those disagree, they win.

Every change follows the same path, and its **type** decides how much of it
you do. Work from a Claude Code session started in the main checkout
(`C:\Users\eric\src\freshflow-engineering-challenge`). That session is the **coordinator**,
and it is where `CLAUDE.md` and the skills load. The id is the next `§`
number after the highest one in `plan.md` or `intents/`.

## The steps

**1. Intent: what you want and why**

- Run `/intent` and describe the problem in your own words.
- It creates `intents/<id>-<slug>/` with `intent.md` and `metadata.yml`, and
  proposes a type. When in doubt, the type is feature.
- Read it. If it's right, record `intent_accepted: <date>`, or ask Claude to
  record it ("accept §N's intent"). This is gate 1, and it is yours.

**2. Spec (features only)**

- `spec.md` says what will be built.
- You record `spec_accepted`.

**3. Plan: how it will be built**

- `plan.md` lists the files, the tests and the steps.
- You record `plan_approved`. No code before this gate: `check:intent` fails
  a change whose code came first.

**4. Build**

The coordinator creates the branch `feat|fix|refactor|adjust|exp/<id>-<slug>`
in a worktree. The `freshflow-engineering-challenge-implementer` agent works through the plan,
tests first. The build ends with `npm run verify` green and
`status: in-review`.

**5. Review**

Run `/review` from the coordinator. It runs `npm run verify`,
`npm run check:intent` and the passes in `REVIEW-POLICY.md`, then writes
`review.md` with a verdict:

- **rework**: fix, then run `/review` again;
- **attest** or **escalate**: go to step 6.

The report also says `live-check: owed` or `not-needed`. When a live check is
owed, its `## Live check` section gives the steps. Run them yourself, then
record `live_checked: <date>`. Only you write that date. If you find a defect,
leave the date empty and send the change back to rework.

Commit `review.md` and the `live_checked:` date to the branch before the
merge: the merge check reads the branch from git and can't see uncommitted
files.

**6. Approve and merge (your gate)**

- **Automated tier** (only intents or docs touched): merge.
- **Attested tier** (`src/`, scripts, tests): read the report, then merge.
- **Reviewed tier** (this policy, the kit's checker, agents, skills, and
  anything that handles prompts, user-facing output, credentials or
  personal data): read the report **and** the diff, then merge.

Merging goes in this order:
1. `git merge --no-ff` on `main`;
2. `npm run verify` on `main`;
3. set `merged:` and `status: done` in `metadata.yml`;
4. move the `plan.md` row to Shipped.

You can ask Claude to do the merge, each time, for that change. It first
checks the review and `check:intent`, and refuses if either does not hold
(`REVIEW-POLICY.md` → "Merging").

## What each type requires

| Type | Use for | You record |
| --- | --- | --- |
| feature | new behaviour, a new integration, anything with a design question | intent, spec, plan |
| fix | a live defect; needs a test that fails first, and `follows_up: <id>` if an earlier § caused it | intent, plan |
| refactor | structure changes, behaviour held constant | intent, plan |
| adjustment | wording, README, config, constants: at most 5 files and 60 lines, no core code | intent only |
| experiment | throwaway probes; never merged into core code as-is | intent only |

## Along the way

- `/grid` refreshes `docs/sdlc-grid.md`. Run it every few weeks.
- A defect you hit becomes a new **fix** intent. Triaging it is one of your
  gates too.
- Every fifth attested change gets a full diff read after merge
  (`sampled: yes` in its `review.md`).

To start: `/intent` plus what you want changed. The first one is §1, the
stack and skeleton.
