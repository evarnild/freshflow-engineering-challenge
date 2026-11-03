# Review policy

How a change to freshflow-engineering-challenge gets reviewed before it merges into `main`.
The `/review` skill and the `freshflow-engineering-challenge-reviewer` agent both run exactly
these passes. Changing this file is itself a **Reviewed**-tier change.

Merges are local (`git merge` on `main`, then push if a remote exists).
There is no PR. The review report lives in `intents/<id>-<slug>/review.md`
and is updated in place as the change evolves. You act on its verdict line.

## Tiers

Review effort matches what a mistake would cost. Three inputs decide the
tier, applied in order. **Nothing lowers a tier automatically**: only an
edit to this file can.

1. **Paths** (table below) set the default. The tier is the highest one any
   touched path asks for.
2. **The intent** can raise it, through `review_tier:` in `metadata.yml`.
3. **The report** can raise it. Any CRITICAL or HIGH finding escalates to
   Reviewed, and so does a "Not checked" item that bears on what a user
   receives or on data handling.

You may escalate by hand at any time without giving a reason.

| Tier | What happens | What you do | Paths / changes |
| --- | --- | --- | --- |
| **Automated** | `npm run verify` and `npm run check:intent` are green, then merge | nothing beyond merging | `intents/**` artefacts only; `docs/**`; `README.md` wording |
| **Attested** | `/review` runs every pass and writes `review.md` | read the report, not the diff; merge if you agree with its scope | `src/**` not listed below, tests-only changes, `scripts/**` not listed below, build config |
| **Reviewed** | the same report, and you read the diff | full read, then merge | this file; the kit's enforcement (`scripts/intent-check-lib.mjs`, `scripts/check-intent.mjs`); lint guardrails once they exist (a config change that loosens a rule, a raised or removed warning cap, a new disable comment in `src/`); `.claude/agents/**`, `.codex/agents/**`, `.claude/skills/**`; `.claude/settings.json` (its hooks run in every session); **and, by meaning until §1 names the paths:** model prompts and agent instructions the product ships, anything that sends text to a user or an external system without a human in between, credential handling, and storage or logging of users' personal data |

**Approving means:** "I read what the checker did, I accept its scope,
including the Not-checked list, and I take responsibility for this change."
If in doubt, read the code; nothing stops you. That the AI missed something
is not a defence.

### Prerequisites: why Attested is available at all

- a context file the checker reads (`CLAUDE.md`);
- a meaningful test suite run by one command (`npm run verify`);
- this written policy.

If `npm run verify` stops running the tests, or a module loses its tests,
the Attested tier is suspended for those paths until the tests are back.
**Until §1 adds the product's test suite, only the kit itself (`scripts/`)
meets this**, so any `src/` change before then is reviewed as Reviewed.

### Against rubber-stamping

- **Sampling.** Every fifth attested change gets a full diff read after the
  merge. Volume here is low, so a 1-in-20 rate would never fire. Mark it
  `sampled: yes` in its `review.md`. Anything you find that the checker
  missed is a defect in the checker: add a pass or a rule here, or move the
  path to Reviewed.
- **Quality per tier.** `npm run sdlc:scan` (and so `/grid`) counts
  follow-up fixes and reverts per tier. A follow-up fix is a fix intent whose
  `follows_up:` names the intent whose change caused the defect. A revert
  counts when its subject names the reverted `§`. If attested changes need
  follow-ups more often than reviewed ones, the boundary is wrong: move it.
- **Time-to-approve is not tracked.** Fast approval is not the goal.

## Live checks

Some behaviour only shows when the thing runs. A **live check** means you
run it yourself (the agent against a real or sandboxed conversation, a UI,
a hook in a real session) and record that you did, before the merge.

- **When one is owed.** `/review` sets `live-check: owed` when any of these
  holds:
  1. the diff touches a runtime path listed here. §1 adds the product's
     entry points, UI and integration adapters; until then this rule names
     nothing;
  2. the diff touches `.claude/settings.json` (its hooks run in every
     session);
  3. a "Not checked" item is runtime behaviour that only a live run can
     show, such as model output on real input, a third-party API, a hook, or
     a real install. The report names which item.

  Otherwise it sets `live-check: not-needed`.
- **What the report says.** When a check is owed, `## Live check` lists
  concrete steps: the command, the input or fixture to start from, what to
  do, and what you should see. When none is needed, one line says why.
- **Who records it.** You do, after doing the steps, by setting
  `live_checked: <date>` in `metadata.yml`. If the check finds a defect,
  leave the date empty and send the change back to rework, or open a fix
  intent if the defect is out of scope. An agent never writes this date,
  even when asked (`intents/README.md` → "Recording a gate").
- **An agent's own run is evidence, not the gate.** The reviewer or the
  implementer may run the thing and list what it saw under "Verified
  myself". That never fills `live_checked:`. The point is a check by
  someone other than the model that wrote and reviewed the code.
- **Enforced.** `npm run check:intent` fails while the current review says
  `owed` and `live_checked:` holds no date.

## Merging

