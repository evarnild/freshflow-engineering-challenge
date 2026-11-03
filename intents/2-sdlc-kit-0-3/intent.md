# §2 — Bring the SDLC kit up to ai-sdlc-kit 0.3.0

**Type:** refactor
**Originator:** me ("port freshflow-engineering-challenge", 2026-11-03)
**Source:** ai-sdlc-kit commit `f7cdeaa` (0.3.0), which ports heraklios's
SDLC as of 2026-11-03 into the kit this repo was scaffolded from (`40c0cdd`)

## Problem

This repository was scaffolded on 2026-11-03 from ai-sdlc-kit 0.2.0. The kit
has since moved to 0.3.0, so this repo misses what heraklios has learnt
since: gates recorded with a `by-agent` marker instead of the interim
comment rule, a queue generated from `metadata.yml` instead of a hand-kept
`plan.md`, the `/spec`, `/build-plan`, `/ship`, `/spawn`, `/sessions` and
`/auto` skills with their scripts, and the review's "Needs rework:" /
"Needs decision:" split.

## Outcome

- The kit files in this repo match ai-sdlc-kit 0.3.0, rendered for
  `freshflow-engineering-challenge`, and `npm run verify` runs the kit's
  254 tests green (256 after merging §1, which added two `CORE_CODE` tests).
- `npm run queue`, `npm run ship -- <id> --dry-run`, `npm run spawn` and
  `npm run sessions` work here; the root `plan.md` is replaced by
  `OVERVIEW.md`.
- §1's product work (stack, `CORE_CODE`, live-check and Reviewed paths,
  `verify` command, Architecture) survives the merge unchanged in meaning.

## Constraints

- §1 is in rework on its own branch and touches six of the same files
  (`CLAUDE.md`, `README.md`, `REVIEW-POLICY.md`, `package.json`,
  `.gitignore`, `scripts/intent-check-lib.mjs`). §2 must not disturb it:
  it is built on its own branch and **merges after §1 ships**, resolving the
  overlap once against §1's final files.
- No product code changes. No new dependency: the kit needs only Node.
- Kit files are Reviewed tier (`REVIEW-POLICY.md` path table).

## Type-specific questions

### Refactor
- **What is restructured:** the SDLC kit: `intents/README.md`,
  `REVIEW-POLICY.md`, `sdlc.md`, `CLAUDE.md` and `AGENTS.md` workflow
  sections, `.claude/` and `.codex/` agents and skills, `scripts/*.mjs`,
  `package.json` scripts, `.claude/settings.json` (new session hooks),
  `plan.md` → `OVERVIEW.md`.
- **How behaviour is held constant:** the product (§1's `src/`, `tests/`)
  is not touched; its tests stay green untouched after the merge. The kit's
  own behaviour changes on purpose (that is the point), proven by the kit's
  tests.
- **Why now:** §1 is the first intent through the gates; every later
  intent would otherwise run on the old rules, and `/ship`, `/auto` and the
  generated queue are unavailable until this lands.

## Assumptions I made

- Refactor rather than feature: the product's behaviour is unchanged, and
  the kit change is a known port with no design question.
- §1's gates keep their old form (a bare date plus
  `# recorded by agent on owner's request`); the new parser reads them as
  recorded. Rewriting them to `by-agent` would rewrite history in §1's
  folder, so §2 leaves them.
