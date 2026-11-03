# §2 plan — Bring the SDLC kit up to ai-sdlc-kit 0.3.0

Intent: [intent.md](intent.md)

Approved before any code exists. If the plan turns out wrong mid-execution,
stop, fix the plan, and re-approve — don't push through.

## Goal

Replace this repo's kit files with ai-sdlc-kit 0.3.0 (`f7cdeaa`) rendered
for this repo, on `refactor/2-sdlc-kit-0-3`, and merge it after §1 ships,
keeping everything §1 wrote into the shared files.

## Risks

- **The merge with §1.** Six files overlap. A careless resolution would drop
  §1's `CORE_CODE`, its live-check and Reviewed paths, its `verify` command
  or its Architecture section, or bring back the old "Recording a gate"
  wording. Resolve file by file, as a 3-way merge with the 0.2.0 render as
  the base.
- **Placeholders.** A `{{…}}` left unfilled, or the coordinator path
  mangled by shell escaping (it happened once while rendering).
- **The session hooks.** `.claude/settings.json` is new here; its hooks run
  in every session, so a broken hook script would show in every session.
- Test lines deleted from `scripts/intent-check-lib.test.mjs` (tests for the
  interim gate rule replaced by the `by-agent` ones) make `check:intent`
  route this refactor; that is expected and is stated in `review.md`.

## Verified against the codebase

Re-read on `main` at `9fb634f`:
- `main` is the 0.2.0 scaffold (`e07c847`) plus §1's intent folder and one
  `plan.md` queue row; the kit files are byte-identical to a fresh 0.2.0
  render (checked by `diff -r` against `40c0cdd` rendered with this repo's
  values).
- `feat/1-order-recommendations-service` (`d57d7ad`) changes `CLAUDE.md`,
  `README.md`, `REVIEW-POLICY.md`, `package.json`, `.gitignore`,
  `scripts/intent-check-lib.mjs` and its test, besides product files.

## Subtasks

1. Create the branch and its worktree from `main`
   (`../freshflow-engineering-challenge-wt/2-sdlc-kit-0-3`), never checking
   out in the main checkout.
2. Copy the 0.3.0 render over the kit files; delete `plan.md`; add
   `OVERVIEW.md`; keep `intents/1-*` and `intents/2-*` untouched. Commit.
3. `npm run verify` and `npm run queue` green in the worktree; set
   `status: in-review`.
4. After §1 merges: rebase (or merge `main` into) the branch, resolving the
   six overlapping files by keeping §1's product facts in 0.3.0's wording,
   and add `"setup:worktree": "uv sync"` to `package.json` if §1's stack is
   uv-managed Python. Re-run verify (now the product's suite too).
5. `/review`, then `/ship 2` on the owner's request.

## Tests

The kit's own suite (254 tests in `scripts/*.test.mjs`) covers the new
scripts. After the merge, §1's product tests run unchanged under `verify`
and must stay green without edits.

## Validation

- `npm run verify` green
- `npm run check:intent` ROUTE (deleted test lines in the kit's test file),
  with the reason recorded in review.md
- Live check: owed by rule 2 (`.claude/settings.json`). Start a new Claude
  Code session in the main checkout after the merge, send one prompt, and
  run `npm run sessions`: the main row shows the session as `working` or
  `idle`, not `no events`.

## Assumptions I made

- Merge after §1, per the owner's choice on 2026-11-03.
- `setup:worktree` is added at merge time only if §1's final `package.json`
  shows the stack needs it.

## Progress

<!-- The implementer appends here, one entry per phase: date, commits, what
shipped, test counts, anything that diverged from the plan. Nothing above
this line is the implementer's to edit. -->
