<!-- generated-by: freshflow-engineering-challenge/review@0.2.0 -->
# §2 review — Bring the SDLC kit up to ai-sdlc-kit 0.3.0

verdict: escalate
tier: reviewed
reviewed-commit: 026e860
round: 1
sampled: no
run: manual
live-check: owed

**Tier:** the path table sets Reviewed, because the change touches this
policy, the kit's enforcement scripts, skills, agents and
`.claude/settings.json`. No finding needs rework, so the verdict is
escalate: read the diff, do the live check, then merge.

## Passes
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

## Type check
```
type-check: ROUTE (intent 2, refactor)
  route: Declared refactor, but existing tests lost lines (scripts/intent-check-lib.test.mjs). Behaviour may have changed — check, or route to feature.
```
ROUTE, reason stated: the only lines deleted are 4 in
`scripts/intent-check-lib.test.mjs`, the old interim gate-rule loop. Those
values are re-asserted as malformed, and `by-agent`, `parseGate` and `[]`
tests were added. §1's `CORE_CODE` tests are untouched.

## Findings
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

## Not checked
- 0.3.0's own code beyond the lines the merge touched (queue, spawn and
  sessions rendering, `/auto`, the skills' prose). This rests on the render
  matching `f7cdeaa` and its tests passing.
- The hooks in a real Claude Code session: they were fed synthetic input
  only. That is the live check.
- `setup:worktree` (`uv sync`) in a real `npm run spawn`.
- A real `/ship 2`: only the dry run ran.

## Live check
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

## Verified myself vs. taken on trust
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
