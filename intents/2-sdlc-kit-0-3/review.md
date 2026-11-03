<!-- generated-by: freshflow-engineering-challenge/review@0.2.0 -->
# §2 review — Bring the SDLC kit up to ai-sdlc-kit 0.3.0

verdict: escalate
tier: reviewed
reviewed-commit: 847c231
round: 2
sampled: no
run: manual
live-check: owed

**Scope:** commit 847c231, which fixes round 1's findings. It touches
documentation only: `OVERVIEW.md`, `docs/sdlc-grid.md`, and §2's
`intent.md` and `plan.md`. The tier stays Reviewed (it is never lowered).
No finding needs rework.

## Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass. Fixes exactly round 1's MEDIUM and two LOWs |
| 2 | Type check | FAIL, and its only error is the owed live check. The ROUTE reason from round 1 stands |
| 3–5 | Behaviour, tests, conventions | pass. No code or test changed |
| 6 | Numbers in prose | pass. The grid's measures row matches `sdlc:scan`: 6 changes, 83%, 0 reverts, 2 intents stamped |
| 7 | Documentation | pass. The grid is refreshed. `OVERVIEW.md` and the grid both say §1's gates predate `by-agent` |
| 8–9 | Hygiene, footguns | pass |

## Type check
```
type-check: FAIL (intent 2, refactor)
  error: A live check is owed and not recorded. Do the steps in intents/2-sdlc-kit-0-3/review.md → ## Live check, then set live_checked: <date> in intents/2-sdlc-kit-0-3/metadata.yml.
```
ROUTE, reason stated in round 1: only the 4 interim gate-rule test lines were
deleted, and they were replaced by `by-agent` tests.

## Round-1 findings
- **MEDIUM** (§1 gates counted as owner gates): **resolved** by
  documenting it in `OVERVIEW.md` and in the grid's declared choices.
  `sdlc:scan` still counts them as owner gates, by design, because history
  isn't rewritten.
- **LOW** (stale grid): **resolved**. The grid was refreshed at
  `grid@0.2.0`, with levels, a measures row, two moves and a changelog
  line.
- **LOW** (254 tests): **resolved**. `intent.md` and `plan.md` now say 256
  once §1 is merged.

## Findings
- **LOW** `docs/sdlc-grid.md`, Test row: `sdlc:scan` reports `lint: no`,
  although `verify` runs ruff. The scan doesn't detect ruff; the grid states
  this. Worth a look later (a scan rule for `pyproject.toml`'s
  `[tool.ruff]`).

## Not checked
- The grid's levels are the coordinator's scoring from the evidence. You
  confirm or adjust them.
- Everything in round 1's Not-checked list still applies.

## Live check
Unchanged from round 1 (below). Open a new Claude Code session in the §2
worktree, send a prompt, answer one permission prompt, then run
`npm run sessions` and `npm run sessions -- --log 10`. You should see the
row as `working` or `idle`, and prompt lengths only, never the words.

## Verified myself vs. taken on trust
- `git diff --name-only 026e860 847c231`: only the four files above, plus
  this `review.md`.
- `npm run verify`: kit 256/256, ruff clean, pytest 122 passed.
- `npm run check:intent`: FAIL, and its only error is the owed live check.
- `npm run -s sdlc:scan`: no metadata problems, and its numbers match the
  measures row.
- Taken on trust: nothing new.

# Round 1 (history)

- verdict: escalate
- tier: reviewed
- reviewed-commit: 026e860
- round: 1
- sampled: no
- run: manual
- live-check: owed

**Tier:** the path table sets Reviewed, because the change touches this
policy, the kit's enforcement scripts, skills, agents and
`.claude/settings.json`. No finding needs rework, so the verdict is
escalate: read the diff, do the live check, then merge.

### Passes
| # | Pass | Result |
| --- | --- | --- |
| 1 | Intent and plan match | pass. 26c997f matches a fresh 0.3.0 render except `OVERVIEW.md` and the coordinator path. `src/` and `tests/` are untouched |
| 2 | Type check | ROUTE, reason stated below |
| 3 | Behaviour | pass. `queue`, `sessions` and the `ship` dry run work, and §1's facts survive the merge |
| 4 | Tests prove behaviour | pass. 9/9 mutants on the lines the merge touched are killed |
| 5 | Conventions | pass |
| 6 | Numbers in prose | findings (1, LOW) |
| 7 | Documentation | findings (1, LOW) |
| 8 | Guardrails and hygiene | pass. The hook logs prompt length only, never prompt text |
| 9 | Footguns | pass |