An agent merges into `main`, pushes, deletes a branch or removes a worktree
**only when the owner explicitly asks for that action in the current
conversation**, never on its own initiative. A request covers the change it
names and does not carry over to the next one. "Go ahead" in reply to a
summary that proposed the merge counts. A standing instruction from an
earlier session, a memory or a `CLAUDE.local.md` brief does not.

Before the merge check runs, `review.md` and any `live_checked:` date must
be **committed to the branch**. The check reads the branch from git, so an
uncommitted report or date is invisible to it.

When asked to merge, the agent first checks the following, and refuses
naming the check that failed:

1. **The review covers what is being merged.**
   - The branch's **committed** `review.md` (`git show
     <branch>:intents/<id>-<slug>/review.md`) says `attest` or `escalate`.
   - Its `reviewed-commit` is an ancestor of the branch (`git merge-base
     --is-ancestor`). A rebase since the review means a new round.
   - Nothing but that intent's `review.md` or `metadata.yml` differs between
     `reviewed-commit` and the branch (`git diff --name-only`).
2. `npm run check:intent <branch>` reports PASS, or ROUTE with the reason
   already stated in `review.md`.
3. No live check is owed without `live_checked:` recorded. `check:intent`
   covers this.

Then it merges with `--no-ff` and runs `npm run verify` on `main`. Last, it
does the bookkeeping: `merged:` and `status: done` in `metadata.yml`, and the
`plan.md` row moves to Shipped.

## Passes

Each pass reports `pass`, `findings`, or `not run` with the reason.

1. **Intent and plan match.** The diff does what `intent.md`'s outcome and
   `plan.md`'s subtasks say, and nothing more. Unplanned scope is a finding,
   and so is refactoring mixed into a feature.
2. **Type check.** Run `npm run check:intent` and paste its output. A
   `ROUTE` needs a stated reason or a re-declared type.
3. **Behaviour against the spec.** Every acceptance criterion in `spec.md`
   (features), or the reproduction in `intent.md` (fixes), is met. Check it
   in the code and tests, not in the implementer's summary.
4. **Tests prove the behaviour, not only pass.** Enumerate mutations from
   the diff, one per changed behavioural line. Revert each one, run the full
   suite, and confirm that something fails. Guard the harness by asserting
   that the file actually changed. Report killed and survived mutants per
   line. A fix must carry a test that failed before the fix.
5. **Conventions** (`CLAUDE.md`). The architecture boundaries and
   conventions written there hold.
6. **Numbers in prose.** Every measurement in `plan.md`, `README.md`, intent
   artefacts and test comments can be reproduced.
7. **Documentation.** `README.md` documents new behaviour, and `CLAUDE.md`
   still describes the architecture accurately.
8. **Guardrails and hygiene.** Lint passes (once there is lint) and the
   warning cap did not rise. No new dependency arrives without a line in the
   intent's `plan.md` saying why. No secret, token or user data is
   committed, including in fixtures and logs. No user- or model-supplied
   text reaches a shell, `eval`, SQL, or HTML unescaped.
9. **Repository-specific footguns.** This list starts empty and grows from
   findings: when a class of bug recurs, name it here so every later review
   looks for it.

**Finding or nit.** A finding is something that is wrong, unproven, or will
mislead the next person: a spec deviation, a surviving mutant, a stale
number. Style preferences, naming taste and "could be shorter" are nits:
leave them out, or put them in one line at the end.

Severities:
- **CRITICAL**: leaks data or credentials, sends something wrong to a
  user, or loses data.
- **HIGH**: wrong behaviour, or behaviour the tests don't prove.
- **MEDIUM**: correct but fragile, or misleading docs.
- **LOW**: stale docs, or something minor.

## The report — `intents/<id>-<slug>/review.md`

The report is structured so that `/grid` can count verdicts without a
separate store.

```markdown
<!-- generated-by: freshflow-engineering-challenge/review@<version> -->
# §<id> review — <title>

verdict: attest | escalate | rework
tier: automated | attested | reviewed
reviewed-commit: <hash>
round: <n>
sampled: no
live-check: owed | not-needed

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass |
| … | … | findings (2) |

## Type check
<output of npm run check:intent>

## Findings
- **HIGH** `src/foo.ts:42` — <what is wrong>. Needs rework: <minimal fix>.
- **LOW** `README.md:12` — <…>. Worth a look.

## Not checked
- <what this run could not assess, and why. Be specific: this list is the
  harness backlog>

## Live check
- owed: <rule 1, 2 or 3 from "Live checks", and which Not-checked item>
- steps: <command> → <input or fixture> → <what to do>
- you should see: <the observable result>
<!-- or, when not needed: "not needed — <why>" -->

## Verified myself vs. taken on trust
- <which commands actually ran, with results>
```

Verdicts:
- `attest`: no findings that need rework. Approve if you agree.
- `rework`: lists what must change. The implementer fixes it and `/review`
  runs again.
- `escalate`: routes the change to the Reviewed tier.

Each new round increments `round` and updates the file in place:
- the current round's header and report go at the top;
- earlier rounds move below a `# Round N (history)` heading, with their
  header fields turned into list items, so the scan reads only the current
  verdict;
- each round's findings stay listed with their resolution.
