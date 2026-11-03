<!-- generated-by: freshflow-engineering-challenge/intent@0.2.0 -->
# §7 — Add an npm lint script so sdlc:scan sees the linter

**Type:** adjustment
**Originator:** me (the open items after §1 and §2 shipped)
**Source:** §2 review round 2 and `docs/sdlc-grid.md` (2026-11-03)

## Problem

`npm run sdlc:scan` reports `lint: no`, although `npm run verify` runs
`ruff check` and `ruff format --check`. The scan detects a linter by the
presence of a `lint` script in `package.json` (`scripts/sdlc-scan.mjs:35`), and
there is none. So the grid's Test row understates the evidence (§2 review
round 2, LOW).

## Outcome

- `package.json` has `"lint": "uv run ruff check && uv run ruff format --check"`,
  and `verify:py` calls it instead of repeating those commands.
- `npm run sdlc:scan` reports `lint: yes`.
- `npm run verify` still runs exactly the same checks.

## Constraints

- No change to the kit's scan code: its convention is fine.

## Type-specific questions

### Adjustment
- **Exactly what changes:** the `scripts` block of `package.json` (one new
  script, one changed), plus the commands list in `CLAUDE.md`.
- **Blast radius:** 2 files, a few lines, with no core code.

## Assumptions I made

- The README needn't mention `npm run lint`. The commands list in `CLAUDE.md` is enough.
