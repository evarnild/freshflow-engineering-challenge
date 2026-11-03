<!-- generated-by: freshflow-engineering-challenge/grid@0.2.0 -->
# freshflow-engineering-challenge — AI-native SDLC grid

One area: the whole repository. Owner: eric.varnild. Refresh with `/grid` at
the start of each quarter or after a pilot change. The numbers come from
`npm run sdlc:scan`, not from memory.

Model and levels: six stages (Intent, Design, Build, Test, Deploy,
Maintain) and five levels (L0–L4). Each stage ends in an artefact the next
one reads, with humans at the gates. The kit was first built for heraklios
(github.com/evarnild/heraklios), whose `docs/sdlc-grid.md` is a worked
example.

## The grid — 2026-11-03 (after §1 shipped, with §2 in review)

| Stage | Level | Evidence | Gap to next level |
| --- | --- | --- | --- |
| **Intent** | L2 (feature, refactor) | §1 and §2 were drafted by `/intent` (stamped) and accepted through their gates | L3: a user report or monitor drafts an intent itself |
| **Design** | L1 (feature) | §1's `spec.md` was written with the `/intent` skill and accepted at its gate. `sdlc:scan`: 0 specs by `/spec`, 1 hand (old stamp) | L2: the next feature's spec produced by `/spec` |
| **Build** | L1 | `CLAUDE.md` with §1's architecture. Plans approved before code (enforced by `check:intent`); the implementer agent built §1. Plans: 0 by `/build-plan` | L2: plans by `/build-plan`, and hooks that block unsafe actions (§2's hooks only observe) |
| **Test** | L1, partly (product and kit) | `npm run verify` runs the kit's 256 tests, `ruff check`, `ruff format --check` and pytest (122, including the real-data test). §1's reviews mutation-tested the product code. There is no dependency or secret check yet. `sdlc:scan` reports `lint: no` because it doesn't detect ruff | Full L1: a dependency and secret check in `verify` |
| **Deploy** | L1 | `REVIEW-POLICY.md` tiers; `/review` with the reviewer agent on every change (§1: 3 rounds; §2: 1); the owner's live check recorded before the merge; `/ship` checks the merge preconditions as tested code | L2: tiers applied and gates enforced as hooks |
| **Maintain** | L0 | The service runs locally and in Docker, but is not deployed, so nothing is observed | L1: findings written as fix intents |

**Production release stays human by design**: any deployment and any push
stay manual gates at every level.

**Declared choices** (the scan can't see these, so keep them on refresh):
- Merges are local. The review report is a committed `review.md`, not a PR
  comment. `main` is pushed to GitHub by hand.
- Stack (§1): Python 3.12, FastAPI and uv, in Docker. The kit's scripts need
  Node ≥ 22.
- §1's gates were recorded by an agent at the owner's request, before
  0.3.0's `by-agent` marker existed. They carry the comment
  `# recorded by agent on owner's request`, so `sdlc:scan` counts them as
  owner gates: 3 agent gates show up as owner gates, and history isn't
  rewritten. Gates recorded by agents from §2 on use `by-agent`.

## The two we move — Q4 2026

1. **Test → full L1 (climb).** Add a dependency audit and a secret scan to
   `npm run verify`. The service now has dependencies and a public repo.
2. **Design → L2 (widen).** Run the next feature's spec through `/spec`,
   instead of drafting it by hand alongside the intent.

## Measures

Report progress and outcome together, never one without the other. Never
read throughput without the revert rate beside it.

| Date | Window | Changes on main | Per week | Reference an intent/§ | Reverts | Intents (stamped) | Attested / reviewed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-03 | repo start | 1 (the kit scaffold) | — | — | 0 | 0 (0) | — |
| 2026-11-03 | 2026-11-03 → 2026-11-03 | 6 | 6 | 83% | 0 (0.0%) | 2 (2) | 0 attested / 1 reviewed (§1), 0 follow-up fixes |

## What each level means here

| Stage | L1 · by hand | L2 · codified | L3 · triggered | L4 · closed loop |
| --- | --- | --- | --- | --- |
| Intent | `intents/<id>/intent.md` written with an assistant, type declared, accepted in metadata | `/intent` drafted and validated it (stamp) | a user report or a monitor drafts the intent itself | intents drafted, deduplicated and ranked unattended |
| Design | `spec.md` written by hand for features | a `/spec` skill loads conventions and prior decisions | accepting an intent fires the spec pass | specs produced unattended; only flagged concerns reach you |
| Build | context file; plan approved before code | shared skills and agents for plan, implement, verify; hooks block unsafe actions | an accepted spec fires plan generation | approved plans implemented unattended where the checks carry it |
| Test | `npm run verify` with a fresh context; failing test first for fixes; security check | test files protected during fixes; a verification skill; an eval suite where the product uses a model | a new change fires verification automatically | verification repairs its own failures within limits |
| Deploy | written review policy; agentic review on every change | tiers applied automatically from the policy; gates enforced as hooks | a verified change fires review; you act on the report | everything up to the release gate unattended (ceiling) |
| Maintain | findings written as fix intents | scheduled evals or soak runs; deterministic checks | a failure fires diagnosis; you triage | findings written back as intents unattended |

Don't skip L1, and don't automate a stage past the point where its output
can be checked.

## Changelog

- 2026-11-03: first fill, alongside the kit scaffold.
- 2026-11-03: refreshed after §1 shipped and §2 merged `main` in. Intent → L2, Test → L1 partly, Deploy → L1.