### Type check
```
type-check: ROUTE (intent 2, refactor)
  route: Declared refactor, but existing tests lost lines (scripts/intent-check-lib.test.mjs). Behaviour may have changed — check, or route to feature.
```
ROUTE, reason stated: the only lines deleted are 4 in
`scripts/intent-check-lib.test.mjs`, the old interim gate-rule loop. Those
values are re-asserted as malformed, and `by-agent`, `parseGate` and `[]`
tests were added. §1's `CORE_CODE` tests are untouched.

### Findings
- **MEDIUM** `scripts/scan-lib.mjs:34-43` with
  `intents/1-order-recommendations-service/metadata.yml:11-13`.
  - **What's wrong:** §1's agent-recorded gates predate the `by-agent`
    marker, so `npm run sdlc:scan` counts them as recorded by the owner
    (`intent_accepted: 1 owner · 1 agent`; the owner entry should be agent).
  - The gates still read as recorded. Only the owner/agent split that
    `/grid` publishes is wrong.
  - Worth a look: one line in `OVERVIEW.md`, or in the grid, saying §1's
    gates predate `by-agent`. Don't rewrite history.
- **LOW** `docs/sdlc-grid.md:21,31`: still says "254 tests; there is no
  product suite" and "stack-agnostic until §1". Worth a look: run `/grid`
  after the merge.
- **LOW** `intents/2-sdlc-kit-0-3/intent.md`, `plan.md`: say 254 tests; after
  the merge there are 256 (Progress has it right). Worth a look.

### Not checked
- 0.3.0's own code beyond the lines the merge touched (queue, spawn and
  sessions rendering, `/auto`, the skills' prose). This rests on the render
  matching `f7cdeaa` and its tests passing.
- The hooks in a real Claude Code session: they were fed synthetic input
  only. That is the live check.
- `setup:worktree` (`uv sync`) in a real `npm run spawn`.
- A real `/ship 2`: only the dry run ran.

### Live check
- **owed:** rule 2. `.claude/settings.json` adds hooks that run
  `scripts/session-event.mjs` in every session.
- **steps:**
  1. Open a new Claude Code session in
     `C:\Users\eric\src\freshflow-engineering-challenge-wt\2-sdlc-kit-0-3`.
  2. Send "say hi", then ask it to run `git status` and answer the
     permission prompt.
  3. In a terminal there, run `npm run sessions`, then
     `npm run sessions -- --log 10`.
- **you should see:**
  - that worktree's row shows `working` or `idle`, not `no events`;
  - the log has `SessionStart`, `UserPromptSubmit` (`"N chars"`, no prompt
    text), `Notification` and `Stop`;
  - no hook errors in the session;
  - the words of your prompt don't appear in the main checkout's
    `.git/freshflow-engineering-challenge-sessions.jsonl`.

### Verified myself vs. taken on trust
**Coordinator, at 026e860:**
- `npm run check:intent`: ROUTE as above.
- `npm run sdlc:scan`: the owner/agent split as in the MEDIUM finding.
- `git diff main HEAD -- scripts/intent-check-lib.test.mjs`: 4 deleted
  lines.
- Before the commit, `npm run verify`: kit 256/256, ruff clean, pytest 122.

**Reviewer agent:**
- `npm run verify` (exit 0).
- `queue`, `sessions` and `ship 2 --dry-run`: the dry run stops at the
  uncommitted `review.md` and changes nothing.
- A fresh 0.3.0 render compared against 26c997f with `diff -r`.
- `git diff main HEAD` on the shared files: `CORE_CODE`, `verify`,
  Architecture, rule-1 paths, `api.py` and `.gitignore` all kept, with no
  `{{` placeholders or "Recording a gate" left.
- The hook script on garbage, empty input and a non-git directory: exit 0
  and silent each time. With a backslash `CLAUDE_PROJECT_DIR` it logs
  `promptChars` only.
- 9 mutants, the full kit suite for each, all killed:
  - `CORE_CODE` ×3;
  - the ship ROUTE, FAIL and exit-code handling ×3;
  - `setup:worktree` not run;
  - `by-agent` rejected;
  - the hook logs prompt text.
- `git status` clean afterwards.

**Taken on trust:** that the local `ai-sdlc-kit-main` copy is `f7cdeaa`.
